"""Tests for the asynchronous personal recommendation snapshot workflow."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogue.models import GameWork
from library.models import LibraryEntry
from recommendations import jobs
from recommendations.cancellation import RecommendationComputationCancelled
from recommendations.models import (
    RecommendationJobStatus,
    RecommendationRefreshJob,
    RecommendationSnapshot,
    RecommendationState,
)
from recommendations.published import (
    SECTION_ALGORITHM_IDS,
    SIGNAL_ALGORITHM_ID,
    configuration_fingerprint,
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


def test_collection_change_enqueues_every_published_section(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())

    state = RecommendationState.objects.get(user=user)
    jobs = RecommendationRefreshJob.objects.filter(user=user)

    assert state.collection_revision == 1
    # content-signals-v1 (2026-09-11) is enqueued alongside every published
    # section: it is not itself a section (SIGNAL_ALGORITHM_ID is not in
    # SECTION_ALGORITHM_IDS), but every content/hybrid job waits on it.
    assert jobs.count() == len(SECTION_ALGORITHM_IDS) + 1
    assert set(jobs.values_list("algorithm_id", flat=True)) == {
        *SECTION_ALGORITHM_IDS,
        SIGNAL_ALGORITHM_ID,
    }
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
        feature_set_version="fs-v6",
        payload={"content": {}, "tags": {"results": []}},
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


def test_snapshot_endpoint_does_not_report_obsolete_jobs_as_a_live_refresh(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())
    state = RecommendationState.objects.get(user=user)
    snapshot = RecommendationSnapshot.objects.create(
        user=user,
        collection_revision=state.collection_revision,
        input_fingerprint=jobs.collection_fingerprint(user.id, state.collection_revision),
        configuration_fingerprint="previous-config",
        corpus_version=None,
        feature_set_version="fs-v6",
        payload={"content": {}, "tags": {"results": []}},
        generated_at=state.updated_at,
    )
    state.active_snapshot = snapshot
    state.save(update_fields=["active_snapshot", "updated_at"])
    RecommendationRefreshJob.objects.filter(user=user).update(
        status=RecommendationJobStatus.OBSOLETE
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/recommendations/snapshot/")

    assert response.status_code == 200
    assert response.json()["status"] == "needs_refresh"
    assert response.json()["job_status"] is None
    assert response.json()["sections"] == snapshot.payload


def test_workers_publish_bundle_only_after_every_section_succeeds(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())

    monkeypatch.setattr(
        jobs,
        "build_recommendation_section",
        lambda user, corpus_version, algorithm_id, **kwargs: {"algorithm_id": algorithm_id, "results": []},
    )

    # content/hybrid sections are only claimable once content-signals-v1 has
    # succeeded for this (user, revision, configuration).
    assert jobs.process_one_job(SIGNAL_ALGORITHM_ID) is True

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
    assert set(state.active_snapshot.payload["content"]) == set(SECTION_ALGORITHM_IDS)


def test_worker_claims_only_its_named_section(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())
    processed = []
    monkeypatch.setattr(
        jobs,
        "build_recommendation_section",
        lambda user, corpus_version, algorithm_id, **kwargs: processed.append(algorithm_id) or {"results": []},
    )

    assert jobs.process_one_job(SIGNAL_ALGORITHM_ID) is True
    processed.clear()

    assert jobs.process_one_job("recency-v1") is True
    assert processed == ["recency-v1"]
    assert RecommendationRefreshJob.objects.get(user=user, algorithm_id="recency-v1").status == RecommendationJobStatus.SUCCEEDED
    assert RecommendationRefreshJob.objects.filter(user=user, status=RecommendationJobStatus.QUEUED).count() == len(SECTION_ALGORITHM_IDS) - 1


def test_mmr_pop_worker_claims_only_its_named_section(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    user = _user()
    _entry(user, _work())
    processed = []
    monkeypatch.setattr(
        jobs,
        "build_recommendation_section",
        lambda user, corpus_version, algorithm_id, **kwargs: processed.append(algorithm_id) or {"results": []},
    )

    assert jobs.process_one_job(SIGNAL_ALGORITHM_ID) is True
    processed.clear()

    assert jobs.process_one_job("content-cbf-mmr-pop-v2") is True
    assert processed == ["content-cbf-mmr-pop-v2"]
    assert RecommendationRefreshJob.objects.get(
        user=user, algorithm_id="content-cbf-mmr-pop-v2"
    ).status == RecommendationJobStatus.SUCCEEDED
    assert RecommendationRefreshJob.objects.filter(
        user=user, status=RecommendationJobStatus.QUEUED
    ).count() == len(SECTION_ALGORITHM_IDS) - 1


def test_only_the_three_chosen_content_variants_are_published() -> None:
    assert SECTION_ALGORITHM_IDS == (
        "content-cbf-weighted-v1",
        "content-cbf-mmr-pop-v2",
        "recency-v1",
    )
    # Variants that stay in the offline lab (and the retired tag shelf) have no product worker.
    for algorithm_id in (
        "hybrid-mmr-v1",
        "hybrid-weighted-cf-v1",
        "cf-user-knn-v1",
        "content-cbf-mmr-v1",
        "tag-taste-v1",
    ):
        with pytest.raises(ValueError):
            jobs.process_one_job(algorithm_id)


def test_new_collection_revision_obsoletes_every_prior_section(transactional_db) -> None:  # noqa: ANN001
    user = _user()
    entry = _entry(user, _work())
    old_jobs = list(RecommendationRefreshJob.objects.filter(user=user))

    entry.rating_half_steps = 10
    entry.save(update_fields=["rating_half_steps", "updated_at"])

    state = RecommendationState.objects.get(user=user)
    assert state.collection_revision == 2
    assert not RecommendationRefreshJob.objects.filter(
        id__in=[job.id for job in old_jobs]
    ).exclude(status=RecommendationJobStatus.OBSOLETE).exists()
    latest_jobs = RecommendationRefreshJob.objects.filter(
        user=user,
        requested_revision=state.collection_revision,
        configuration_fingerprint=configuration_fingerprint(),
    )
    assert latest_jobs.count() == len(SECTION_ALGORITHM_IDS) + 1
    assert set(latest_jobs.values_list("status", flat=True)) == {RecommendationJobStatus.QUEUED}


def test_running_worker_cancels_when_a_new_revision_arrives(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    user = _user()
    entry = _entry(user, _work())

    def supersede_while_calculating(user, corpus_version, algorithm_id, *, should_continue, **kwargs):  # noqa: ANN001
        if algorithm_id != "recency-v1":
            return {"algorithm_id": algorithm_id, "results": []}
        entry.rating_half_steps = 10
        entry.save(update_fields=["rating_half_steps", "updated_at"])
        assert should_continue is not None
        assert should_continue() is False
        raise RecommendationComputationCancelled

    monkeypatch.setattr(jobs, "build_recommendation_section", supersede_while_calculating)

    assert jobs.process_one_job(SIGNAL_ALGORITHM_ID) is True
    assert jobs.process_one_job("recency-v1") is True

    state = RecommendationState.objects.get(user=user)
    assert state.collection_revision == 2
    assert RecommendationRefreshJob.objects.get(
        user=user, requested_revision=1, algorithm_id="recency-v1"
    ).status == RecommendationJobStatus.OBSOLETE
    assert RecommendationRefreshJob.objects.filter(
        user=user,
        requested_revision=2,
        status=RecommendationJobStatus.QUEUED,
    ).count() == len(SECTION_ALGORITHM_IDS) + 1


def test_content_job_is_not_claimable_before_its_signals_job_succeeds(transactional_db, monkeypatch) -> None:  # noqa: ANN001
    """A dependent worker polls and finds nothing rather than computing signals itself."""

    user = _user()
    _entry(user, _work())
    monkeypatch.setattr(
        jobs,
        "build_recommendation_section",
        lambda user, corpus_version, algorithm_id, **kwargs: {"algorithm_id": algorithm_id, "results": []},
    )

    # No signals row for this (user, revision, configuration) yet: the claim
    # query withholds every dependent job -- a --loop worker just polls again.
    assert jobs.process_one_job("content-cbf-weighted-v1") is False
    assert jobs.process_one_job("content-cbf-mmr-pop-v2") is False
    assert RecommendationRefreshJob.objects.get(
        user=user, algorithm_id="content-cbf-weighted-v1"
    ).status == RecommendationJobStatus.QUEUED

    assert jobs.process_one_job(SIGNAL_ALGORITHM_ID) is True

    # Now that the signals job has succeeded, the same dependent job becomes
    # claimable without any change to the queued row itself.
    assert jobs.process_one_job("content-cbf-weighted-v1") is True
    assert RecommendationRefreshJob.objects.get(
        user=user, algorithm_id="content-cbf-weighted-v1"
    ).status == RecommendationJobStatus.SUCCEEDED
