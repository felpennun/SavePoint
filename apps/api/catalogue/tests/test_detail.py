"""Tests for the game detail endpoint (Plan 01-06 Task 2, CAT-03/CAT-04)."""

from __future__ import annotations

from datetime import date

import pytest
from rest_framework.test import APIClient

from catalogue.models import AssetAttribution, Edition, GameRelease, GameWork, Platform, RelatedContent, SourceRecord


@pytest.mark.django_db
def test_detail_includes_hierarchy_and_provenance() -> None:
    work = GameWork.objects.create(
        canonical_slug="the-base-game",
        original_title="The Base Game",
        title_en="The Base Game",
        title_es="El Juego Base",
    )
    platform = Platform.objects.create(name="PC", slug="pc")
    release = GameRelease.objects.create(
        work=work, platform=platform, release_name="The Base Game (PC)", release_date=date(2020, 5, 1)
    )
    Edition.objects.create(release=release, name="Deluxe Edition")
    SourceRecord.objects.create(
        work=work,
        source="wikidata",
        source_id="Q1",
        source_url="https://www.wikidata.org/wiki/Q1",
        retrieved_at="2026-09-04T00:00:00Z",
        licence="CC0 1.0",
        snapshot_sha256="a" * 64,
    )

    client = APIClient()
    response = client.get("/api/catalogue/games/the-base-game/")
    assert response.status_code == 200
    body = response.json()

    assert body["title"] == "The Base Game"
    assert body["year"] == 2020
    assert len(body["releases"]) == 1
    assert body["releases"][0]["platform"] == "PC"
    assert body["releases"][0]["editions"] == ["Deluxe Edition"]

    provenance = body["provenance"]
    assert provenance["source"] == "wikidata"
    assert provenance["source_id"] == "Q1"
    assert provenance["licence"] == "CC0 1.0"
    assert provenance["snapshot_sha256"] == "a" * 64


@pytest.mark.django_db
def test_detail_shows_dlc_as_non_actionable_child_content() -> None:
    base = GameWork.objects.create(canonical_slug="base-game-2", original_title="Base Game 2")
    dlc = GameWork.objects.create(canonical_slug="base-game-2-dlc", original_title="Base Game 2: Expansion", is_dlc=True)
    RelatedContent.objects.create(parent_work=base, child_work=dlc, relation=RelatedContent.Relation.EXPANSION)
    SourceRecord.objects.create(
        work=base, source="wikidata", source_id="Q2", source_url="https://www.wikidata.org/wiki/Q2",
        retrieved_at="2026-09-04T00:00:00Z", licence="CC0 1.0", snapshot_sha256="b" * 64,
    )

    client = APIClient()
    response = client.get("/api/catalogue/games/base-game-2/")
    body = response.json()

    assert len(body["related_content"]) == 1
    related = body["related_content"][0]
    assert related["title"] == "Base Game 2: Expansion"
    assert related["relation"] == "expansion"
    # The related-content DTO carries identity only -- no status/rating/copy
    # fields that would make it independently actionable (D-11).
    assert set(related.keys()) == {"id", "slug", "title", "relation"}

    # The DLC itself is never surfaced as an independent catalogue result.
    assert "base-game-2-dlc" not in [w["slug"] for w in client.get("/api/catalogue/games/").json()["results"]]


@pytest.mark.django_db
def test_missing_game_returns_generic_404() -> None:
    client = APIClient()
    response = client.get("/api/catalogue/games/does-not-exist/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}


@pytest.mark.django_db
def test_cover_falls_back_to_placeholder_when_no_approved_asset() -> None:
    work = GameWork.objects.create(canonical_slug="no-cover-game", original_title="No Cover Game")
    AssetAttribution.objects.create(work=work, display_allowed=False, licence="", creator="")
    SourceRecord.objects.create(
        work=work, source="wikidata", source_id="Q3", source_url="https://www.wikidata.org/wiki/Q3",
        retrieved_at="2026-09-04T00:00:00Z", licence="CC0 1.0", snapshot_sha256="c" * 64,
    )

    client = APIClient()
    response = client.get("/api/catalogue/games/no-cover-game/")
    cover = response.json()["cover"]
    assert cover["is_placeholder"] is True
    assert cover["url"] is None


@pytest.mark.django_db
def test_cover_uses_approved_asset_with_attribution() -> None:
    work = GameWork.objects.create(canonical_slug="covered-game", original_title="Covered Game")
    AssetAttribution.objects.create(
        work=work,
        display_allowed=True,
        creator="Some Photographer",
        licence="CC BY-SA 3.0",
        licence_url="https://creativecommons.org/licenses/by-sa/3.0/",
        source_url="https://commons.wikimedia.org/wiki/File:Example.jpg",
        file_url="https://upload.wikimedia.org/wikipedia/commons/x/example.jpg",
    )
    SourceRecord.objects.create(
        work=work, source="wikidata", source_id="Q4", source_url="https://www.wikidata.org/wiki/Q4",
        retrieved_at="2026-09-04T00:00:00Z", licence="CC0 1.0", snapshot_sha256="d" * 64,
    )

    client = APIClient()
    response = client.get("/api/catalogue/games/covered-game/")
    cover = response.json()["cover"]
    assert cover["is_placeholder"] is False
    assert cover["attribution"]["creator"] == "Some Photographer"
    assert cover["attribution"]["licence"] == "CC BY-SA 3.0"
