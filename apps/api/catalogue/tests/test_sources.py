"""Tests for the sources/provenance summary endpoint (Plan 01-09, DATA-02/D-08)."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from catalogue.models import AssetAttribution, GameWork, SourceRecord


@pytest.mark.django_db
def test_sources_returns_provenance_summary() -> None:
    work = GameWork.objects.create(canonical_slug="sources-game", original_title="Sources Game")
    SourceRecord.objects.create(
        work=work,
        source="wikidata",
        source_id="Q1",
        source_url="https://www.wikidata.org/wiki/Q1",
        retrieved_at="2026-09-04T00:00:00Z",
        licence="CC0 1.0",
        snapshot_sha256="a" * 64,
    )
    AssetAttribution.objects.create(work=work, display_allowed=True, licence="CC BY 2.0", creator="Someone")
    AssetAttribution.objects.create(work=work, display_allowed=False)

    client = APIClient()
    response = client.get("/api/catalogue/sources/")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "wikidata"
    assert body["licence"] == "CC0 1.0"
    assert body["snapshot_sha256"] == "a" * 64
    assert body["record_count"] == 1
    assert body["approved_asset_count"] == 1
    assert body["total_asset_candidate_count"] == 2


@pytest.mark.django_db
def test_sources_unavailable_when_no_data_imported() -> None:
    client = APIClient()
    response = client.get("/api/catalogue/sources/")
    assert response.status_code == 503
