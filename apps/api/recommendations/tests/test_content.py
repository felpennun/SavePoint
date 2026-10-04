"""Tests for the versioned content-recommendation laboratory (Plan 02-11)."""

from __future__ import annotations

from datetime import date, timezone

import pytest
from django.utils import timezone as django_timezone
from rest_framework.test import APIClient

from catalogue.models import CorpusRatingSnapshot, CuratedLabel, GameWork, GameWorkCuratedLabel
from library.models import LibraryEntry
from recommendations.content.combine import combine, rating_term
from recommendations.content.features import bayesian_rating, rating_quality_signal
from recommendations.content.rank import rank_content_v1
from recommendations.content.variants import ALGORITHM_REGISTRY, VariantSpec

_CORPUS = "test-corpus"


@pytest.fixture
def user_a(db):  # noqa: ANN001
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        username="content-user-a", password="Content-User-A-Pass-9!"
    )


@pytest.fixture
def genres(db):  # noqa: ANN001
    # "genres" for call-site continuity; these are CuratedLabel rows (the
    # ranking pipeline reads work.curated_labels exclusively).
    return {
        "rpg": CuratedLabel.objects.create(
            name="Role-playing (RPG)", slug="role-playing-rpg", kind=CuratedLabel.Kind.GENRE, curation_version="test"
        ),
        "shooter": CuratedLabel.objects.create(name="Shooter", slug="shooter", kind=CuratedLabel.Kind.GENRE, curation_version="test"),
        "puzzle": CuratedLabel.objects.create(name="Puzzle", slug="puzzle", kind=CuratedLabel.Kind.GENRE, curation_version="test"),
    }


def _work(slug: str, *tags: CuratedLabel) -> GameWork:
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        total_rating_count=1000,
        in_corpus=True,
        corpus_version=_CORPUS,
        first_release_date=date(2020, 1, 1),
    )
    for tag in tags:
        GameWorkCuratedLabel.objects.create(work=work, label=tag, source_kind="genre", source_value=tag.name)
    return work


def _own(user, work, *, status="completed", rating=None):  # noqa: ANN001
    return LibraryEntry.objects.create(
        user=user, work=work, current_status=status, rating_half_steps=rating
    )


def _snapshot(
    work: GameWork,
    *,
    rating: float,
    rating_count: int = 100,
    total_rating_count: int | None = 100,
) -> None:
    work.rating = rating
    work.save(update_fields=["rating"])
    CorpusRatingSnapshot.objects.create(
        work=work,
        corpus_version=_CORPUS,
        source="igdb",
        rating=rating,
        rating_count=rating_count,
        total_rating_count=total_rating_count,
        retrieved_at=django_timezone.now(),
    )


def test_algorithm_registry_has_the_named_positive_and_negative_variants() -> None:
    assert set(ALGORITHM_REGISTRY) == {
        "content-cbf-weighted-v1",
        "content-cbf-multiplicative-v1",
        "content-cbf-twostage-v1",
        "content-cbf-neg-v1",
        "content-cbf-weighted-pop-v1",
        "content-cbf-multiplicative-pop-v1",
        "content-cbf-twostage-pop-v1",
        "content-cbf-neg-pop-v1",
        "recency-v1",
        "content-cbf-mmr-v1",
        "content-cbf-mmr-pop-v1",
    }
    assert all(isinstance(spec, VariantSpec) for spec in ALGORITHM_REGISTRY.values())
    assert [spec.combine_mode for spec in ALGORITHM_REGISTRY.values()] == [
        "weighted_sum",
        "multiplicative",
        "two_stage",
        "negative_weighted_sum",
        "weighted_sum",
        "multiplicative_popscore",
        "two_stage_popscore",
        "negative_weighted_sum_popscore",
        "weighted_sum",
        "mmr",
        "mmr",
    ]


