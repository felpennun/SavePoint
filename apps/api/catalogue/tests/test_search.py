"""Tests for tolerant catalogue search (Plan 01-06 Task 2, CAT-01/CAT-06)
plus the CAT-02 filter/sort/facet contract (Plan 01.1-03 Task 1)."""

from __future__ import annotations

import socket
from datetime import date

import pytest
from django.http import QueryDict
from rest_framework.test import APIClient

from catalogue.models import (
    CorpusPopularityScore,
    CorpusVersion,
    CuratedLabel,
    Developer,
    Edition,
    Franchise,
    GameAlias,
    GameMode,
    GameRelease,
    GameWork,
    GameWorkCuratedLabel,
    Platform,
    Publisher,
    SourceRecord,
)
from catalogue.normalization import normalize_title
from catalogue.search import (
    SORT_ORDERS,
    CatalogueQuery,
    FilterValidationError,
    parse_catalogue_query,
    search_games,
)


def _make_work(
    title: str,
    *,
    is_dlc: bool = False,
    year: int | None = None,
    platform_name: str | None = None,
    in_corpus: bool = True,
) -> GameWork:
    slug = title.lower().replace(" ", "-").replace("'", "")
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=title,
        title_en=title,
        title_es="",
        is_dlc=is_dlc,
        in_corpus=in_corpus,
        total_rating_count=1000,
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
def test_catalogue_without_query_defaults_to_popscore() -> None:
    _make_work("Unrated Game")
    rated = _make_work("Highly Rated Game")
    rated.total_rating = 96.0
    rated.save(update_fields=["total_rating"])

    result = search_games()

    assert result["sort"] == "popscore_desc"
    assert [work.original_title for work in result["results"]] == [
        "Highly Rated Game",
        "Unrated Game",
    ]


@pytest.mark.django_db
def test_default_popscore_keeps_works_with_fewer_than_one_thousand_ratings() -> None:
    included = _make_work("Included Default Result")
    included.total_rating = 90.0
    included.save(update_fields=["total_rating"])
    excluded = _make_work("Excluded Small Sample")
    excluded.total_rating = 99.0
    excluded.total_rating_count = 999
    excluded.save(update_fields=["total_rating", "total_rating_count"])

    result = search_games()

    assert result["sort"] == "popscore_desc"
    assert [work.original_title for work in result["results"]] == [
        "Excluded Small Sample",
        "Included Default Result",
    ]


@pytest.mark.django_db
def test_relevance_uses_stepped_rating_count_tiers() -> None:
    expected = [
        ("Tier 1000", 1000, 60.0),
        ("Tier 500", 500, 99.0),
        ("Tier 200", 200, 98.0),
        ("Tier 100", 100, 97.0),
        ("Tier 50", 50, 96.0),
        ("Tier 10", 10, 95.0),
        ("Tier No Ratings", 0, 100.0),
        ("Tier Missing Count", None, 90.0),
    ]
    for title, rating_count, rating in expected:
        work = _make_work(title)
        work.total_rating = rating
        work.total_rating_count = rating_count
        work.save(update_fields=["total_rating", "total_rating_count"])

    result = search_games(cq=CatalogueQuery(sort="relevance"))

    assert [work.original_title for work in result["results"]] == [title for title, _, _ in expected]


@pytest.mark.django_db
def test_relevance_uses_rating_tier_before_score_for_search() -> None:
    low = _make_work("Elden Ring Low")
    low.total_rating = 60.0
    low.total_rating_count = 1000
    low.save(update_fields=["total_rating", "total_rating_count"])
    high = _make_work("Elden Ring High")
    high.total_rating = 95.0
    high.save(update_fields=["total_rating"])
    too_small = _make_work("Elden Ring Small")
    too_small.total_rating = 99.0
    too_small.total_rating_count = 999
    too_small.save(update_fields=["total_rating", "total_rating_count"])

    result = search_games(cq=CatalogueQuery(q="Elden Ring", sort="relevance"))

    assert result["sort"] == "relevance"
    assert [work.original_title for work in result["results"]] == [
        "Elden Ring High",
        "Elden Ring Low",
        "Elden Ring Small",
    ]


@pytest.mark.django_db
def test_default_catalogue_order_uses_active_popscore() -> None:
    low = _make_work("Low PopScore")
    high = _make_work("High PopScore")
    CorpusVersion.objects.create(
        version="catalogue-v1",
        ruleset_sha256="1" * 64,
        is_active=True,
    )
    calculated_at = "2026-09-09T00:00:00Z"
    for work, score in ((low, 0.15), (high, 0.85)):
        CorpusPopularityScore.objects.create(
            work=work,
            corpus_version="catalogue-v1",
            score=score,
            formula_version="igdb-engagement-weighted-v2",
            calculated_at=calculated_at,
            source_snapshot_sha256="2" * 64,
        )

    result = search_games()

    assert result["sort"] == "popscore_desc"
    assert [work.original_title for work in result["results"][:2]] == [
        "High PopScore",
        "Low PopScore",
    ]


