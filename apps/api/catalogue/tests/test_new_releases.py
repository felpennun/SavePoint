"""Tests for the expanded catalogue detail serializer and the ``NewReleasesView``
shelf endpoint (Plan 02-05 Task 1, DATA-05 / QUAL-05 / D-24).

The detail serializer must carry the IGDB ``summary`` and the IGDB *user*
rating (``rating`` / ``rating_count``) plus provenance ``retrieved_at`` /
``source``. ``GET /api/catalogue/new-releases/`` returns up to 20 governed
works released in the last ~6 months, ranked by ``0.70 * recency +
0.30 * PopScore`` with ``canonical_slug`` as the tie-break; an empty window
is ``[]`` with 200, never an error, and a work outside the governed corpus
never appears.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from rest_framework.test import APIClient

from catalogue.models import (
    CorpusPopularityScore,
    CorpusVersion,
    GameWork,
    SourceRecord,
)

pytestmark = pytest.mark.django_db

_TODAY = date.today()
_RECENT = _TODAY - timedelta(days=30)
_OLD = _TODAY - timedelta(days=400)


def _governed_work(
    slug: str,
    *,
    first_release_date: date | None,
    in_corpus: bool = True,
    is_dlc: bool = False,
    summary: str = "",
    rating: float | None = None,
    rating_count: int | None = None,
) -> GameWork:
    return GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        title_en=slug.replace("-", " ").title(),
        first_release_date=first_release_date,
        in_corpus=in_corpus,
        corpus_version="2026.09.1" if in_corpus else "",
        is_dlc=is_dlc,
        summary=summary,
        rating=rating,
        rating_count=rating_count,
    )


def _igdb_source(work: GameWork, source_id: str) -> SourceRecord:
    return SourceRecord.objects.create(
        work=work,
        source="igdb",
        source_id=source_id,
        source_url=f"https://www.igdb.com/games/{work.canonical_slug}",
        retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
        licence="IGDB",
        snapshot_sha256="a" * 64,
    )


# --------------------------------------------------------------------------- #
# Detail serializer: summary + IGDB user rating + provenance                  #
# --------------------------------------------------------------------------- #
def test_detail_exposes_summary_rating_and_provenance_fields() -> None:
    work = _governed_work(
        "synopsis-game",
        first_release_date=_RECENT,
        summary="A sprawling tactical RPG about logistics.",
        rating=84.5,
        rating_count=1200,
    )
    _igdb_source(work, "42")

    body = APIClient().get("/api/catalogue/games/synopsis-game/").json()

    assert body["summary"] == "A sprawling tactical RPG about logistics."
    assert body["rating"] == 84.5
    assert body["rating_count"] == 1200
    assert body["provenance"]["source"] == "igdb"
    assert body["provenance"]["retrieved_at"].startswith("2026-09-07")


def test_detail_summary_is_empty_string_when_igdb_has_none() -> None:
    work = _governed_work("no-synopsis-game", first_release_date=_RECENT)
    _igdb_source(work, "43")

    body = APIClient().get("/api/catalogue/games/no-synopsis-game/").json()

    assert body["summary"] == ""
    assert body["rating"] is None
    assert body["rating_count"] is None


def test_detail_prefers_the_igdb_source_record_for_provenance() -> None:
    work = _governed_work("multi-source-game", first_release_date=_RECENT)
    SourceRecord.objects.create(
        work=work,
        source="wikidata",
        source_id="Q9",
        source_url="https://www.wikidata.org/wiki/Q9",
        retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        licence="CC0 1.0",
        snapshot_sha256="b" * 64,
    )
    _igdb_source(work, "44")

    body = APIClient().get("/api/catalogue/games/multi-source-game/").json()
    assert body["provenance"]["source"] == "igdb"


# --------------------------------------------------------------------------- #
# Card serializer: display rating number, explicit "no rating"               #
# --------------------------------------------------------------------------- #
def test_card_exposes_display_rating_number_and_null_when_absent() -> None:
    rated = _governed_work(
        "rated-card", first_release_date=_RECENT, rating=90.0, rating_count=10
    )
    _igdb_source(rated, "45")
    unrated = _governed_work("unrated-card", first_release_date=_RECENT)
    _igdb_source(unrated, "46")

    body = APIClient().get("/api/catalogue/new-releases/").json()
    by_slug = {row["slug"]: row for row in body}

    assert by_slug["rated-card"]["display_rating"] == 90.0
    assert by_slug["unrated-card"]["display_rating"] is None


# --------------------------------------------------------------------------- #
# NewReleasesView                                                             #
# --------------------------------------------------------------------------- #
def test_new_releases_returns_recent_governed_works_only() -> None:
    recent = _governed_work("recent-governed", first_release_date=_RECENT)
    _igdb_source(recent, "1")
    ungoverned = _governed_work(
        "recent-ungoverned", first_release_date=_RECENT, in_corpus=False
    )
    _igdb_source(ungoverned, "2")
    old = _governed_work("old-governed", first_release_date=_OLD)
    _igdb_source(old, "3")

    response = APIClient().get("/api/catalogue/new-releases/")
    assert response.status_code == 200
    slugs = [row["slug"] for row in response.json()]

    assert "recent-governed" in slugs
    assert "recent-ungoverned" not in slugs
    assert "old-governed" not in slugs


def test_new_releases_excludes_dlc_even_if_recent_and_in_corpus() -> None:
    dlc = _governed_work(
        "recent-dlc", first_release_date=_RECENT, is_dlc=True
    )
    _igdb_source(dlc, "4")

    body = APIClient().get("/api/catalogue/new-releases/").json()
    assert "recent-dlc" not in [row["slug"] for row in body]


def test_new_releases_orders_by_release_date_desc_then_canonical_slug() -> None:
    older = _governed_work(
        "z-older", first_release_date=_TODAY - timedelta(days=90)
    )
    _igdb_source(older, "5")
    newer_b = _governed_work("b-newer", first_release_date=_TODAY - timedelta(days=2))
    _igdb_source(newer_b, "6")
    newer_a = _governed_work("a-newer", first_release_date=_TODAY - timedelta(days=2))
    _igdb_source(newer_a, "7")

    body = APIClient().get("/api/catalogue/new-releases/").json()
    slugs = [row["slug"] for row in body]

    assert slugs.index("a-newer") < slugs.index("b-newer") < slugs.index("z-older")


def test_new_releases_blends_recency_with_popscore() -> None:
    """A somewhat older but highly popular release outranks a fresher one
    with no engagement signal: the ranking is 0.70 recency + 0.30 PopScore,
    not recency alone."""
    CorpusVersion.objects.create(
        version="2026.09.1", ruleset_sha256="c" * 64, is_active=True
    )
    fresh = _governed_work(
        "fresh-unknown", first_release_date=_TODAY - timedelta(days=30)
    )
    _igdb_source(fresh, "20")
    popular = _governed_work(
        "old-but-popular", first_release_date=_TODAY - timedelta(days=45)
    )
    _igdb_source(popular, "21")
    CorpusPopularityScore.objects.create(
        work=popular,
        corpus_version="2026.09.1",
        score=1.0,
        formula_version="igdb-engagement-weighted-v2",
        calculated_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        source_snapshot_sha256="d" * 64,
    )

    slugs = [row["slug"] for row in APIClient().get("/api/catalogue/new-releases/").json()]
    assert slugs.index("old-but-popular") < slugs.index("fresh-unknown")


def test_new_releases_empty_window_returns_empty_list_with_200() -> None:
    old = _governed_work("only-old", first_release_date=_OLD)
    _igdb_source(old, "8")

    response = APIClient().get("/api/catalogue/new-releases/")
    assert response.status_code == 200
    assert response.json() == []


def test_new_releases_caps_at_twenty_items() -> None:
    for index in range(25):
        work = _governed_work(
            f"cap-{index:02d}",
            first_release_date=_TODAY - timedelta(days=index + 1),
        )
        _igdb_source(work, f"cap-{index}")

    body = APIClient().get("/api/catalogue/new-releases/").json()
    assert len(body) == 20
