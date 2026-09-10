"""PostgreSQL-backed refresh queue for personalized recommendations."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any, Callable

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from evaluation import protocol as evaluation_protocol
from library.models import LibraryEntry, OwnedCopy
from recommendations.content.features import FEATURE_SET_VERSION
from recommendations.cancellation import RecommendationComputationCancelled
from recommendations.genre_heuristic import rank_genre_taste_v1
from recommendations.models import (
    RecommendationJobStatus,
    RecommendationRefreshJob,
    RecommendationSnapshot,
    RecommendationState,
)
from recommendations.service import active_corpus_version, recommend_for_user
from recommendations.published import (
    CONTENT_ALGORITHM_IDS,
    GENRE_ALGORITHM_ID,
    PUBLISHED_RESULT_LIMIT,
    SECTION_ALGORITHM_IDS,
    configuration_fingerprint,
)


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


def enqueue_latest_refresh(user_id: int) -> list[RecommendationRefreshJob]:
    """Supersede old work and enqueue exactly one job per latest section."""

    state = RecommendationState.objects.filter(user_id=user_id).first()
    if state is None or state.collection_revision == 0:
        return []
    now = timezone.now()
    fingerprint = configuration_fingerprint()
    RecommendationRefreshJob.objects.filter(user_id=user_id).filter(
        Q(requested_revision__lt=state.collection_revision)
        | ~Q(configuration_fingerprint=fingerprint)
    ).filter(
        status__in=(RecommendationJobStatus.QUEUED, RecommendationJobStatus.RUNNING)
    ).update(
        status=RecommendationJobStatus.OBSOLETE,
        locked_at=None,
        updated_at=now,
    )
    jobs = []
    for algorithm_id in SECTION_ALGORITHM_IDS:
        job, created = RecommendationRefreshJob.objects.get_or_create(
            user_id=user_id,
            requested_revision=state.collection_revision,
            configuration_fingerprint=fingerprint,
            algorithm_id=algorithm_id,
            defaults={"available_at": now},
        )
        if not created and job.status in {
            RecommendationJobStatus.FAILED,
            RecommendationJobStatus.OBSOLETE,
        }:
            job.status = RecommendationJobStatus.QUEUED
            job.available_at = now
            job.locked_at = None
            job.last_error = ""
            job.result_payload = None
            job.save(
                update_fields=[
                    "status",
                    "available_at",
                    "locked_at",
                    "last_error",
                    "result_payload",
                    "updated_at",
                ]
            )
        jobs.append(job)
    return jobs


def build_recommendation_section(
    user: Any,
    corpus_version: str | None,
    algorithm_id: str,
    *,
    should_continue: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Compute exactly one product section under the shared algorithm catalog."""

    if algorithm_id in CONTENT_ALGORITHM_IDS:
        frozen = evaluation_protocol.load(allow_consumed_test=True)
        return recommend_for_user(
            user,
            algorithm_id,
            protocol=frozen,
            corpus_version=corpus_version,
            limit=PUBLISHED_RESULT_LIMIT,
            should_continue=should_continue,
        )
    if algorithm_id == GENRE_ALGORITHM_ID:
        return rank_genre_taste_v1(
            user,
            corpus_version=corpus_version,
            limit=PUBLISHED_RESULT_LIMIT,
            should_continue=should_continue,
        )
    raise ValueError("unknown published recommendation section")


def _claim_next_job(algorithm_id: str | None = None) -> str | None:
    now = timezone.now()
    stale_before = now - timedelta(minutes=10)
    with transaction.atomic():
        stale_jobs = RecommendationRefreshJob.objects.filter(
            status=RecommendationJobStatus.RUNNING,
            locked_at__lt=stale_before,
        )
        if algorithm_id is not None:
            stale_jobs = stale_jobs.filter(algorithm_id=algorithm_id)
        stale_jobs.update(status=RecommendationJobStatus.QUEUED, locked_at=None)
        queued_jobs = (
            RecommendationRefreshJob.objects.select_for_update(skip_locked=True)
            .filter(status=RecommendationJobStatus.QUEUED, available_at__lte=now)
            .filter(
                user__recommendation_state__collection_revision=F("requested_revision"),
                configuration_fingerprint=configuration_fingerprint(),
            )
        )
        if algorithm_id is not None:
            queued_jobs = queued_jobs.filter(algorithm_id=algorithm_id)
        job = queued_jobs.order_by("available_at", "created_at").first()
        if job is None:
            return None
        job.status = RecommendationJobStatus.RUNNING
        job.attempts += 1
        job.locked_at = now
        job.save(update_fields=["status", "attempts", "locked_at", "updated_at"])
        return str(job.id)


def _job_is_current(job: RecommendationRefreshJob) -> bool:
    """Return whether the exact claimed job remains the latest user revision."""

    return RecommendationRefreshJob.objects.filter(
        id=job.id,
        status=RecommendationJobStatus.RUNNING,
        requested_revision=job.requested_revision,
        configuration_fingerprint=job.configuration_fingerprint,
        user__recommendation_state__collection_revision=job.requested_revision,
    ).exists()