def test_mmr_pop_v2_is_product_only_and_has_the_retuned_effective_weights() -> None:
    from recommendations.content.variants import PRODUCT_VARIANT_REGISTRY, RANKABLE_VARIANT_REGISTRY

    assert "content-cbf-mmr-pop-v2" not in ALGORITHM_REGISTRY
    assert "content-cbf-weighted-pop-v2" not in ALGORITHM_REGISTRY
    assert set(PRODUCT_VARIANT_REGISTRY) <= set(RANKABLE_VARIANT_REGISTRY)
    mmr = PRODUCT_VARIANT_REGISTRY["content-cbf-mmr-pop-v2"]
    base = RANKABLE_VARIANT_REGISTRY[mmr.params["base_algorithm_id"]]
    lam = mmr.params["lambda"]
    effective = {
        "content": lam * base.params["w_content"],
        "rating": lam * base.params["w_rating"],
        "popscore": lam * base.params["w_popscore"],
        "variety": 1 - lam,
    }
    assert {key: round(value, 4) for key, value in effective.items()} == {
        "content": 0.35,
        "rating": 0.20,
        "popscore": 0.25,
        "variety": 0.20,
    }


def test_recency_variant_adds_recency_to_the_other_candidate_signals() -> None:
    spec = ALGORITHM_REGISTRY["recency-v1"]
    score = combine(
        0.8,
        0.7,
        None,
        spec,
        rating_volume=0.6,
        popscore=0.5,
        recency_score=1.0,
    )

    rating_confidence = 0.7
    assert score == pytest.approx(0.8 * 0.20 + rating_confidence * 0.20 + 0.5 * 0.20 + 1.0 * 0.40)
    assert spec.params["w_recency"] == 0.40


def test_bayesian_rating_shrinks_sparse_scores_towards_the_frozen_prior() -> None:
    prior = 70.0
    sparse = bayesian_rating(95.0, 5, prior)
    established = bayesian_rating(95.0, 500, prior)

    assert sparse == pytest.approx((5 * 95.0 + 25 * prior) / 30)
    assert established == pytest.approx((500 * 95.0 + 25 * prior) / 525)
    assert prior < sparse < established < 95.0
    assert rating_quality_signal(sparse) < rating_quality_signal(established)


@pytest.mark.django_db
def test_rating_term_uses_observed_corpus_snapshot_without_genre_dilution(genres) -> None:  # noqa: ANN001
    work = _work("snapshot-rated-rpg", genres["rpg"])
    work.total_rating = 1.0
    work.save(update_fields=["total_rating"])
    _snapshot(work, rating=90.0, rating_count=100)

    term, is_fallback = rating_term(
        work, _CORPUS, {"role-playing-rpg": 60.0}
    )

    assert term == pytest.approx(0.648)
    assert is_fallback is False

    # The mutable product field must not influence a frozen recommendation.
    work.total_rating = 100.0
    work.save(update_fields=["total_rating"])
    assert rating_term(work, _CORPUS, {"role-playing-rpg": 60.0}) == (
        pytest.approx(0.648),
        False,
    )


@pytest.mark.django_db
def test_rating_term_falls_back_to_median_genre_profile(genres) -> None:  # noqa: ANN001
    work = _work("unrated-rpg-shooter", genres["rpg"], genres["shooter"])

    term, is_fallback = rating_term(
        work,
        _CORPUS,
        {"role-playing-rpg": 80.0, "shooter": 40.0},
    )

    assert term == pytest.approx(0.36)
    assert is_fallback is True


def test_combination_modes_have_distinct_ordering_semantics() -> None:
    candidates = {
        "high-sim-low-rating": (0.9, 0.1),
        "mid-sim-high-rating": (0.5, 0.9),
        "balanced": (0.7, 0.8),
    }

    orders = {}
    for algorithm_id, spec in ALGORITHM_REGISTRY.items():
        if spec.combine_mode == "mmr":
            continue
        scored = [
            (combine(cos, term, None, spec), slug)
            for slug, (cos, term) in candidates.items()
        ]
        orders[algorithm_id] = [slug for _score, slug in sorted(scored, reverse=True)]

    assert orders["content-cbf-weighted-v1"] == [
        "balanced",
        "high-sim-low-rating",
        "mid-sim-high-rating",
    ]
    assert orders["content-cbf-multiplicative-v1"] == [
        "balanced",
        "mid-sim-high-rating",
        "high-sim-low-rating",
    ]
    assert orders["content-cbf-twostage-v1"] == [
        "high-sim-low-rating",
        "balanced",
        "mid-sim-high-rating",
    ]


