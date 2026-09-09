"""Phase 3 v2 profile and frozen-signal invariants."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone

from catalogue.models import CorpusRatingSnapshot, GameWork, Genre
from library.models import LibraryEntry
from recommendations.cancellation import RecommendationComputationCancelled
from recommendations.content.features import (
    compose_rating_confidence,
    rating_bayesian_normalized,
    rating_confidence,
    rating_final,
    rating_quality,
    normalise_rating,
    normalise_rating_volume,
    rating_quality_signal,
)
from recommendations.content.profile import build_profile_inputs
from recommendations.content.recency import recency_score
from recommendations.content.rank import rank_content_v1
from recommendations.content.combine import combine
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations._weights import _entry_weight


CORPUS = "content-v2-test"
User = get_user_model()


@pytest.fixture
def user(db):  # noqa: ANN001
    return User.objects.create_user(username="content-v2", password="Content-V2-Pass-9!")


@pytest.fixture
def genres(db):  # noqa: ANN001
    return {
        "rpg": Genre.objects.create(igdb_id=701, name="RPG", slug="rpg-v2"),
        "puzzle": Genre.objects.create(igdb_id=702, name="Puzzle", slug="puzzle-v2"),
    }


def work(slug: str, *genres: Genre) -> GameWork:
    item = GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug,
        in_corpus=True,
        corpus_version=CORPUS,
        rating=80.0,
        total_rating_count=10,
        first_release_date=date(2020, 1, 1),
    )
    item.genres.set(genres)
    return item


def entry(user, item: GameWork, status: str, rating: int | None) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(
        user=user, work=item, current_status=status, rating_half_steps=rating
    )


def snapshot(item: GameWork, rating: float, count: int) -> None:
    CorpusRatingSnapshot.objects.create(
        work=item,
        corpus_version=CORPUS,
        source="igdb",
        rating=rating,
        rating_count=count,
        retrieved_at=django_timezone.now(),
    )


def test_normalised_snapshot_scalars_preserve_missing_values() -> None:
    assert normalise_rating(75.0) == pytest.approx(0.75)
    assert rating_quality_signal(95.0) == pytest.approx(0.9025)
    assert rating_quality_signal(85.0) == pytest.approx(0.7225)
    assert rating_quality_signal(75.0) == pytest.approx(0.5625)
    assert normalise_rating(None) is None
    assert rating_quality_signal(None) is None
    assert normalise_rating_volume(99, 99) == pytest.approx(1.0)
    assert normalise_rating_volume(None, 99) is None
    assert normalise_rating_volume(0, 0) is None


def test_rating_confidence_does_not_apply_volume_twice() -> None:
    high_quality = rating_quality_signal(95.0)
    lower_quality = rating_quality_signal(85.0)

    assert compose_rating_confidence(high_quality, 1.0) > compose_rating_confidence(lower_quality, 1.0)
    assert compose_rating_confidence(high_quality, 1.0) == pytest.approx(
        compose_rating_confidence(high_quality, 0.1)
    )
    assert compose_rating_confidence(high_quality, None) == pytest.approx(high_quality)


def test_rating_signal_exposes_quality_confidence_and_final_once() -> None:
    normalized = rating_bayesian_normalized(90.0, 25, 70.0)

    assert normalized == pytest.approx(0.8)
    assert rating_quality(normalized) == pytest.approx(0.64)
    assert rating_confidence(25) == pytest.approx(0.5)
    assert rating_final(normalized, 25) == pytest.approx(0.32)
    assert 0.0 <= rating_final(normalized, 25) <= 1.0


def test_personal_rating_intensity_prioritises_high_seed_ratings() -> None:
    assert _entry_weight("completed", 10) == pytest.approx(4.0)
    assert _entry_weight("completed", 8) == pytest.approx(3.64)
    assert _entry_weight("completed", 7) == pytest.approx(3.49)
    assert _entry_weight("completed", 10) > _entry_weight("completed", 8) > _entry_weight("completed", 7)


def test_popscore_variants_penalise_missing_popscore_with_the_minimum_floor() -> None:
    for algorithm_id in (
        "content-cbf-weighted-pop-v1",
        "content-cbf-multiplicative-pop-v1",
        "content-cbf-twostage-pop-v1",
        "content-cbf-neg-pop-v1",
    ):
        spec = ALGORITHM_REGISTRY[algorithm_id]
        missing = combine(0.8, 0.8, None, spec, popscore=None)
        maximum = combine(0.8, 0.8, None, spec, popscore=1.0)

        assert spec.params["popscore_missing_floor"] == 0.0
        assert missing < maximum

    recency = ALGORITHM_REGISTRY["recency-v1"]
    assert combine(0.8, 0.8, None, recency, popscore=None, recency_score=1.0) < combine(
        0.8, 0.8, None, recency, popscore=1.0, recency_score=1.0
    )


def test_recency_score_is_bounded_and_requires_released_rated_work() -> None:
    cutoff = date(2026, 9, 9)

    assert recency_score(date(2026, 9, 9), eligibility_cutoff_date=cutoff, has_external_rating=True) == pytest.approx(1.0)
    assert recency_score(date(2025, 9, 9), eligibility_cutoff_date=cutoff, has_external_rating=True) == pytest.approx(0.35)
    assert recency_score(date(2024, 9, 9), eligibility_cutoff_date=cutoff, has_external_rating=True) == pytest.approx(0.35**2)
    assert recency_score(date(2011, 9, 9), eligibility_cutoff_date=cutoff, has_external_rating=True) < 1e-6
    assert recency_score(None, eligibility_cutoff_date=cutoff, has_external_rating=True) is None
    assert recency_score(date(2026, 10, 1), eligibility_cutoff_date=cutoff, has_external_rating=True) is None
    assert recency_score(date(2026, 9, 9), eligibility_cutoff_date=cutoff, has_external_rating=False) is None


@pytest.mark.django_db
def test_content_ranking_stops_before_work_when_cancelled(user) -> None:  # noqa: ANN001
    with pytest.raises(RecommendationComputationCancelled):
        rank_content_v1(
            user,
            "content-cbf-weighted-v1",
            corpus_version=CORPUS,
            should_continue=lambda: False,
        )


@pytest.mark.django_db
def test_profile_accepts_playing_positive_ratings_and_ignores_pending(user, genres) -> None:  # noqa: ANN001
    entry(user, work("completed-rpg", genres["rpg"]), "completed", 8)
    entry(user, work("playing-puzzle", genres["puzzle"]), "playing", 10)
    entry(user, work("pending-rpg", genres["rpg"]), "pending", 10)
    entry(user, work("unrated-rpg", genres["rpg"]), "completed", None)

    profile = build_profile_inputs(user, CORPUS)

    assert profile.positive_entry_count == 2
    assert set(profile.positive) == {"genre:rpg-v2", "genre:puzzle-v2"}
    assert profile.negative == {}


@pytest.mark.django_db
def test_negative_genre_is_isolated_until_three_low_ratings(user, genres) -> None:  # noqa: ANN001
    for index in range(2):
        entry(user, work(f"low-rpg-{index}", genres["rpg"]), "completed", 6)
    assert build_profile_inputs(user, CORPUS).negative == {}

    entry(user, work("low-rpg-third", genres["rpg"]), "playing", 4)
    profile = build_profile_inputs(user, CORPUS)

    assert profile.negative_genres == ("genre:rpg-v2",)
    assert profile.negative == {"genre:rpg-v2": pytest.approx(1.0)}


@pytest.mark.django_db
def test_negative_variant_penalises_only_the_guarded_negative_genre(user, genres) -> None:  # noqa: ANN001
    for index in range(3):
        entry(user, work(f"positive-puzzle-{index}", genres["puzzle"]), "completed", 10)
        entry(user, work(f"negative-rpg-{index}", genres["rpg"]), "completed", 4)
    rpg = work("candidate-rpg", genres["rpg"])
    puzzle = work("candidate-puzzle", genres["puzzle"])
    unobserved = work("candidate-unobserved", genres["puzzle"])
    snapshot(rpg, 85.0, 100)
    snapshot(puzzle, 85.0, 100)

    payload = rank_content_v1(
        user,
        "content-cbf-neg-v1",
        corpus_version=CORPUS,
        min_rating_count=None,
        generated_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
    )
    by_slug = {item["slug"]: item for item in payload["results"]}

    assert by_slug["candidate-rpg"]["negative_similarity"] > 0
    assert by_slug["candidate-puzzle"]["negative_similarity"] == 0
    assert by_slug["candidate-puzzle"]["score"] > by_slug["candidate-rpg"]["score"]
    assert by_slug[unobserved.canonical_slug]["signals"]["external_rating"] is None
    assert by_slug[unobserved.canonical_slug]["signals"]["rating_volume"] is None
    assert payload["parameters"]["negative_penalty"] == 1.0
    assert payload["signal_availability"]["popscore_available"] is False


@pytest.mark.django_db
def test_recency_variant_adds_released_rated_age_to_the_other_signals(user, genres) -> None:  # noqa: ANN001
    for index in range(3):
        entry(user, work(f"history-{index}", genres["rpg"]), "completed", 10)
    recent = work("recent", genres["rpg"])
    recent.first_release_date = date(2026, 9, 9)
    recent.save(update_fields=["first_release_date"])
    older = work("older", genres["rpg"])
    older.first_release_date = date(2025, 9, 9)
    older.save(update_fields=["first_release_date"])
    unrated = work("unrated", genres["rpg"])
    unrated.first_release_date = date(2026, 9, 9)
    unrated.save(update_fields=["first_release_date"])
    snapshot(recent, 80.0, 10)
    snapshot(older, 80.0, 10)

    payload = rank_content_v1(
        user,
        "recency-v1",
        corpus_version=CORPUS,
        min_rating_count=None,
        eligibility_cutoff_date=date(2026, 9, 9),
    )
    by_slug = {item["slug"]: item for item in payload["results"]}

    assert by_slug["recent"]["score"] > by_slug["older"]["score"]
    assert by_slug["recent"]["signals"]["recency_score"] == pytest.approx(1.0)
    assert by_slug["older"]["signals"]["recency_score"] == pytest.approx(0.35)
    assert by_slug["unrated"]["signals"]["recency_score"] is None
    assert by_slug["unrated"]["signals"]["popscore"] == 0.0
    assert by_slug["unrated"]["signals"]["popscore_imputed"] is True