@pytest.mark.django_db
def test_dlc_excluded_from_search_results() -> None:
    _make_work("Base Game")
    _make_work("Base Game Season Pass", is_dlc=True)
    result = search_games("Base Game")
    titles = [w.original_title for w in result["results"]]
    assert "Base Game Season Pass" not in titles


@pytest.mark.django_db
def test_pagination_defaults_to_25_per_page() -> None:
    # 25 is a multiple of the catalogue grid's 5 columns (2026-09-12): a full
    # page always fills complete rows instead of leaving the last one short.
    for i in range(30):
        _make_work(f"Game {i:02d}")
    result = search_games(None, page=1)
    assert result["page_size"] == 25
    assert len(result["results"]) == 25
    assert result["has_next"] is True

    result_page_2 = search_games(None, page=2)
    assert len(result_page_2["results"]) == 5
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


def _genre(name: str, igdb_id: int) -> CuratedLabel:  # noqa: ARG001 -- igdb_id kept for call-site continuity
    from django.utils.text import slugify

    return CuratedLabel.objects.create(
        name=name, slug=slugify(name), kind=CuratedLabel.Kind.GENRE, curation_version="test"
    )


def _work(
    title: str,
    *,
    is_dlc: bool = False,
    year: int | None = None,
    rating: float | None = None,
    platforms: tuple[str, ...] = (),
    genres: tuple[CuratedLabel, ...] = (),
    in_corpus: bool = True,
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
        total_rating_count=1000,
        in_corpus=in_corpus,
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
    for tag in genres:
        GameWorkCuratedLabel.objects.create(work=work, label=tag, source_kind="genre", source_value=tag.name)
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

    result = search_games(cq=parse_catalogue_query({"tag": "shooter"}))
    assert {w.original_title for w in result["results"]} == {"Loud Shooter"}


@pytest.mark.django_db
def test_year_and_rating_filters_intersect() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Old Great", year=1999, rating=95.0, platforms=("PC",), genres=(rpg,))
    _work("New Great", year=2020, rating=92.0, platforms=("PC",), genres=(rpg,))
    _work("New Weak", year=2021, rating=40.0, platforms=("PC",), genres=(rpg,))

    cq = parse_catalogue_query(
        {"platform": "pc", "tag": "role-playing-rpg", "year_from": "2010", "min_rating": "80"}
    )
    result = search_games(cq=cq)
    assert {w.original_title for w in result["results"]} == {"New Great"}


@pytest.mark.django_db
def test_dlc_is_excluded_even_when_filters_match() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Base RPG", year=2015, rating=90.0, platforms=("PC",), genres=(rpg,))
    _work("Base RPG Season Pass", is_dlc=True, year=2015, rating=90.0, platforms=("PC",), genres=(rpg,))

    result = search_games(cq=parse_catalogue_query({"platform": "pc", "tag": "role-playing-rpg"}))
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
    assert platform_counts["playstation-5"] == 1
    assert "pc" not in platform_counts
    genre_counts = {g["slug"]: g["count"] for g in facets["tags"]}
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
    # A full page of 25 cards, each with tags + releases + cover, must not
    # scale the query count with the row count.
    with django_assert_max_num_queries(18):  # type: ignore[operator]
        response = client.get("/api/catalogue/games/", {"sort": "rating_desc"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 25


@pytest.mark.django_db
def test_serializer_exposes_total_rating_and_genres() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Rated RPG", year=2015, rating=88.5, genres=(rpg,))

    client = APIClient()
    card = client.get("/api/catalogue/games/", {"q": "Rated"}).json()["results"][0]
    assert card["total_rating"] == 88.5
    assert card["total_rating_count"] == 1000
    assert card["tags"] == [{"slug": "role-playing-rpg", "name": "Role-playing (RPG)"}]


@pytest.mark.django_db
def test_filtered_view_is_url_reproducible() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    for i in range(5):
        _work(f"Repeatable {i}", year=2005 + i, rating=70.0 + i, platforms=("PC",), genres=(rpg,))

    params = {"platform": "pc", "tag": "role-playing-rpg", "sort": "rating_desc", "min_rating": "70"}
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


# ---------------------------------------------------------------------------
# Plan 02-03 Task 2 -- multi-select filters + governed-corpus scoping (CAT-02)
# ---------------------------------------------------------------------------


def _qd(**lists: list[str]) -> QueryDict:
    qd = QueryDict(mutable=True)
    for key, values in lists.items():
        qd.setlist(key, values)
    return qd


@pytest.mark.django_db
def test_parse_reads_all_repeated_genre_and_platform_values() -> None:
    cq = parse_catalogue_query(
        _qd(tag=["rpg", "strategy"], platform=["switch", "pc-microsoft-windows"])
    )
    assert cq.tags == ("rpg", "strategy")
    assert cq.platforms == ("switch", "pc-microsoft-windows")


@pytest.mark.django_db
def test_parse_dedupes_and_drops_blank_repeated_values() -> None:
    cq = parse_catalogue_query(_qd(tag=["rpg", "", "rpg", " strategy ", "strategy"]))
    assert cq.tags == ("rpg", "strategy")
    assert cq.platforms == ()


@pytest.mark.django_db
def test_parse_rejects_more_than_twenty_repeated_facet_values() -> None:
    with pytest.raises(FilterValidationError):
        parse_catalogue_query(_qd(tag=[f"g{i}" for i in range(21)]))
    with pytest.raises(FilterValidationError):
        parse_catalogue_query(_qd(platform=[f"p{i}" for i in range(21)]))


@pytest.mark.django_db
def test_single_value_dict_params_still_supported() -> None:
    cq = parse_catalogue_query({"tag": "role-playing-rpg", "platform": "pc"})
    assert cq.tags == ("role-playing-rpg",)
    assert cq.platforms == ("pc",)


@pytest.mark.django_db
def test_multiple_genres_are_ANDed_without_join_duplicates() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    strategy = _genre("Strategy", 15)
    shooter = _genre("Shooter", 5)
    _work("Triple Genre", year=2015, genres=(rpg, strategy, shooter))
    _work("Only RPG", year=2016, genres=(rpg,))

    cq = parse_catalogue_query(_qd(tag=["role-playing-rpg", "strategy"]))
    result = search_games(cq=cq)

    assert [w.original_title for w in result["results"]] == ["Triple Genre"]
    assert result["count"] == 1


@pytest.mark.django_db
def test_multiple_platforms_are_ORed() -> None:
    _work("On Switch", year=2015, platforms=("Switch",))
    _work("On PC", year=2016, platforms=("PC",))
    _work("On PS5", year=2017, platforms=("PlayStation 5",))

    cq = parse_catalogue_query(_qd(platform=["switch", "pc"]))
    result = search_games(cq=cq)

    assert {w.original_title for w in result["results"]} == {"On Switch", "On PC"}


@pytest.mark.django_db
def test_unknown_repeated_slug_is_dropped_not_emptying() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Present", year=2011, platforms=("PC",), genres=(rpg,))

    cq = parse_catalogue_query(
        _qd(tag=["role-playing-rpg", "does-not-exist"], platform=["pc", "nope"])
    )
    assert {w.original_title for w in search_games(cq=cq)["results"]} == {"Present"}


@pytest.mark.django_db
def test_min_rating_remains_single_valued() -> None:
    cq = parse_catalogue_query({"min_rating": "80"})
    assert cq.min_rating == 80.0
    _work("High", year=2015, rating=90.0)
    _work("Low", year=2015, rating=40.0)

    result = search_games(cq=parse_catalogue_query({"min_rating": "80"}))
    assert {w.original_title for w in result["results"]} == {"High"}


@pytest.mark.django_db
def test_non_governed_work_hidden_from_list_search_and_facets() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    _work("Governed Game", year=2015, platforms=("PC",), genres=(rpg,))
    _work("Excluded Game", year=2016, platforms=("PC",), genres=(rpg,), in_corpus=False)

    listing = search_games()
    assert {w.original_title for w in listing["results"]} == {"Governed Game"}
    assert listing["count"] == 1

    assert search_games("Excluded Game")["results"] == []

    genre_counts = {g["slug"]: g["count"] for g in listing["facets"]["tags"]}
    assert genre_counts["role-playing-rpg"] == 1


@pytest.mark.django_db
def test_facets_exclude_non_allowlisted_platforms_on_governed_works() -> None:
    rpg = _genre("Role-playing (RPG)", 12)
    work = _work("Multi-platform Game", year=2015, platforms=("PC",), genres=(rpg,))
    allowed, _ = Platform.objects.get_or_create(
        slug="pc-microsoft-windows",
        defaults={"name": "PC (Microsoft Windows)"},
    )
    GameRelease.objects.create(
        work=work,
        platform=allowed,
        release_name="Multi-platform Game (Windows)",
        release_date=date(2015, 1, 1),
    )

    platform_slugs = {item["slug"] for item in search_games()["facets"]["platforms"]}
    assert "pc-microsoft-windows" in platform_slugs
    assert "pc" not in platform_slugs


@pytest.mark.django_db
def test_endpoint_rejects_more_than_twenty_repeated_values_with_bounded_400() -> None:
    client = APIClient()
    response = client.get(
        "/api/catalogue/games/", {"tag": [f"g{i}" for i in range(21)]}
    )
    assert response.status_code == 400
    assert "results" not in response.json()


# ---------------------------------------------------------------------------
# Phase 06 Plan 02 -- complete CAT-05 discovery contract
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cat05_query_and_facets_cover_every_catalogue_dimension() -> None:
    genre = Genre.objects.create(igdb_id=501, name="Role Playing", slug="role-playing")
    franchise = Franchise.objects.create(igdb_id=502, name="Signal Saga", slug="signal-saga")
    developer = Developer.objects.create(
        igdb_id=503, name="Signal Studio", slug="signal-studio"
    )
    publisher = Publisher.objects.create(
        igdb_id=504, name="Signal Publishing", slug="signal-publishing"
    )
    mode = GameMode.objects.create(igdb_id=505, name="Single Player", slug="single-player")
    tag = _genre("Curated Signal", 506)
    work = _work("Signal Edition Quest", year=2022, platforms=("PC",), in_corpus=True)
    work.genres.add(genre)
    work.franchises.add(franchise)
    work.developers.add(developer)
    work.publishers.add(publisher)
    work.game_modes.add(mode)
    GameWorkCuratedLabel.objects.create(
        work=work, label=tag, source_kind="genre", source_value=tag.name
    )
    release = work.releases.get()
    Edition.objects.create(release=release, name="Deluxe Edition")

    query = {
        "platform": "pc",
        "edition": "deluxe-edition",
        "genre": "role-playing",
        "franchise": "signal-saga",
        "developer": "signal-studio",
        "publisher": "signal-publishing",
        "year_from": "2022",
        "year_to": "2022",
        "mode": "single-player",
        "tag": "curated-signal",
        "sort": "title_asc",
    }
    result = search_games(cq=parse_catalogue_query(query))

    assert [item.original_title for item in result["results"]] == ["Signal Edition Quest"]
    assert {item["slug"] for item in result["facets"]["editions"]} == {"deluxe-edition"}
    assert {item["slug"] for item in result["facets"]["genres"]} == {"role-playing"}
    assert {item["slug"] for item in result["facets"]["franchises"]} == {"signal-saga"}
    assert {item["slug"] for item in result["facets"]["developers"]} == {"signal-studio"}
    assert {item["slug"] for item in result["facets"]["publishers"]} == {"signal-publishing"}
    assert {item["slug"] for item in result["facets"]["modes"]} == {"single-player"}
    assert {item["slug"] for item in result["facets"]["tags"]} >= {"curated-signal"}
    assert result["facets"]["dates"] == [{"value": "2022", "label": "2022", "count": 1}]


@pytest.mark.django_db
def test_cat05_repeated_filters_pagination_and_sort_are_reproducible() -> None:
    genre = Genre.objects.create(igdb_id=601, name="Puzzle", slug="puzzle")
    for index in range(3):
        work = _work(f"Repeatable Edition {index}", year=2020 + index, platforms=("PC",))
        work.genres.add(genre)
        release = work.releases.get()
        Edition.objects.create(release=release, name="Standard")

    params = _qd(genre=["puzzle", "puzzle"], platform=["pc", "pc"], edition=["standard"])
    params["sort"] = "title_desc"
    first = search_games(cq=parse_catalogue_query(params), page=1, page_size=2)
    second = search_games(cq=parse_catalogue_query(params), page=1, page_size=2)

    assert [item.id for item in first["results"]] == [item.id for item in second["results"]]
    assert first["count"] == second["count"] == 3
    assert first["has_next"] is True


@pytest.mark.django_db
def test_cat05_invalid_bounds_fail_before_orm_and_unknown_slugs_are_ignored() -> None:
    _work("Known Local Work", year=2020, platforms=("PC",))
    with pytest.raises(FilterValidationError):
        parse_catalogue_query({"sort": "release_newest; DROP TABLE catalogue_gamework"})
    with pytest.raises(FilterValidationError):
        parse_catalogue_query({"date_from": "not-a-date"})

    client = APIClient()
    response = client.get(
        "/api/catalogue/games/",
        {"publisher": "does-not-exist", "edition": "does-not-exist"},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
