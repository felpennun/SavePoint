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
from recommendations.published import SECTION_ALGORITHM_IDS, configuration_fingerprint


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


def test_collection_change_enqueues_every_published_section(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())

    state = RecommendationState.objects.get(user=user)
    jobs = RecommendationRefreshJob.objects.filter(user=user)

    assert state.collection_revision == 1
    assert jobs.count() == len(SECTION_ALGORITHM_IDS)
    assert set(jobs.values_list("algorithm_id", flat=True)) == set(SECTION_ALGORITHM_IDS)
    assert set(jobs.values_list("requested_revision", flat=True)) == {1}
    assert set(jobs.values_list("status", flat=True)) == {RecommendationJobStatus.QUEUED}


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
        configuration_fingerprint=configuration_fingerprint(),
        corpus_version=None,
        feature_set_version="fs-v5",
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


def test_workers_publish_bundle_only_after_every_section_succeeds(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())

    monkeypatch.setattr(
        jobs,
        "build_recommendation_section",
        lambda user, corpus_version, algorithm_id: {"algorithm_id": algorithm_id, "results": []},
    )

    for algorithm_id in SECTION_ALGORITHM_IDS[:-1]:
        assert jobs.process_one_job(algorithm_id) is True
    state = RecommendationState.objects.get(user=user)
    assert state.active_snapshot is None

    assert jobs.process_one_job(SECTION_ALGORITHM_IDS[-1]) is True

    state = RecommendationState.objects.get(user=user)
    jobs_for_user = RecommendationRefreshJob.objects.filter(user=user)
    assert not jobs_for_user.exclude(status=RecommendationJobStatus.SUCCEEDED).exists()
    assert state.active_snapshot is not None
    assert state.active_snapshot.collection_revision == state.collection_revision == 1
    assert set(state.active_snapshot.payload["content"]) == set(SECTION_ALGORITHM_IDS[:-1])


def test_worker_claims_only_its_named_section(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())
    processed = []
    monkeypatch.setattr(
        jobs,
        "build_recommendation_section",
        lambda user, corpus_version, algorithm_id: processed.append(algorithm_id) or {"results": []},
    )

    assert jobs.process_one_job("recency-v1") is True
    assert processed == ["recency-v1"]
    assert RecommendationRefreshJob.objects.get(user=user, algorithm_id="recency-v1").status == RecommendationJobStatus.SUCCEEDED
    assert RecommendationRefreshJob.objects.filter(user=user, status=RecommendationJobStatus.QUEUED).count() == len(SECTION_ALGORITHM_IDS) - 1
