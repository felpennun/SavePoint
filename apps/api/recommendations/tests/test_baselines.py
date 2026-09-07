"""Tests for the random comparison-floor baseline (REC-01) and the stdlib
cosine similarity used by the content recommender laboratory (D-12).

Plan 02-10 Task 2. ``rank_random_v1`` mirrors ``library/popularity.py``'s
deterministic-DTO contract exactly -- same key grammar, same
``input_snapshot_sha256`` discipline -- but draws uniformly at random from the
governed corpus minus the user's own library. It is a comparison floor only
and must never be presented as a recommendation of taste.
"""

from __future__ import annotations

import math

import pytest
from django.contrib.auth import get_user_model

from catalogue.models import GameWork
from library.models import LibraryEntry
from library.popularity import rank_popularity_v1
from recommendations.baselines import ALGORITHM_ID, rank_random_v1
from recommendations.content.similarity import cosine

User = get_user_model()


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="rnd-user-a", password="Rnd-User-A-Pass-9!")


def _governed_work(slug: str, *, is_dlc: bool = False) -> GameWork:
    return GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        is_dlc=is_dlc,
        in_corpus=not is_dlc,
        corpus_version="test-corpus" if not is_dlc else "",
    )


def _own(user, work: GameWork) -> LibraryEntry:  # noqa: ANN001
    return LibraryEntry.objects.create(user=user, work=work, current_status="completed")


def _ranked_slugs(result: dict) -> list[str]:
    return [item["slug"] for item in result["results"]]


# --------------------------------------------------------------------------- #
# rank_random_v1                                                               #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_same_seed_produces_identical_ranking_and_fingerprint(user_a) -> None:  # noqa: ANN001
    for idx in range(25):
        _governed_work(f"gov-{idx:02d}")

    first = rank_random_v1(user_a, seed=42, limit=10)
    second = rank_random_v1(user_a, seed=42, limit=10)

    assert _ranked_slugs(first) == _ranked_slugs(second)
    assert first["input_snapshot_sha256"] == second["input_snapshot_sha256"]


@pytest.mark.django_db
def test_different_seed_produces_a_different_order(user_a) -> None:  # noqa: ANN001
    for idx in range(25):
        _governed_work(f"gov-{idx:02d}")

    one = rank_random_v1(user_a, seed=1, limit=10)
    two = rank_random_v1(user_a, seed=2, limit=10)

    assert _ranked_slugs(one) != _ranked_slugs(two)
    assert one["input_snapshot_sha256"] != two["input_snapshot_sha256"]


@pytest.mark.django_db
def test_never_returns_a_work_in_the_users_library(user_a) -> None:  # noqa: ANN001
    owned = [_governed_work(f"owned-{idx:02d}") for idx in range(5)]
    for work in owned:
        _own(user_a, work)
    for idx in range(20):
        _governed_work(f"unseen-{idx:02d}")

    result = rank_random_v1(user_a, seed=7, limit=20)
    slugs = set(_ranked_slugs(result))

    assert slugs.isdisjoint({w.canonical_slug for w in owned})
    assert all(slug.startswith("unseen-") for slug in slugs)


@pytest.mark.django_db
def test_only_draws_from_the_governed_corpus(user_a) -> None:  # noqa: ANN001
    for idx in range(10):
        _governed_work(f"gov-{idx:02d}")
    # Not in corpus -- must never appear.
    GameWork.objects.create(
        canonical_slug="ungoverned", original_title="Ungoverned", in_corpus=False
    )
    # DLC is excluded from the governed view.
    _governed_work("gov-dlc", is_dlc=True)

    result = rank_random_v1(user_a, seed=3, limit=20)
    slugs = set(_ranked_slugs(result))

    assert "ungoverned" not in slugs
    assert "gov-dlc" not in slugs
    assert len(slugs) == 10


@pytest.mark.django_db
def test_dto_grammar_matches_rank_popularity_v1(user_a) -> None:  # noqa: ANN001
    for idx in range(12):
        _governed_work(f"gov-{idx:02d}")

    random_dto = rank_random_v1(user_a, seed=5, limit=10)
    popularity_dto = rank_popularity_v1()

    assert set(random_dto) == set(popularity_dto)
    assert random_dto["algorithm_id"] == ALGORITHM_ID == "random-v1"
    assert len(random_dto["input_snapshot_sha256"]) == 64
    assert "comparison floor" in random_dto["limitation"].lower()
    for item in random_dto["results"]:
        assert set(item) == {"work_id", "slug", "title", "score"}
        assert item["score"] >= 0.0


@pytest.mark.django_db
def test_limit_is_clamped_when_there_are_fewer_candidates(user_a) -> None:  # noqa: ANN001
    for idx in range(3):
        _governed_work(f"gov-{idx:02d}")

    result = rank_random_v1(user_a, seed=9, limit=10)

    assert len(result["results"]) == 3


@pytest.mark.django_db
def test_fingerprint_changes_when_the_candidate_set_changes(user_a) -> None:  # noqa: ANN001
    for idx in range(15):
        _governed_work(f"gov-{idx:02d}")
    before = rank_random_v1(user_a, seed=11, limit=5)

    _governed_work("gov-late-arrival")
    after = rank_random_v1(user_a, seed=11, limit=5)

    assert before["input_snapshot_sha256"] != after["input_snapshot_sha256"]


# --------------------------------------------------------------------------- #
# cosine (stdlib)                                                              #
# --------------------------------------------------------------------------- #
def test_cosine_of_a_vector_with_itself_is_exactly_one() -> None:
    vec = {"genre:rpg": 1 / math.sqrt(3), "genre:shooter": 1 / math.sqrt(3), "platform:pc": 0.5}

    assert cosine(vec, vec) == 1.0
    assert cosine(dict(vec), vec) == 1.0


def test_cosine_is_bounded_between_zero_and_one() -> None:
    p = {"a": 1.0, "b": 2.0, "c": 3.0}
    v = {"b": 1.0, "c": 1.0, "d": 5.0}

    value = cosine(p, v)

    assert 0.0 <= value <= 1.0


def test_cosine_of_orthogonal_vectors_is_zero() -> None:
    assert cosine({"a": 1.0, "b": 2.0}, {"c": 3.0, "d": 4.0}) == 0.0


def test_cosine_with_an_empty_or_zero_vector_is_zero() -> None:
    assert cosine({}, {"a": 1.0}) == 0.0
    assert cosine({"a": 1.0}, {}) == 0.0
    assert cosine({"a": 0.0}, {"a": 0.0}) == 0.0


def test_cosine_matches_the_hand_computed_value() -> None:
    p = {"a": 1.0, "b": 1.0}
    v = {"a": 1.0}
    # num = 1; |p| = sqrt(2); |v| = 1 -> 1 / sqrt(2)
    assert cosine(p, v) == pytest.approx(1 / math.sqrt(2))
