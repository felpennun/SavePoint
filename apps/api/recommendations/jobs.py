"""PostgreSQL-backed refresh queue for personalized recommendations."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from evaluation import protocol as evaluation_protocol
from library.models import LibraryEntry, OwnedCopy
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.content.features import FEATURE_SET_VERSION
from recommendations.genre_heuristic import rank_genre_taste_v1
from recommendations.models import (
    RecommendationJobStatus,
    RecommendationRefreshJob,
    RecommendationSnapshot,
    RecommendationState,
)
from recommendations.service import active_corpus_version, recommend_for_user


def collection_fingerprint(user_id: int, revision: int) -> str:
    """Hash the exact user-owned inputs used by a refresh."""

    entries = list(
        LibraryEntry.objects.filter(user_id=user_id)
        .values_list("work_id", "current_status", "rating_half_steps")
    )
    copies = list(
        OwnedCopy.objects.filter(user_id=user_id).values_list(
            "id", "work_id", "release_id", "edition_id", "format"
        )
    )
    payload = {
        "revision": revision,
        "entries": sorted((str(work_id), status, rating) for work_id, status, rating in entries),
        "copies": sorted(
            (str(copy_id), str(work_id), str(release_id), str(edition_id) if edition_id else None, fmt)
            for copy_id, work_id, release_id, edition_id, fmt in copies
        ),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def enqueue_latest_refresh(user_id: int) -> RecommendationRefreshJob | None:
    """Create or re-open exactly one job for the user's current revision."""

    state = RecommendationState.objects.filter(user_id=user_id).first()
    if state is None or state.collection_revision == 0:
        return None
    now = timezone.now()
    job, created = RecommendationRefreshJob.objects.get_or_create(
        user_id=user_id,
        requested_revision=state.collection_revision,
        defaults={"available_at": now},
    )
    if not created and job.status in {RecommendationJobStatus.FAILED, RecommendationJobStatus.OBSOLETE}:
        job.status = RecommendationJobStatus.QUEUED
        job.available_at = now
        job.last_error = ""
        job.save(update_fields=["status", "available_at", "last_error", "updated_at"])
    return job


def build_recommendation_bundle(user: Any, corpus_version: str | None) -> dict[str, Any]:
    """Compute every product section as one unpublished bundle."""

    frozen = evaluation_protocol.load(allow_consumed_test=True)
    content = {
        algorithm_id: recommend_for_user(
            user,
            algorithm_id,
            protocol=frozen,
            corpus_version=corpus_version,
            limit=20,
        )
        for algorithm_id in ALGORITHM_REGISTRY
    }
    return {
        "content": content,
        "genre": rank_genre_taste_v1(user, limit=20),
    }


def _claim_next_job() -> str | None:
    now = timezone.now()
    stale_before = now - timedelta(minutes=10)
    with transaction.atomic():
        RecommendationRefreshJob.objects.filter(
            status=RecommendationJobStatus.RUNNING,
            locked_at__lt=stale_before,
        ).update(status=RecommendationJobStatus.QUEUED, locked_at=None)
        job = (
            RecommendationRefreshJob.objects.select_for_update(skip_locked=True)
            .filter(status=RecommendationJobStatus.QUEUED, available_at__lte=now)
            .order_by("available_at", "created_at")
            .first()
        )
        if job is None:
            return None
        job.status = RecommendationJobStatus.RUNNING
        job.attempts += 1
        job.locked_at = now
        job.save(update_fields=["status", "attempts", "locked_at", "updated_at"])
        return str(job.id)


def process_one_job() -> bool:
    """Process one job; stale results are discarded rather than published."""

    job_id = _claim_next_job()
    if job_id is None:
        return False
    job = RecommendationRefreshJob.objects.select_related("user").get(id=job_id)
    try:
        state = RecommendationState.objects.get(user_id=job.user_id)
        fingerprint = collection_fingerprint(job.user_id, job.requested_revision)
        corpus_version = active_corpus_version()
        payload = build_recommendation_bundle(job.user, corpus_version)
        with transaction.atomic():
            state = RecommendationState.objects.select_for_update().get(user_id=job.user_id)
            current_fingerprint = collection_fingerprint(job.user_id, state.collection_revision)
            if state.collection_revision != job.requested_revision or current_fingerprint != fingerprint:
                job.status = RecommendationJobStatus.OBSOLETE
                job.locked_at = None
                job.save(update_fields=["status", "locked_at", "updated_at"])
                transaction.on_commit(lambda: enqueue_latest_refresh(job.user_id))
                return True
            snapshot = RecommendationSnapshot.objects.create(
                user_id=job.user_id,
                collection_revision=state.collection_revision,
                input_fingerprint=fingerprint,
                corpus_version=corpus_version,
                feature_set_version=FEATURE_SET_VERSION,
                payload=payload,
                generated_at=timezone.now(),
            )
            state.active_snapshot = snapshot
            state.save(update_fields=["active_snapshot", "updated_at"])
            job.status = RecommendationJobStatus.SUCCEEDED
            job.locked_at = None
            job.last_error = ""
            job.save(update_fields=["status", "locked_at", "last_error", "updated_at"])
        return True
    except Exception as exc:  # noqa: BLE001 - persist failure and keep old snapshot
        RecommendationRefreshJob.objects.filter(id=job_id).update(
            status=RecommendationJobStatus.FAILED,
            locked_at=None,
            last_error=type(exc).__name__,
            updated_at=timezone.now(),
        )
        return True
