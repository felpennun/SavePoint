"""Tests for the genre-taste-v1 heuristic and its authenticated API.

Plan 01.1-05 (REC-10). The service mirrors ``library/popularity.py``'s
deterministic-DTO contract but is scoped strictly to the signed-in user's
own recorded activity (D-09): it must be visibly distinct from the public
popularity baseline (REC-02) and must never fall back to it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogue.models import AssetAttribution, GameWork, Genre
from library.models import LibraryEntry
from recommendations.genre_heuristic import ALGORITHM_ID, rank_genre_taste_v1

User = get_user_model()


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="rec-user-a", password="Rec-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="rec-user-b", password="Rec-User-B-Pass-9!")


@pytest.fixture
def genres(db):  # noqa: ANN001
    return {
        "rpg": Genre.objects.create(igdb_id=12, name="Role-playing (RPG)", slug="role-playing-rpg"),
        "shooter": Genre.objects.create(igdb_id=5, name="Shooter", slug="shooter"),
        "puzzle": Genre.objects.create(igdb_id=9, name="Puzzle", slug="puzzle"),
    }


def _work(slug: str, *genre_objs: Genre, is_dlc: bool = False) -> GameWork:
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        is_dlc=is_dlc,
        total_rating_count=1000,
    )
    if genre_objs:
        work.genres.set(genre_objs)
    return work


def _own(user, work: GameWork, *, status: str | None = "completed", rating: int | None = None) -> LibraryEntry:  # noqa: ANN001
    return LibraryEntry.objects.create(
        user=user, work=work, current_status=status, rating_half_steps=rating
    )


def _slugs(result: dict) -> list[str]:
    return [item["slug"] for item in result["results"]]


# --------------------------------------------------------------------------- #
# Service: DTO contract                                                        #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_empty_history_returns_explicit_insufficient_result(user_a) -> None:  # noqa: ANN001
    result = rank_genre_taste_v1(user_a, limit=10)

    assert result["insufficient_history"] is True
    assert result["results"] == []
    assert result["algorithm_id"] == ALGORITHM_ID == "genre-taste-v1"
    # NEVER a silent fall-back to the public popularity baseline (D-09).
    assert "popularity" not in result["limitation"].lower()


@pytest.mark.django_db
def test_dto_always_declares_identity_hash_and_bounded_limitation(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _work("unseen-rpg", genres["rpg"])

    result = rank_genre_taste_v1(user_a, limit=10)

    assert result["algorithm_id"] == "genre-taste-v1"
    assert "generated_at" in result
    assert isinstance(result["input_snapshot_sha256"], str)
    assert len(result["input_snapshot_sha256"]) == 64
    assert result["insufficient_history"] is False
    # The limitation string explicitly bounds this away from Phase 6's model
    # comparison so the frontend cannot confuse it with REC-03 research work.
    lowered = result["limitation"].lower()
    assert "phase 6" in lowered
    assert "trained model" in lowered


# --------------------------------------------------------------------------- #
# Service: genre taste is derived from the user's own activity                 #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_rated_completed_activity_weights_the_users_genres(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _work("unseen-rpg", genres["rpg"])
    _work("unseen-shooter", genres["shooter"])

    result = rank_genre_taste_v1(user_a, limit=10)

    # The RPG work is recommended; the shooter work has zero overlap with the
    # user's taste and never appears.
    assert "unseen-rpg" in _slugs(result)
    assert "unseen-shooter" not in _slugs(result)


@pytest.mark.django_db
def test_owned_or_in_library_works_never_appear(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    # An entry with no status/rating still counts as "in library" -> excluded.
    _own(user_a, _work("tracked-rpg", genres["rpg"]), status=None, rating=None)
    _work("unseen-rpg", genres["rpg"])

    result = rank_genre_taste_v1(user_a, limit=10)

    assert "owned-rpg" not in _slugs(result)
    assert "tracked-rpg" not in _slugs(result)
    assert "unseen-rpg" in _slugs(result)


@pytest.mark.django_db
def test_dlc_is_excluded_from_candidates(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _work("unseen-rpg-dlc", genres["rpg"], is_dlc=True)
    _work("unseen-rpg", genres["rpg"])

    result = rank_genre_taste_v1(user_a, limit=10)

    assert "unseen-rpg-dlc" not in _slugs(result)
    assert "unseen-rpg" in _slugs(result)


@pytest.mark.django_db
def test_stronger_genre_overlap_ranks_higher(user_a, genres) -> None:  # noqa: ANN001
    # User activity: heavy RPG, light shooter.
    _own(user_a, _work("owned-rpg-1", genres["rpg"]), status="completed", rating=10)
    _own(user_a, _work("owned-rpg-2", genres["rpg"]), status="completed", rating=10)
    _own(user_a, _work("owned-shooter", genres["shooter"]), status="pending", rating=None)

    both = _work("unseen-rpg-shooter", genres["rpg"], genres["shooter"])  # noqa: F841
    only_shooter = _work("unseen-shooter-only", genres["shooter"])  # noqa: F841

    result = rank_genre_taste_v1(user_a, limit=10)
    slugs = _slugs(result)

    assert slugs.index("unseen-rpg-shooter") < slugs.index("unseen-shooter-only")


@pytest.mark.django_db
def test_catalogue_rating_orders_matching_candidates_before_numeric_titles(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status=None, rating=10)
    low = _work("100 Animals", genres["rpg"])
    low.total_rating = 25.0
    low.save(update_fields=["total_rating"])
    high = _work("100 Tokyo Cats", genres["rpg"])
    high.total_rating = 95.0
    high.save(update_fields=["total_rating"])

    result = rank_genre_taste_v1(user_a, limit=10)

    assert [item["slug"] for item in result["results"]] == ["100 Tokyo Cats", "100 Animals"]
    assert result["results"][0]["catalogue_rating"] == 95.0
    assert result["results"][1]["catalogue_rating"] == 25.0


@pytest.mark.django_db
def test_candidates_need_at_least_one_thousand_catalogue_ratings(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status=None, rating=10)
    excluded = _work("small-sample-rpg", genres["rpg"])
    excluded.total_rating_count = 999
    excluded.save(update_fields=["total_rating_count"])
    included = _work("large-sample-rpg", genres["rpg"])
    included.total_rating_count = 1000
    included.save(update_fields=["total_rating_count"])

    result = rank_genre_taste_v1(user_a, limit=10)

    assert _slugs(result) == ["large-sample-rpg"]
    assert result["results"][0]["catalogue_rating_count"] == 1000


# --------------------------------------------------------------------------- #
# Service: determinism                                                         #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_ties_break_by_canonical_slug_ascending(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _work("zzz-tie", genres["rpg"])
    _work("aaa-tie", genres["rpg"])

    result = rank_genre_taste_v1(user_a, limit=10)
    tied = [s for s in _slugs(result) if s in ("aaa-tie", "zzz-tie")]

    assert tied == ["aaa-tie", "zzz-tie"]


@pytest.mark.django_db
def test_tie_break_holds_at_the_limit_boundary(user_a, genres) -> None:  # noqa: ANN001
    """L-03: with rating-driven weights (multiples of 0.1, not exactly
    representable) two equally-scored works can carry different float sums.
    The exact Python re-score must still cut on canonical_slug at limit=1, so
    the DB's float ordering can never decide which side of the boundary a
    tied work lands on."""
    # A rating of 7 half-steps -> 0.7 rating contribution + 3 (completed) per
    # matched genre; both candidate works share the same two taste genres, so
    # their rational scores are identical.
    _own(user_a, _work("owned-a", genres["rpg"]), status="completed", rating=7)
    _own(user_a, _work("owned-b", genres["shooter"]), status="completed", rating=7)
    _work("mmm-boundary", genres["rpg"], genres["shooter"])
    _work("bbb-boundary", genres["rpg"], genres["shooter"])

    result = rank_genre_taste_v1(user_a, limit=1)

    assert _slugs(result) == ["bbb-boundary"]


@pytest.mark.django_db
def test_identical_inputs_produce_identical_ranking_and_hash(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=8)
    _work("unseen-rpg-1", genres["rpg"])
    _work("unseen-rpg-2", genres["rpg"])

    cutoff = datetime.now(timezone.utc)
    first = rank_genre_taste_v1(user_a, limit=10, generated_at=cutoff)
    second = rank_genre_taste_v1(user_a, limit=10, generated_at=cutoff)

    assert first["input_snapshot_sha256"] == second["input_snapshot_sha256"]
    assert first["results"] == second["results"]


@pytest.mark.django_db
def test_hash_changes_when_user_activity_changes(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=6)
    _work("unseen-rpg", genres["rpg"])
    _work("unseen-shooter", genres["shooter"])

    before = rank_genre_taste_v1(user_a, limit=10)
    _own(user_a, _work("owned-shooter", genres["shooter"]), status="completed", rating=10)
    after = rank_genre_taste_v1(user_a, limit=10)

    assert before["input_snapshot_sha256"] != after["input_snapshot_sha256"]


# --------------------------------------------------------------------------- #
# Service: cross-user isolation                                               #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_cross_user_isolation(user_a, user_b, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("a-owned-rpg", genres["rpg"]), status="completed", rating=10)
    _own(user_b, _work("b-owned-shooter", genres["shooter"]), status="completed", rating=10)
    _work("unseen-rpg", genres["rpg"])
    _work("unseen-shooter", genres["shooter"])

    result_a = rank_genre_taste_v1(user_a, limit=10)
    result_b = rank_genre_taste_v1(user_b, limit=10)

    assert _slugs(result_a) == ["unseen-rpg"]
    assert _slugs(result_b) == ["unseen-shooter"]


# --------------------------------------------------------------------------- #
# Service: explanations                                                        #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_each_item_carries_genre_overlap_explanation_evidence(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _work("unseen-rpg", genres["rpg"])

    result = rank_genre_taste_v1(user_a, limit=10)
    item = next(i for i in result["results"] if i["slug"] == "unseen-rpg")

    assert set(item) >= {"work_id", "slug", "title", "score", "matched_genres"}
    assert item["score"] > 0
    matched = item["matched_genres"]
    assert [g["slug"] for g in matched] == ["role-playing-rpg"]
    assert matched[0]["weight"] > 0
    assert matched[0]["name"] == "Role-playing (RPG)"


# --------------------------------------------------------------------------- #
# Service: bounded limit                                                       #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_limit_is_respected(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    for idx in range(5):
        _work(f"unseen-rpg-{idx}", genres["rpg"])

    result = rank_genre_taste_v1(user_a, limit=3)

    assert len(result["results"]) == 3


@pytest.mark.django_db
def test_out_of_range_limit_is_clamped_to_documented_bounds(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    for idx in range(4):
        _work(f"unseen-rpg-{idx}", genres["rpg"])

    # Below the minimum clamps up to 1 (never 0, never unbounded).
    too_small = rank_genre_taste_v1(user_a, limit=0)
    assert len(too_small["results"]) == 1

    # Above the maximum clamps down to the 50-item ceiling.
    too_big = rank_genre_taste_v1(user_a, limit=10_000)
    assert len(too_big["results"]) <= 50


@pytest.mark.django_db
def test_activity_without_genre_data_is_insufficient_history(user_a) -> None:  # noqa: ANN001
    # Works carry no genres at all -> no taste vector can be built.
    _own(user_a, _work("owned-no-genre"), status="completed", rating=10)
    _work("unseen-no-genre")

    result = rank_genre_taste_v1(user_a, limit=10)

    assert result["insufficient_history"] is True
    assert result["results"] == []


@pytest.mark.django_db
def test_service_snapshot_filters_activity_after_the_generated_at_cutoff(user_a, genres) -> None:  # noqa: ANN001
    entry = _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _work("unseen-rpg", genres["rpg"])
    # Force the activity to look older than the cutoff we will pass.
    LibraryEntry.objects.filter(pk=entry.pk).update(
        updated_at=datetime.now(timezone.utc) - timedelta(days=2)
    )

    past_cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    future_cutoff = datetime.now(timezone.utc)

    assert rank_genre_taste_v1(user_a, limit=10, generated_at=past_cutoff)["insufficient_history"] is False
    # Everything is before `future_cutoff`, so the ranking is still produced.
    assert rank_genre_taste_v1(user_a, limit=10, generated_at=future_cutoff)["insufficient_history"] is False


# --------------------------------------------------------------------------- #
# Endpoint: GET /api/recommendations/genre-taste/                             #
# --------------------------------------------------------------------------- #
_ENDPOINT = "/api/recommendations/genre-taste/"
_DTO_KEYS = {
    "algorithm_id",
    "generated_at",
    "input_snapshot_sha256",
    "insufficient_history",
    "limitation",
    "results",
}
_ITEM_KEYS = {
    "work_id",
    "slug",
    "title",
    "score",
    "catalogue_rating",
    "catalogue_rating_count",
    "year",
    "platform_summary",
    "cover",
    "matched_genres",
}


@pytest.mark.django_db
def test_endpoint_returns_current_users_ranking_with_allowlisted_dto(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    _work("unseen-rpg", genres["rpg"])

    client = APIClient()
    client.force_authenticate(user=user_a)
    response = client.get(_ENDPOINT)

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm_id"] == "genre-taste-v1"
    assert "phase 6" in body["limitation"].lower()
    assert set(body) == _DTO_KEYS
    assert [item["slug"] for item in body["results"]] == ["unseen-rpg"]
    assert set(body["results"][0]) == _ITEM_KEYS


@pytest.mark.django_db
def test_recommendation_item_includes_card_cover_metadata(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    recommended = _work("recommended-rpg", genres["rpg"])
    AssetAttribution.objects.create(
        work=recommended,
        file_url="https://cdn.example.test/recommended-rpg.jpg",
        creator="Catalogue source",
        licence="Catalogue terms",
        licence_url="https://example.test/licence",
        source_url="https://example.test/recommended-rpg",
        display_allowed=True,
    )

    client = APIClient()
    client.force_authenticate(user=user_a)
    item = client.get(_ENDPOINT).json()["results"][0]

    assert item["cover"]["is_placeholder"] is False
    assert item["cover"]["url"] == "https://cdn.example.test/recommended-rpg.jpg"


@pytest.mark.django_db
def test_endpoint_isolates_taste_between_authenticated_users(user_a, user_b, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("a-owned-rpg", genres["rpg"]), status="completed", rating=10)
    _own(user_b, _work("b-owned-shooter", genres["shooter"]), status="completed", rating=10)
    _work("unseen-rpg", genres["rpg"])
    _work("unseen-shooter", genres["shooter"])

    client = APIClient()
    client.force_authenticate(user=user_a)
    body_a = client.get(_ENDPOINT).json()

    client.force_authenticate(user=user_b)
    body_b = client.get(_ENDPOINT).json()

    assert [item["slug"] for item in body_a["results"]] == ["unseen-rpg"]
    assert [item["slug"] for item in body_b["results"]] == ["unseen-shooter"]
    assert body_a["input_snapshot_sha256"] != body_b["input_snapshot_sha256"]


@pytest.mark.django_db
def test_endpoint_denies_anonymous_requests_without_leaking_taste_data() -> None:
    response = APIClient().get(_ENDPOINT)

    assert response.status_code == 403
    assert "results" not in response.json()


@pytest.mark.django_db
def test_endpoint_rejects_non_integer_limit(user_a) -> None:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user_a)
    response = client.get(_ENDPOINT, {"limit": "abc"})

    assert response.status_code == 400
    assert "results" not in response.json()


@pytest.mark.django_db
def test_endpoint_clamps_out_of_range_limit(user_a, genres) -> None:  # noqa: ANN001
    _own(user_a, _work("owned-rpg", genres["rpg"]), status="completed", rating=10)
    for idx in range(3):
        _work(f"unseen-rpg-{idx}", genres["rpg"])

    client = APIClient()
    client.force_authenticate(user=user_a)

    small = client.get(_ENDPOINT, {"limit": "0"})
    assert small.status_code == 200
    assert len(small.json()["results"]) == 1

    big = client.get(_ENDPOINT, {"limit": "9999"})
    assert big.status_code == 200
    assert len(big.json()["results"]) <= 50


@pytest.mark.django_db
def test_endpoint_reports_insufficient_history_without_falling_back(user_a) -> None:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user_a)
    body = client.get(_ENDPOINT).json()

    assert body["insufficient_history"] is True
    assert body["results"] == []
    assert "popularity" not in body["limitation"].lower()
