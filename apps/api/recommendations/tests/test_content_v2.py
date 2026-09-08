"""Phase 3 v2 profile and frozen-signal invariants."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone

from catalogue.models import CorpusRatingSnapshot, GameWork, Genre
from library.models import LibraryEntry
from recommendations.content.features import normalise_rating, normalise_rating_volume
from recommendations.content.profile import build_profile_inputs
from recommendations.content.rank import rank_content_v1


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
        total_rating_count=1,
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
    assert normalise_rating(None) is None
    assert normalise_rating_volume(99, 99) == pytest.approx(1.0)
    assert normalise_rating_volume(None, 99) is None
    assert normalise_rating_volume(0, 0) is None


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
