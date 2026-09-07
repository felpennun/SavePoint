"""Tests for the live blended product rating (Plan 02-05 Task 3, D-09).

``display_rating`` is a read-time confidence-weighted blend of the IGDB user
rating and the mean of SavePoint ``LibraryEntry.rating_half_steps`` (x10)
restricted to the same account set as ``rank_popularity_v1``. It never reads
``CorpusRatingSnapshot`` (external-only, frozen per ``corpus_version``), and
``rating_breakdown`` exposes only aggregate counts -- never per-user rows
(threats T-02-05-02 / T-02-05-03).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import DemoAccountAnchor
from catalogue.models import CorpusRatingSnapshot, GameWork, SourceRecord
from catalogue.ratings import display_rating, rating_breakdown
from library.models import LibraryEntry

pytestmark = pytest.mark.django_db

User = get_user_model()


def _work(slug: str, *, rating: float | None = None, rating_count: int | None = None) -> GameWork:
    return GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug.replace("-", " ").title(),
        title_en=slug.replace("-", " ").title(),
        in_corpus=True,
        corpus_version="2026.09.1",
        rating=rating,
        rating_count=rating_count,
    )


def _demo_user(username: str) -> User:
    """A seeded demo account -- the only kind whose ratings feed the live
    product number (mirrors ``rank_popularity_v1``'s restriction)."""
    user = User.objects.create_user(username=username, password="Demo-Pass-9!x")
    DemoAccountAnchor.objects.create(user=user)
    return user


def _rate(user: User, work: GameWork, half_steps: int) -> None:
    LibraryEntry.objects.create(
        user=user, work=work, current_status="completed", rating_half_steps=half_steps
    )


# --------------------------------------------------------------------------- #
# display_rating                                                              #
# --------------------------------------------------------------------------- #
def test_external_only_returns_the_external_value() -> None:
    work = _work("ext-only", rating=75.0, rating_count=100)
    assert display_rating(work) == 75.0


def test_savepoint_only_returns_the_local_mean_times_ten() -> None:
    work = _work("local-only")
    _rate(_demo_user("d-local-1"), work, 7)  # 7 half-steps -> 70 on the 0-100 scale
    assert display_rating(work) == 70.0


def test_external_plus_savepoint_is_a_confidence_weighted_blend() -> None:
    work = _work("blended", rating=80.0, rating_count=3)  # external weight 3
    _rate(_demo_user("d-blend-1"), work, 10)  # local: mean 10 -> 100
    _rate(_demo_user("d-blend-2"), work, 10)  # local weight 2

    # (80*3 + 100*2) / 5 == 88.0, and always strictly between the two sources.
    assert display_rating(work) == 88.0
    assert 80.0 < display_rating(work) < 100.0


def test_no_source_with_data_returns_none() -> None:
    work = _work("no-rating")
    assert display_rating(work) is None
    assert rating_breakdown(work) == {"igdb_count": 0, "savepoint_count": 0}


def test_rating_from_a_non_restricted_account_does_not_move_the_number() -> None:
    work = _work("restricted-only")
    _rate(_demo_user("d-restricted-1"), work, 8)  # -> 80.0
    assert display_rating(work) == 80.0

    self_registered = User.objects.create_user(
        username="real-visitor-x", password="Real-Pass-9!x"
    )
    _rate(self_registered, work, 2)  # would drag a naive mean down to 50

    assert display_rating(work) == 80.0


def test_display_rating_never_reads_the_corpus_rating_snapshot() -> None:
    work = _work("snapshot-inert", rating=80.0, rating_count=10)
    SourceRecord.objects.create(
        work=work,
        source="igdb",
        source_id="snap-1",
        source_url="https://www.igdb.com/games/snapshot-inert",
        retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
        licence="IGDB",
        snapshot_sha256="a" * 64,
    )
    snapshot = CorpusRatingSnapshot.objects.create(
        work=work,
        corpus_version="2026.09.1",
        source="igdb",
        rating=1.0,  # deliberately nothing like the live value
        rating_count=999,
        retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )

    # The snapshot's 1.0 has no influence -- the live number is the external
    # value until a SavePoint rating arrives.
    assert display_rating(work) == 80.0

    _rate(_demo_user("d-snap-1"), work, 10)  # -> local 100, shifts the live number
    assert display_rating(work) != 80.0

    snapshot.refresh_from_db()
    assert snapshot.rating == 1.0
    assert snapshot.rating_count == 999


# --------------------------------------------------------------------------- #
# rating_breakdown -- aggregate counts only                                   #
# --------------------------------------------------------------------------- #
def test_rating_breakdown_reports_aggregate_counts_only() -> None:
    work = _work("breakdown", rating=90.0, rating_count=1234)
    _rate(_demo_user("d-bd-1"), work, 9)
    _rate(_demo_user("d-bd-2"), work, 8)
    self_registered = User.objects.create_user(
        username="real-visitor-bd", password="Real-Pass-9!x"
    )
    _rate(self_registered, work, 3)  # not counted -- non-restricted account

    breakdown = rating_breakdown(work)
    assert breakdown == {"igdb_count": 1234, "savepoint_count": 2}
    # Aggregate shape only -- no per-user keys leak through.
    assert set(breakdown.keys()) == {"igdb_count", "savepoint_count"}


def test_igdb_count_is_zero_when_there_is_no_external_rating() -> None:
    work = _work("no-ext", rating=None, rating_count=None)
    _rate(_demo_user("d-noext-1"), work, 6)
    assert rating_breakdown(work) == {"igdb_count": 0, "savepoint_count": 1}


# --------------------------------------------------------------------------- #
# Serializer wiring                                                           #
# --------------------------------------------------------------------------- #
def test_detail_endpoint_exposes_display_rating_and_breakdown() -> None:
    work = _work("wired-detail", rating=88.0, rating_count=50)
    SourceRecord.objects.create(
        work=work,
        source="igdb",
        source_id="wired-1",
        source_url="https://www.igdb.com/games/wired-detail",
        retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
        licence="IGDB",
        snapshot_sha256="c" * 64,
    )
    _rate(_demo_user("d-wired-1"), work, 10)

    body = APIClient().get("/api/catalogue/games/wired-detail/").json()
    assert body["display_rating"] == display_rating(work)
    assert body["rating_breakdown"] == {"igdb_count": 50, "savepoint_count": 1}
