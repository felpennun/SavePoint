"""Invariants for the Phase 3 v2 recommendation service."""

from __future__ import annotations

import copy
from datetime import date

import pytest
from django.utils import timezone

from catalogue.models import CorpusRatingSnapshot, GameWork, Genre
from evaluation import protocol
from evaluation.protocol import ProtocolError
from library.models import LibraryEntry
from recommendations import service
from recommendations.content.variants import ALGORITHM_REGISTRY


CORPUS = "phase-3-test"


@pytest.fixture
def service_user(db):  # noqa: ANN001
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        username="phase-3-service-user", password="Phase-3-Service-Pass-9!"
    )


@pytest.fixture
def service_genres(db):  # noqa: ANN001
    return {
        "rpg": Genre.objects.create(igdb_id=101, name="Role-playing", slug="rpg"),
        "shooter": Genre.objects.create(igdb_id=102, name="Shooter", slug="shooter"),
    }


def make_work(slug: str, *genres: Genre, **overrides) -> GameWork:
    fields = {
        "in_corpus": True,
        "corpus_version": CORPUS,
        "first_release_date": date(2020, 1, 1),
        **overrides,
    }
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        **fields,
    )
    work.genres.set(genres)
    return work


def add_snapshot(work: GameWork, rating: float = 80.0) -> None:
    CorpusRatingSnapshot.objects.create(
        work=work,
        corpus_version=CORPUS,
        source="igdb",
        rating=rating,
        rating_count=10,
        retrieved_at=timezone.now(),
    )


def v2_protocol():
    return protocol.load()


@pytest.mark.django_db
def test_manifest_excludes_seen_future_and_unrated_works(service_user, service_genres) -> None:  # noqa: ANN001
    owned = make_work("owned", service_genres["rpg"], rating=80.0, total_rating_count=10)
    counted = make_work("counted", service_genres["rpg"], rating=80.0, total_rating_count=10)
    low_volume = make_work("low-volume", service_genres["shooter"], rating=80.0, total_rating_count=4)
    unrated = make_work("unrated", service_genres["rpg"], total_rating_count=10)
    future = make_work(
        "future",
        service_genres["rpg"],
        rating=80.0,
        total_rating_count=10,
        first_release_date=date(2026, 9, 9),
    )
    LibraryEntry.objects.create(user=service_user, work=owned, current_status="pending")

    manifest = service.build_candidate_manifest(
        service_user,
        v2_protocol(),
        corpus_version=CORPUS,
        eligibility_cutoff_date=date(2026, 9, 8),
    )

    assert str(counted.id) in {str(value) for value in manifest.candidate_ids}
    assert str(low_volume.id) not in {str(value) for value in manifest.candidate_ids}
    assert str(owned.id) not in {str(value) for value in manifest.candidate_ids}
    assert str(unrated.id) not in {str(value) for value in manifest.candidate_ids}
    assert str(future.id) not in {str(value) for value in manifest.explorable_ids}
    assert manifest.candidate_manifest_sha256 == service.build_candidate_manifest(
        service_user,
        v2_protocol(),
        corpus_version=CORPUS,
        eligibility_cutoff_date=date(2026, 9, 8),
    ).candidate_manifest_sha256


@pytest.mark.django_db
def test_algorithms_share_the_same_manifest_and_payload_stays_score_ordered(
    service_user, service_genres
) -> None:  # noqa: ANN001
    for index in range(3):
        make_work(f"seed-{index}", service_genres["rpg"], rating=80.0, total_rating_count=10)
        LibraryEntry.objects.create(
            user=service_user,
            work=GameWork.objects.get(canonical_slug=f"seed-{index}"),
            current_status="completed",
            rating_half_steps=8,
        )
    for slug in ("z-last", "a-first"):
        candidate = make_work(slug, service_genres["rpg"], rating=80.0, total_rating_count=10)
        add_snapshot(candidate)

    payloads = [
        service.recommend_for_user(
            service_user,
            algorithm_id,
            corpus_version=CORPUS,
            eligibility_cutoff_date=date(2026, 9, 8),
        )
        for algorithm_id in ALGORITHM_REGISTRY
    ]

    assert {payload["protocol_version"] for payload in payloads} == {12}
    assert len({payload["candidate_manifest_sha256"] for payload in payloads}) == 1
    assert all(
        all(left["score"] >= right["score"] for left, right in zip(payload["results"], payload["results"][1:]))
        for payload in payloads
    )
    assert payloads[0]["results"][0]["reason"]["kind"] == "signal_overlap"


