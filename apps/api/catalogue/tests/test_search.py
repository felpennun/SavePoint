"""Tests for tolerant catalogue search (Plan 01-06 Task 2, CAT-01/CAT-06)
plus the CAT-02 filter/sort/facet contract (Plan 01.1-03 Task 1)."""

from __future__ import annotations

import socket
from datetime import date

import pytest
from rest_framework.test import APIClient

from catalogue.models import GameAlias, GameRelease, GameWork, Genre, Platform, SourceRecord
from catalogue.normalization import normalize_title
from catalogue.search import (
    SORT_ORDERS,
    CatalogueQuery,
    FilterValidationError,
    parse_catalogue_query,
    search_games,
)


def _make_work(title: str, *, is_dlc: bool = False, year: int | None = None, platform_name: str | None = None) -> GameWork:
    slug = title.lower().replace(" ", "-").replace("'", "")
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=title,
        title_en=title,
        title_es="",
        is_dlc=is_dlc,
    )
    GameAlias.objects.create(work=work, locale="en", value=title, normalized_value=normalize_title(title))
    if platform_name:
        platform, _ = Platform.objects.get_or_create(name=platform_name, defaults={"slug": platform_name.lower()})
        GameRelease.objects.create(
            work=work,
            platform=platform,
            release_name=f"{title} ({platform_name})",
            release_date=date(year, 1, 1) if year else None,
        )
    SourceRecord.objects.create(
        work=work,
        source="wikidata",
        source_id=f"Q{work.id.int % 100000}",
        source_url="https://www.wikidata.org/wiki/Q1",
        retrieved_at="2026-09-04T00:00:00Z",
        licence="CC0 1.0",
        snapshot_sha256="0" * 64,
    )
    return work


@pytest.mark.django_db
def test_exact_match_ranks_first() -> None:
    _make_work("Quake")
    _make_work("Quake II")
    result = search_games("Quake")
    titles = [w.original_title for w in result["results"]]
    assert titles[0] == "Quake"


@pytest.mark.django_db
def test_prefix_match() -> None:
    _make_work("Assassin's Creed II")
    result = search_games("Assassin")
    assert any(w.original_title == "Assassin's Creed II" for w in result["results"])


@pytest.mark.django_db
def test_accent_and_case_insensitive() -> None:
    _make_work("Pokémon")
    result = search_games("pokemon")
    assert any(w.original_title == "Pokémon" for w in result["results"])
    result_upper = search_games("POKÉMON")
    assert any(w.original_title == "Pokémon" for w in result_upper["results"])


@pytest.mark.django_db
def test_small_typo_tolerated_via_trigram() -> None:
    _make_work("Boulder Dash")
    result = search_games("Boulder Dach")  # one-letter typo
    assert any(w.original_title == "Boulder Dash" for w in result["results"])


@pytest.mark.django_db
def test_whitespace_only_query_returns_unfiltered_catalogue() -> None:
    _make_work("Alpha Game")
    _make_work("Beta Game")
    result = search_games("   ")
    assert result["count"] == 2


@pytest.mark.django_db
def test_dlc_excluded_from_search_results() -> None:
    _make_work("Base Game")
    _make_work("Base Game Season Pass", is_dlc=True)
    result = search_games("Base Game")
    titles = [w.original_title for w in result["results"]]
    assert "Base Game Season Pass" not in titles


@pytest.mark.django_db
def test_pagination_defaults_to_24_per_page() -> None:
    for i in range(30):
        _make_work(f"Game {i:02d}")
    result = search_games(None, page=1)
    assert result["page_size"] == 24
    assert len(result["results"]) == 24
    assert result["has_next"] is True

    result_page_2 = search_games(None, page=2)
    assert len(result_page_2["results"]) == 6
    assert result_page_2["has_next"] is False