@pytest.mark.django_db
def test_rank_is_deterministic_and_breaks_equal_scores_by_slug(user_a, genres) -> None:  # noqa: ANN001
    for index in range(3):
        owned = _work(f"owned-rpg-{index}", genres["rpg"])
        _own(user_a, owned)
        _snapshot(owned, rating=80.0)

    for slug in ("zzz-candidate", "aaa-candidate"):
        candidate = _work(slug, genres["rpg"])
        _snapshot(candidate, rating=80.0)

    generated_at = django_timezone.now()
    first = rank_content_v1(
        user_a, "content-cbf-weighted-v1", limit=10, corpus_version=_CORPUS,
        generated_at=generated_at,
    )
    second = rank_content_v1(
        user_a, "content-cbf-weighted-v1", limit=10, corpus_version=_CORPUS,
        generated_at=generated_at,
    )

    assert [item["slug"] for item in first["results"]] == [
        "aaa-candidate",
        "zzz-candidate",
    ]
    assert first["results"] == second["results"]


def test_explain_is_numeric_and_sorted_by_tag_contribution() -> None:
    spec = ALGORITHM_REGISTRY["content-cbf-weighted-v1"]
    candidate = {"tag:rpg": 0.5, "tag:shooter": 0.5, "platform:pc": 0.2}
    profile = {"tag:rpg": 0.8, "tag:shooter": 0.2, "platform:pc": 0.1}

    from recommendations.content.explain import explain

    result = explain(candidate, profile, spec)

    assert set(result) == {
        "contributions",
        "reason_signals",
        "rating_term",
        "rating_term_is_fallback",
        "negative_similarity",
        "variant",
    }
    assert result["variant"] == spec.algorithm_id
    assert result["contributions"] == [
        {"tag": "rpg", "contribution_pct": round(0.4 / 0.52, 3)},
        {"tag": "shooter", "contribution_pct": round(0.1 / 0.52, 3)},
    ]
    assert result["reason_signals"] == [
        {"kind": "tag", "value": "rpg", "contribution_pct": round(0.4 / 0.52, 3)},
        {"kind": "tag", "value": "shooter", "contribution_pct": round(0.1 / 0.52, 3)},
    ]
    assert all("because" not in str(value).lower() for value in result.values())


@pytest.mark.django_db
def test_cold_start_returns_fallback_and_keeps_seen_work_out(user_a, genres) -> None:  # noqa: ANN001
    owned = _work("cold-owned", genres["rpg"])
    _own(user_a, owned)
    for slug, genre in (("cold-rpg", genres["rpg"]), ("cold-puzzle", genres["puzzle"])):
        candidate = _work(slug, genre)
        _snapshot(candidate, rating=75.0)

    result = rank_content_v1(
        user_a, "content-cbf-weighted-v1", limit=10, corpus_version=_CORPUS
    )

    assert result["insufficient_history"] is True
    assert result["results"]
    assert "cold-owned" not in {item["slug"] for item in result["results"]}


@pytest.mark.django_db
def test_rank_excludes_candidates_below_the_total_rating_volume_threshold(user_a, genres) -> None:  # noqa: ANN001
    user_rated = _work("low-volume-user-rated-candidate", genres["rpg"])
    user_rated.total_rating_count = None
    user_rated.save(update_fields=["total_rating_count"])
    _snapshot(user_rated, rating=99.0, rating_count=1)

    included = _work("high-confidence-candidate", genres["rpg"])
    included.total_rating_count = 1000
    included.save(update_fields=["total_rating_count"])
    _snapshot(included, rating=80.0, rating_count=1000)

    result = rank_content_v1(
        user_a, "content-cbf-weighted-v1", limit=10, corpus_version=_CORPUS
    )

    slugs = {item["slug"] for item in result["results"]}
    assert "high-confidence-candidate" in slugs
    assert "low-volume-user-rated-candidate" not in slugs


