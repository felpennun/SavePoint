"""Tests for the asynchronous personal recommendation snapshot workflow."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogue.models import GameWork
from library.models import LibraryEntry
from recommendations import jobs
from recommendations.models import (
    RecommendationJobStatus,
    RecommendationRefreshJob,
    RecommendationSnapshot,
    RecommendationState,
)


def _user():
    return get_user_model().objects.create_user(
        username="snapshot-user", password="Snapshot-User-Pass-9!"
    )


def _work(slug: str = "snapshot-work"):
    return GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
    )


def _entry(user, work):  # noqa: ANN001
    return LibraryEntry.objects.create(
        user=user, work=work, current_status="completed", rating_half_steps=8
    )


def test_collection_change_enqueues_one_revision(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())

    state = RecommendationState.objects.get(user=user)
    job = RecommendationRefreshJob.objects.get(user=user)

    assert state.collection_revision == 1
    assert job.requested_revision == 1
    assert job.status == RecommendationJobStatus.QUEUED


def test_snapshot_endpoint_returns_empty_without_collection(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/recommendations/snapshot/")

    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["sections"] is None


def test_snapshot_endpoint_keeps_previous_bundle_while_refreshing(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    entry = _entry(user, _work())
    state = RecommendationState.objects.get(user=user)
    snapshot = RecommendationSnapshot.objects.create(
        user=user,
        collection_revision=state.collection_revision,
        input_fingerprint=jobs.collection_fingerprint(user.id, state.collection_revision),
        corpus_version=None,
        feature_set_version="fs-v4",
        payload={"content": {}, "genre": {"results": []}},
        generated_at=state.updated_at,
    )
    state.active_snapshot = snapshot
    state.save(update_fields=["active_snapshot", "updated_at"])

    entry.rating_half_steps = 10
    entry.save(update_fields=["rating_half_steps", "updated_at"])

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/recommendations/snapshot/")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "stale"
    assert data["published_revision"] == 1
    assert data["sections"] == snapshot.payload


def test_existing_collection_without_job_is_not_requeued_by_page_open(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())
    RecommendationRefreshJob.objects.filter(user=user).delete()

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/recommendations/snapshot/")

    assert response.status_code == 200
    assert response.json()["status"] == "needs_refresh"
    assert not RecommendationRefreshJob.objects.filter(user=user).exists()


def test_worker_publishes_bundle_only_for_current_revision(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())

    monkeypatch.setattr(
        jobs,
        "build_recommendation_bundle",
        lambda user, corpus_version: {"content": {}, "genre": {"results": []}},
    )

    assert jobs.process_one_job() is True

    state = RecommendationState.objects.get(user=user)
    job = RecommendationRefreshJob.objects.get(user=user)
    assert job.status == RecommendationJobStatus.SUCCEEDED
    assert state.active_snapshot is not None
    assert state.active_snapshot.collection_revision == state.collection_revision == 1