@pytest.mark.django_db
def test_search_is_deterministically_ordered_across_repeated_calls() -> None:
    for i in range(5):
        _make_work(f"Repeat Game {i}")
    first = [w.id for w in search_games("Repeat")["results"]]
    second = [w.id for w in search_games("Repeat")["results"]]
    assert first == second


@pytest.mark.django_db
def test_list_endpoint_no_external_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """CAT-06/OPS-03: catalogue must remain usable with zero external calls."""

    def _blocked(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("catalogue search must never open a network socket")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    _make_work("Local Only Game")

    client = APIClient()
    response = client.get("/api/catalogue/games/", {"q": "Local"})
    assert response.status_code == 200
    assert response.json()["count"] == 1


# ---------------------------------------------------------------------------
# Plan 01.1-03 Task 1 -- CAT-02 filters, stable sort allowlist, facets
# ---------------------------------------------------------------------------


def _genre(name: str, igdb_id: int) -> Genre:
    slug = name.lower().replace(" ", "-").replace("/", "-").replace("'", "")
    return Genre.objects.create(igdb_id=igdb_id, name=name, slug=slug)


def _work(
    title: str,
    *,
    is_dlc: bool = False,
    year: int | None = None,
    rating: float | None = None,
    platforms: tuple[str, ...] = (),
    genres: tuple[Genre, ...] = (),
) -> GameWork:
    slug = title.lower().replace(" ", "-").replace("'", "").replace(":", "")
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=title,
        title_en=title,
        title_es="",
        is_dlc=is_dlc,
        first_release_date=date(year, 1, 1) if year else None,
        total_rating=rating,
    )
    GameAlias.objects.create(work=work, locale="en", value=title, normalized_value=normalize_title(title))
    for pname in platforms:
        platform, _ = Platform.objects.get_or_create(name=pname, defaults={"slug": pname.lower().replace(" ", "-")})
        GameRelease.objects.create(
            work=work,
            platform=platform,
            release_name=f"{title} ({pname})",
            release_date=date(year, 1, 1) if year else None,
        )
    if genres:
        work.genres.set(genres)
    SourceRecord.objects.create(
        work=work,
        source="igdb",
        source_id=str(work.id.int % 1_000_000),
        source_url="https://www.igdb.com/games/x",
        retrieved_at="2026-09-04T00:00:00Z",
        licence="IGDB",
        snapshot_sha256="0" * 64,
    )
    return work


@pytest.mark.django_db
def test_parse_rejects_unknown_sort_key() -> None:
    with pytest.raises(FilterValidationError):
        parse_catalogue_query({"sort": "id); DROP TABLE catalogue_gamework;--"})
    with pytest.raises(FilterValidationError):
        parse_catalogue_query({"sort": "total_rating"})  # a real column, still not an allowlisted key


@pytest.mark.django_db
def test_parse_rejects_out_of_range_and_non_numeric_year_and_rating() -> None:
    for bad in ({"year_from": "1200"}, {"year_to": "3999"}, {"year_from": "abc"}):
        with pytest.raises(FilterValidationError):
            parse_catalogue_query(bad)
    for bad in ({"min_rating": "-5"}, {"min_rating": "150"}, {"min_rating": "high"}):
        with pytest.raises(FilterValidationError):
            parse_catalogue_query(bad)


@pytest.mark.django_db
def test_parse_swaps_reversed_year_bounds() -> None:
    cq = parse_catalogue_query({"year_from": "2015", "year_to": "2001"})
    assert (cq.year_from, cq.year_to) == (2001, 2015)


@pytest.mark.django_db
def test_hostile_sort_value_returns_bounded_400_and_selects_nothing() -> None:
    _work("Anything", year=2000)
    client = APIClient()
    response = client.get("/api/catalogue/games/", {"sort": "canonical_slug; SELECT"})
    assert response.status_code == 400
    body = response.json()
    assert "results" not in body  # no data leaked, purely a validation error


