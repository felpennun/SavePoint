"""Tests for the Phase 4 collaborative and hybrid rankers."""

from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model

from catalogue.models import GameWork, Genre
from library.models import LibraryEntry
from recommendations.collaborative import rank_collaborative_user_knn_v1
from recommendations.hybrid import rank_hybrid_mmr_v1, rank_hybrid_weighted_cf_v1


User = get_user_model()
CORPUS = "phase-4-test"


@pytest.fixture
def phase4_data(db):  # noqa: ANN001
    genre = Genre.objects.create(igdb_id=701, name="Role-playing", slug="rpg")
    target = User.objects.create_user(username="phase4-target", password="Phase4-Target-9!")
    reference = User.objects.create_user(username="phase4-reference", password="Phase4-Reference-9!")
    seed = GameWork.objects.create(
        canonical_slug="phase4-seed",
        original_title="Phase4 Seed",
        in_corpus=True,
        corpus_version=CORPUS,
        first_release_date=date(2020, 1, 1),
    )
    seed_two = GameWork.objects.create(
        canonical_slug="phase4-seed-two",
        original_title="Phase4 Seed Two",
        in_corpus=True,
        corpus_version=CORPUS,
        first_release_date=date(2020, 2, 1),
    )
    candidate_a = GameWork.objects.create(
        canonical_slug="phase4-candidate-a",
        original_title="Phase4 Candidate A",
        in_corpus=True,
        corpus_version=CORPUS,
        first_release_date=date(2021, 1, 1),
    )
    candidate_b = GameWork.objects.create(
        canonical_slug="phase4-candidate-b",
        original_title="Phase4 Candidate B",
        in_corpus=True,
        corpus_version=CORPUS,
        first_release_date=date(2022, 1, 1),
    )
    seed.genres.set([genre])
    seed_two.genres.set([genre])
    candidate_a.genres.set([genre])
    candidate_b.genres.set([genre])
    LibraryEntry.objects.create(user=target, work=seed, current_status="completed", rating_half_steps=9)
    LibraryEntry.objects.create(user=target, work=seed_two, current_status="completed", rating_half_steps=8)
    LibraryEntry.objects.create(user=reference, work=seed, current_status="completed", rating_half_steps=9)
    LibraryEntry.objects.create(user=reference, work=seed_two, current_status="completed", rating_half_steps=8)
    LibraryEntry.objects.create(user=reference, work=candidate_a, current_status="completed", rating_half_steps=10)
    LibraryEntry.objects.create(user=reference, work=candidate_b, current_status="completed", rating_half_steps=2)
    prepared = {
        "works": [candidate_a, candidate_b],
        "vectors": {candidate_a.id: {"genre:rpg": 1.0}, candidate_b.id: {"genre:rpg": 1.0}},
        "genre_profile": {},
        "snapshot_stats": {},
        "snapshot_sha256": "snapshot",
        "popscore_snapshot_sha256": "popscore",
    }
    return target, reference, (candidate_a, candidate_b), prepared


@pytest.mark.django_db
def test_user_knn_uses_positive_neighbour_ratings_and_stable_fallback(phase4_data) -> None:  # noqa: ANN001
    target, reference, candidates, prepared = phase4_data
    result = rank_collaborative_user_knn_v1(
        target,
        candidate_ids=[work.id for work in candidates],
        reference_user_ids=[reference.id],
        prepared=prepared,
    )

    assert result["algorithm_id"] == "cf-user-knn-v1"
    assert [item["slug"] for item in result["results"]] == ["phase4-candidate-a", "phase4-candidate-b"]
    assert result["results"][0]["signals"]["neighbor_count"] == 1


@pytest.mark.django_db
def test_hybrid_reports_its_two_fixed_signal_weights(phase4_data) -> None:  # noqa: ANN001
    target, reference, candidates, prepared = phase4_data
    result = rank_hybrid_weighted_cf_v1(
        target,
        candidate_ids=[work.id for work in candidates],
        corpus_version=CORPUS,
        reference_user_ids=[reference.id],
        prepared=prepared,
        genre_profile={},
    )

    assert result["algorithm_id"] == "hybrid-weighted-cf-v1"
    assert result["parameters"]["content_weight"] == 0.60
    assert result["parameters"]["collaborative_weight"] == 0.40
    assert all(item["score"] >= 0 for item in result["results"])


@pytest.mark.django_db
def test_hybrid_mmr_uses_shared_relevance_pool_and_auditable_mmr(phase4_data) -> None:  # noqa: ANN001
    target, reference, candidates, prepared = phase4_data
    result = rank_hybrid_mmr_v1(
        target,
        candidate_ids=[work.id for work in candidates],
        limit=20,
        corpus_version=CORPUS,
        reference_user_ids=[reference.id],
        prepared=prepared,
        genre_profile={},
    )

    assert result["algorithm_id"] == "hybrid-mmr-v1"
    assert result["parameters"] == {
        "base_algorithm_id": "hybrid-weighted-cf-v1",
        "content_algorithm_id": "content-cbf-weighted-v1",
        "collaborative_algorithm_id": "cf-user-knn-v1",
        "content_weight": 0.60,
        "collaborative_weight": 0.40,
        "lambda": 0.80,
        "pool_size": 100,
        "pool_rule": "max(100, 5*K)",
        "feature_set_version": "fs-v9",
        "presentation_limit": 20,
    }
    assert len(result["results"]) == 2
    assert all("mmr_score" in item["signals"] for item in result["results"])
    assert all("hybrid_relevance_score" in item["signals"] for item in result["results"])
