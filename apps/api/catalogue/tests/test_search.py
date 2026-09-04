"""Tests for tolerant catalogue search (Plan 01-06 Task 2, CAT-01/CAT-06)."""

from __future__ import annotations

import socket
from datetime import date

import pytest
from rest_framework.test import APIClient

from catalogue.models import GameAlias, GameRelease, GameWork, Platform, SourceRecord
from catalogue.normalization import normalize_title
from catalogue.search import search_games


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