def _publish_if_complete(
    *,
    user_id: int,
    state: RecommendationState,
    requested_revision: int,
    input_fingerprint: str,
    config_fingerprint: str,
    corpus_version: str | None,
) -> None:
    """Publish the new bundle only when all independent sections succeeded."""

    section_jobs = list(
        RecommendationRefreshJob.objects.select_for_update()
        .filter(
            user_id=user_id,
            requested_revision=requested_revision,
            configuration_fingerprint=config_fingerprint,
            algorithm_id__in=SECTION_ALGORITHM_IDS,
        )
        .order_by("algorithm_id")
    )
    if len(section_jobs) != len(SECTION_ALGORITHM_IDS) or any(
        section.status != RecommendationJobStatus.SUCCEEDED or section.result_payload is None
        for section in section_jobs
    ):
        return

    payload = {
        "content": {
            section.algorithm_id: section.result_payload
            for section in section_jobs
            if section.algorithm_id in CONTENT_ALGORITHM_IDS
        },
        "tags": next(
            section.result_payload
            for section in section_jobs
            if section.algorithm_id == GENRE_ALGORITHM_ID
        ),
    }
    snapshot, created = RecommendationSnapshot.objects.get_or_create(
        user_id=user_id,
        collection_revision=requested_revision,
        input_fingerprint=input_fingerprint,
        configuration_fingerprint=config_fingerprint,
        defaults={
            "corpus_version": corpus_version,
            "feature_set_version": FEATURE_SET_VERSION,
            "payload": payload,
            "generated_at": timezone.now(),
        },
    )
    if not created:
        snapshot.corpus_version = corpus_version
        snapshot.feature_set_version = FEATURE_SET_VERSION
        snapshot.payload = payload
        snapshot.generated_at = timezone.now()
        snapshot.save(
            update_fields=[
                "corpus_version",
                "feature_set_version",
                "payload",
                "generated_at",
            ]
        )
    state.active_snapshot = snapshot
    state.save(update_fields=["active_snapshot", "updated_at"])


def process_one_job(algorithm_id: str | None = None) -> bool:
    """Process one named section; stale results are never published."""

    if algorithm_id is not None and algorithm_id not in SECTION_ALGORITHM_IDS:
        raise ValueError("unknown published recommendation section")
    job_id = _claim_next_job(algorithm_id)
    if job_id is None:
        return False
    job = RecommendationRefreshJob.objects.select_related("user").get(id=job_id)
    try:
        if not _job_is_current(job):
            RecommendationRefreshJob.objects.filter(id=job.id).update(
                status=RecommendationJobStatus.OBSOLETE,
                locked_at=None,
                updated_at=timezone.now(),
            )
            return True
        state = RecommendationState.objects.get(user_id=job.user_id)
        input_fingerprint = collection_fingerprint(job.user_id, job.requested_revision)
        corpus_version = active_corpus_version()
        payload = build_recommendation_section(
            job.user,
            corpus_version,
            job.algorithm_id,
            should_continue=lambda: _job_is_current(job),
        )
        with transaction.atomic():
            state = RecommendationState.objects.select_for_update().get(user_id=job.user_id)
            current_fingerprint = collection_fingerprint(job.user_id, state.collection_revision)
            if (
                state.collection_revision != job.requested_revision
                or current_fingerprint != input_fingerprint
                or job.configuration_fingerprint != configuration_fingerprint()
            ):
                job.status = RecommendationJobStatus.OBSOLETE
                job.locked_at = None
                job.save(update_fields=["status", "locked_at", "updated_at"])
                transaction.on_commit(lambda: enqueue_latest_refresh(job.user_id))
                return True
            job.status = RecommendationJobStatus.SUCCEEDED
            job.locked_at = None
            job.last_error = ""
            job.result_payload = payload
            job.save(
                update_fields=[
                    "status",
                    "locked_at",
                    "last_error",
                    "result_payload",
                    "updated_at",
                ]
            )
            _publish_if_complete(
                user_id=job.user_id,
                state=state,
                requested_revision=job.requested_revision,
                input_fingerprint=input_fingerprint,
                config_fingerprint=job.configuration_fingerprint,
                corpus_version=corpus_version,
            )
        return True
    except RecommendationComputationCancelled:
        RecommendationRefreshJob.objects.filter(id=job_id).update(
            status=RecommendationJobStatus.OBSOLETE,
            locked_at=None,
            last_error="",
            updated_at=timezone.now(),
        )
        return True
    except Exception as exc:  # noqa: BLE001 - persist failure and keep old snapshot
        RecommendationRefreshJob.objects.filter(id=job_id).update(
            status=RecommendationJobStatus.FAILED,
            locked_at=None,
            last_error=type(exc).__name__,
            updated_at=timezone.now(),
        )
        return True