@pytest.mark.django_db
def test_out_of_range_year_returns_400_from_endpoint() -> None:
    client = APIClient()
    assert client.get("/api/catalogue/games/", {"year_from": "1000"}).status_code == 400
    assert client.get("/api/catalogue/games/", {"min_rating": "999"}).status_code == 400


@pytest.mark.django_db
def test_platform_filter_limits_results() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("PC Only", year=2018, platforms=("PC",), genres=(rpg,))
    _work("Console Only", year=2019, platforms=("PlayStation 5",), genres=(rpg,))

    result = search_games(cq=parse_catalogue_query({"platform": "pc"}))
    titles = {w.original_title for w in result["results"]}
    assert titles == {"PC Only"}


@pytest.mark.django_db
def test_genre_filter_limits_results() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    shooter = _genre("Shooter", 5)
    _work("Big RPG", year=2015, genres=(rpg,))
    _work("Loud Shooter", year=2016, genres=(shooter,))

    result = search_games(cq=parse_catalogue_query({"genre": "shooter"}))
    assert {w.original_title for w in result["results"]} == {"Loud Shooter"}


@pytest.mark.django_db
def test_year_and_rating_filters_intersect() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Old Great", year=1999, rating=95.0, platforms=("PC",), genres=(rpg,))
    _work("New Great", year=2020, rating=92.0, platforms=("PC",), genres=(rpg,))
    _work("New Weak", year=2021, rating=40.0, platforms=("PC",), genres=(rpg,))

    cq = parse_catalogue_query(
        {"platform": "pc", "genre": "role-playing-rpg", "year_from": "2010", "min_rating": "80"}
    )
    result = search_games(cq=cq)
    assert {w.original_title for w in result["results"]} == {"New Great"}


@pytest.mark.django_db
def test_dlc_is_excluded_even_when_filters_match() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Base RPG", year=2015, rating=90.0, platforms=("PC",), genres=(rpg,))
    _work("Base RPG Season Pass", is_dlc=True, year=2015, rating=90.0, platforms=("PC",), genres=(rpg,))

    result = search_games(cq=parse_catalogue_query({"platform": "pc", "genre": "role-playing-rpg"}))
    assert {w.original_title for w in result["results"]} == {"Base RPG"}


@pytest.mark.django_db
def test_every_sort_key_is_deterministic_with_canonical_slug_tiebreak() -> None:
    # Two works share a title and a rating and a year -> only canonical_slug
    # can break the tie, and it must do so identically on every call.
    a = _work("Tie Game", year=2010, rating=80.0)
    b = _work("Tie Game 2", year=2010, rating=80.0)
    _work("Zzz Late", year=2001, rating=10.0)
    _work("Aaa Early", year=2022, rating=99.0)

    for key in SORT_ORDERS:
        first = [w.id for w in search_games(cq=CatalogueQuery(sort=key))["results"]]
        second = [w.id for w in search_games(cq=CatalogueQuery(sort=key))["results"]]
        assert first == second, key
        assert set([a.id, b.id]).issubset(set(first))

    ascending = [w.original_title for w in search_games(cq=CatalogueQuery(sort="title_asc"))["results"]]
    assert ascending == sorted(ascending)
    descending = [w.original_title for w in search_games(cq=CatalogueQuery(sort="title_desc"))["results"]]
    assert descending == sorted(descending, reverse=True)


@pytest.mark.django_db
def test_release_sort_orders_by_year() -> None:
    _work("Middle", year=2010)
    _work("Newest", year=2024)
    _work("Oldest", year=1990)

    newest = [w.original_title for w in search_games(cq=CatalogueQuery(sort="release_newest"))["results"]]
    assert newest[:3] == ["Newest", "Middle", "Oldest"]
    oldest = [w.original_title for w in search_games(cq=CatalogueQuery(sort="release_oldest"))["results"]]
    assert oldest[:3] == ["Oldest", "Middle", "Newest"]