@pytest.mark.django_db
def test_versioned_dto_and_item_evidence(user_a, genres) -> None:  # noqa: ANN001
    for index in range(3):
        owned = _work(f"dto-owned-{index}", genres["rpg"])
        _own(user_a, owned, rating=8)
    candidate = _work("dto-candidate", genres["rpg"], genres["shooter"])
    _snapshot(candidate, rating=85.0, rating_count=200)

    result = rank_content_v1(
        user_a, "content-cbf-weighted-v1", limit=10, corpus_version=_CORPUS
    )

    assert set(result) == {
        "algorithm_id",
        "generated_at",
        "input_snapshot_sha256",
        "feature_set_version",
            "corpus_version",
            "snapshot_sha256",
            "popscore_snapshot_sha256",
            "parameters",
        "profile_inputs",
        "signal_availability",
        "insufficient_history",
        "limitation",
        "results",
    }
    assert result["feature_set_version"] == "fs-v13-family-weighted-tags"
    assert result["corpus_version"] == _CORPUS
    assert len(result["snapshot_sha256"]) == 64
    assert len(result["input_snapshot_sha256"]) == 64
    item = result["results"][0]
    assert set(item) == {
        "work_id",
        "slug",
        "title",
        "score",
        "contributions",
        "rating_term",
        "rating_term_is_fallback",
        "reason_signals",
        "negative_similarity",
        "signals",
    }
    assert item["contributions"]
    assert "rating_term" in item
    assert "rating_term_is_fallback" in item


@pytest.mark.django_db
def test_content_view_requires_authentication(user_a) -> None:  # noqa: ANN001
    response = APIClient().get("/api/recommendations/content/")

    assert response.status_code in {401, 302, 403}


@pytest.mark.django_db
def test_content_view_validates_algorithm_and_clamps_limit(user_a, genres) -> None:  # noqa: ANN001
    for index in range(3):
        _own(user_a, _work(f"view-owned-{index}", genres["rpg"]))
    for index in range(2):
        candidate = _work(f"view-candidate-{index}", genres["rpg"])
        candidate.rating = 80.0
        candidate.rating_count = 1
        candidate.save(update_fields=["rating", "rating_count"])
    client = APIClient()
    client.force_authenticate(user=user_a)

    unknown = client.get(
        "/api/recommendations/content/?algorithm_id=content-cbf-v999"
    )
    invalid = client.get("/api/recommendations/content/?limit=abc")
    clamped = client.get(
        "/api/recommendations/content/?limit=0&user=someone-else"
    )

    assert unknown.status_code == 400
    assert unknown.json() == {"detail": "unknown algorithm_id"}
    assert invalid.status_code == 400
    assert clamped.status_code == 200
    body = clamped.json()
    assert set(body) == {
        "protocol_version",
        "algorithm_id",
        "generated_at",
        "input_snapshot_sha256",
        "feature_set_version",
        "corpus_version",
        "snapshot_sha256",
        "popscore_snapshot_sha256",
        "candidate_manifest_sha256",
        "candidate_count",
        "explorable_count",
        "eligibility_cutoff_date",
        "insufficient_history",
        "limitation",
        "results",
    }
    assert len(body["results"]) == 1
    assert all(
        set(item)
        == {
            "work_id",
            "slug",
            "title",
            "score",
            "contributions",
            "rating_term",
            "rating_term_is_fallback",
            "display_rating",
            "year",
            "platform_summary",
            "cover",
            "reason",
        }
        for item in body["results"]
    )
