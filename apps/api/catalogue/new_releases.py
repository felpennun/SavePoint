"""Materialised home "Novedades" shelf (D-24).

Ranking is ``0.70 * recency + 0.30 * PopScore`` over governed, non-DLC
works released in the last ~183 days. It is recomputed **only** when the
IGDB catalogue is (re-)imported -- never per request. Between imports the
release window and the PopScore inputs do not move, so every page load
serves the frozen ordered list in ``NewReleasesSnapshot``.
"""

from __future__ import annotations

from datetime import date, timedelta

from django.db import connection, transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from catalogue.corpus import governed_works
from catalogue.models import CorpusPopularityScore, CorpusVersion, NewReleasesSnapshot

# ~6 months, in days so the window is one indexed btree comparison on
# ``first_release_date`` (no calendar arithmetic per row).
NEW_RELEASE_WINDOW_DAYS = 183
NEW_RELEASE_LIMIT = 20
NEW_RELEASE_RECENCY_WEIGHT = 0.70
NEW_RELEASE_POPSCORE_WEIGHT = 0.30
NEW_RELEASE_FORMULA = "recency-0.70-popscore-0.30-v1"

# Transaction-scoped advisory lock serialising snapshot writes (auto-released
# at transaction end, like the other catalogue materialisers).
_MATERIALIZE_LOCK_KEY = 725_02_24


def ranked_new_release_work_ids(*, today: date | None = None) -> list[str]:
    """The ordered ``GameWork`` primary keys (as strings, for JSON storage)
    for the shelf, capped at ``NEW_RELEASE_LIMIT``. Recency-only order is
    the special case where no work in the window carries a PopScore."""
    today = today or date.today()
    cutoff = today - timedelta(days=NEW_RELEASE_WINDOW_DAYS)

    active_version = (
        CorpusVersion.objects.filter(is_active=True)
        .order_by("-created_at")
        .values("version")[:1]
    )
    popscore = (
        CorpusPopularityScore.objects.filter(
            work_id=OuterRef("pk"),
            corpus_version=Subquery(active_version),
        )
        .values("score")[:1]
    )
    window = (
        governed_works()
        .filter(first_release_date__gte=cutoff)
        .annotate(popscore=Subquery(popscore))
        .values_list("pk", "canonical_slug", "first_release_date", "popscore")
    )

    def blended(first_release_date: date, popscore: float | None) -> float:
        days_in = (first_release_date - cutoff).days
        recency = min(1.0, max(0.0, days_in / NEW_RELEASE_WINDOW_DAYS))
        pop = float(popscore) if popscore is not None else 0.0
        return (
            NEW_RELEASE_RECENCY_WEIGHT * recency
            + NEW_RELEASE_POPSCORE_WEIGHT * pop
        )

    ordered = sorted(
        window,
        key=lambda row: (-blended(row[2], row[3]), row[1]),
    )
    return [str(row[0]) for row in ordered[:NEW_RELEASE_LIMIT]]


def materialize_new_releases(*, today: date | None = None) -> NewReleasesSnapshot:
    """Recompute the shelf and upsert the singleton ``NewReleasesSnapshot``."""
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_MATERIALIZE_LOCK_KEY])
        work_ids = ranked_new_release_work_ids(today=today)
        snapshot, _ = NewReleasesSnapshot.objects.update_or_create(
            pk=NewReleasesSnapshot.SINGLETON_PK,
            defaults={
                "work_ids": work_ids,
                "formula": NEW_RELEASE_FORMULA,
                "computed_at": timezone.now(),
            },
        )
    return snapshot


def get_or_bootstrap_snapshot() -> NewReleasesSnapshot:
    """Return the materialised snapshot. If it is missing (first boot, or a
    fresh test database) it is computed once here; a subsequent request
    never recomputes -- only ``materialize_new_releases`` does."""
    snapshot = NewReleasesSnapshot.objects.filter(
        pk=NewReleasesSnapshot.SINGLETON_PK
    ).first()
    if snapshot is None:
        snapshot = materialize_new_releases()
    return snapshot