@pytest.mark.django_db
def test_rating_sort_orders_high_to_low_nulls_last() -> None:
    _work("Unrated", year=2010, rating=None)
    _work("Mediocre", year=2010, rating=55.0)
    _work("Acclaimed", year=2010, rating=97.0)

    ranked = [w.original_title for w in search_games(cq=CatalogueQuery(sort="rating_desc"))["results"]]
    assert ranked[0] == "Acclaimed"
    assert ranked[1] == "Mediocre"
    assert ranked[-1] == "Unrated"


@pytest.mark.django_db
def test_response_includes_facets_with_counts_and_year_range() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    shooter = _genre("Shooter", 5)
    _work("A", year=2001, platforms=("PC",), genres=(rpg,))
    _work("B", year=2019, platforms=("PC", "PlayStation 5"), genres=(rpg, shooter))

    client = APIClient()
    body = client.get("/api/catalogue/games/").json()
    facets = body["facets"]

    platform_counts = {p["slug"]: p["count"] for p in facets["platforms"]}
    assert platform_counts["pc"] == 2
    assert platform_counts["playstation-5"] == 1
    genre_counts = {g["slug"]: g["count"] for g in facets["genres"]}
    assert genre_counts["role-playing-rpg"] == 2
    assert genre_counts["shooter"] == 1
    assert facets["year_range"] == {"min": 2001, "max": 2019}


@pytest.mark.django_db
def test_list_endpoint_has_no_n_plus_one_and_is_query_bounded(
    django_assert_max_num_queries: object,
) -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    for i in range(25):
        _work(f"Bulk Game {i:02d}", year=2000 + i, rating=50.0 + i, platforms=("PC", "Switch"), genres=(rpg,))

    client = APIClient()
    # A full page of 24 cards, each with genres + releases + cover, must not
    # scale the query count with the row count.
    with django_assert_max_num_queries(18):  # type: ignore[operator]
        response = client.get("/api/catalogue/games/", {"sort": "rating_desc"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 24


@pytest.mark.django_db
def test_serializer_exposes_total_rating_and_genres() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Rated RPG", year=2015, rating=88.5, genres=(rpg,))

    client = APIClient()
    card = client.get("/api/catalogue/games/", {"q": "Rated"}).json()["results"][0]
    assert card["total_rating"] == 88.5
    assert card["genres"] == [{"slug": "role-playing-rpg", "name": "Role-playing (RPG)"}]


@pytest.mark.django_db
def test_filtered_view_is_url_reproducible() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    for i in range(5):
        _work(f"Repeatable {i}", year=2005 + i, rating=70.0 + i, platforms=("PC",), genres=(rpg,))

    params = {"platform": "pc", "genre": "role-playing-rpg", "sort": "rating_desc", "min_rating": "70"}
    client = APIClient()
    first = client.get("/api/catalogue/games/", params).json()
    second = client.get("/api/catalogue/games/", params).json()
    assert [r["id"] for r in first["results"]] == [r["id"] for r in second["results"]]
    assert first["count"] == second["count"] == 5
    assert first["sort"] == "rating_desc"


@pytest.mark.django_db
def test_text_query_and_filters_compose() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Dragon Quest XI", year=2017, platforms=("PC",), genres=(rpg,))
    _work("Dragon Quest Builders", year=2016, platforms=("Switch",), genres=(rpg,))

    cq = parse_catalogue_query({"q": "Dragon Quest", "platform": "pc"})
    result = search_games(cq.q, cq=cq)
    assert {w.original_title for w in result["results"]} == {"Dragon Quest XI"}


@pytest.mark.django_db
def test_unknown_platform_or_genre_slug_is_ignored_not_500() -> None:
    _work("Present Game", year=2011, platforms=("PC",))
    result = search_games(cq=parse_catalogue_query({"platform": "does-not-exist"}))
    # Unknown facet value -> filter dropped, catalogue still returned (UI-SPEC).
    assert {w.original_title for w in result["results"]} == {"Present Game"}