@pytest.mark.django_db
def test_service_rejects_ranker_result_outside_manifest(service_user, service_genres, monkeypatch) -> None:  # noqa: ANN001
    candidate = make_work("real-candidate", service_genres["rpg"], rating=80.0, total_rating_count=10)
    add_snapshot(candidate)
    external = make_work("external", service_genres["rpg"], rating=80.0, total_rating_count=10, in_corpus=False)

    def fake_ranker(*args, **kwargs):  # noqa: ANN002, ANN003
        return {
            "algorithm_id": "content-cbf-weighted-v1",
            "generated_at": "2026-09-08T00:00:00+00:00",
            "input_snapshot_sha256": "a" * 64,
            "feature_set_version": "fs-v1",
            "corpus_version": CORPUS,
            "snapshot_sha256": "b" * 64,
            "insufficient_history": False,
            "limitation": "test",
            "results": [{"work_id": str(external.id), "contributions": []}],
        }

    monkeypatch.setattr(service, "rank_content_v1", fake_ranker)
    with pytest.raises(service.RecommendationServiceError, match="outside"):
        service.recommend_for_user(
            service_user,
            "content-cbf-weighted-v1",
            corpus_version=CORPUS,
            eligibility_cutoff_date=date(2026, 9, 8),
        )


@pytest.mark.django_db
def test_service_rejects_v1_artifact(service_user) -> None:  # noqa: ANN001
    raw = copy.deepcopy(protocol.load().raw)
    raw["protocol_version"] = 1

    with pytest.raises(ProtocolError, match="expected protocol_version 12"):
        service.recommend_for_user(
            service_user,
            "content-cbf-weighted-v1",
            protocol=protocol.from_mapping(raw),
            corpus_version=CORPUS,
        )


@pytest.mark.django_db
def test_service_routes_hybrid_mmr_and_preserves_parameters(
    service_user, service_genres, monkeypatch
) -> None:  # noqa: ANN001
    for index in range(3):
        seed = make_work(
            f"hybrid-mmr-seed-{index}",
            service_genres["rpg"],
            rating=80.0,
            total_rating_count=10,
        )
        LibraryEntry.objects.create(
            user=service_user,
            work=seed,
            current_status="completed",
            rating_half_steps=8,
        )
    candidate = make_work(
        "hybrid-mmr-candidate",
        service_genres["rpg"],
        rating=80.0,
        total_rating_count=10,
    )
    add_snapshot(candidate)
    called = {}

    def fake_ranker(*args, **kwargs):  # noqa: ANN002, ANN003
        called.update(kwargs)
        return {
            "algorithm_id": "hybrid-mmr-v1",
            "generated_at": "2026-09-09T00:00:00+00:00",
            "input_snapshot_sha256": "a" * 64,
            "feature_set_version": "fs-v9",
            "corpus_version": CORPUS,
            "snapshot_sha256": "b" * 64,
            "popscore_snapshot_sha256": "c" * 64,
            "insufficient_history": False,
            "limitation": "test",
            "parameters": {"lambda": 0.80, "pool_rule": "max(100, 5*K)"},
            "results": [{
                "work_id": str(candidate.id),
                "slug": candidate.canonical_slug,
                "title": candidate.original_title,
                "score": 0.8,
                "contributions": [],
                "rating_term": 0.8,
                "rating_term_is_fallback": False,
                "reason_signals": [],
                "negative_similarity": 0.0,
                "signals": {},
            }],
        }

    monkeypatch.setattr(service, "rank_hybrid_mmr_v1", fake_ranker)
    payload = service.recommend_for_user(
        service_user,
        "hybrid-mmr-v1",
        corpus_version=CORPUS,
        eligibility_cutoff_date=date(2026, 9, 8),
    )

    assert called["candidate_ids"]
    assert payload["algorithm_id"] == "hybrid-mmr-v1"
    assert payload["parameters"]["lambda"] == 0.80
