"""Live product ``display`` rating (D-09).

The number a visitor sees on a card / detail page is a confidence-weighted
blend of the IGDB user rating and the mean of SavePoint ratings for the same
restricted account set used by the popularity ranker.

It is deliberately kept separate from the frozen research observation in
``CorpusRatingSnapshot``. ``rating_breakdown`` exposes only aggregate counts,
never which specific users rated a work.
"""

from __future__ import annotations

from django.db.models import Avg, Count, Q

from catalogue.models import GameWork
from library.models import LibraryEntry

# Same anti-contamination account set as ``rank_popularity_v1``.
_REAL_ACCOUNT = Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False)

# Confidence ceiling: past this many ratings a source is treated as fully
# confident, so neither source can unboundedly swamp the other side.
_CONFIDENCE_CAP = 50


def _counted_savepoint_entries(work: GameWork):
    """Rated SavePoint rows from demo/simulated accounts only."""
    return LibraryEntry.objects.filter(
        _REAL_ACCOUNT, work=work, rating_half_steps__isnull=False
    )


def _savepoint_mean_and_count(work: GameWork) -> tuple[float | None, int]:
    aggregate = _counted_savepoint_entries(work).aggregate(
        mean=Avg("rating_half_steps"), n=Count("id")
    )
    return _scale(aggregate["mean"], aggregate["n"] or 0)


def _scale(mean: float | None, count: int) -> tuple[float | None, int]:
    if count == 0 or mean is None:
        return None, 0
    return float(mean) * 10.0, count


def savepoint_rating_stats(work_ids: object) -> dict[object, tuple[float | None, int]]:
    """Bulk ``{work_id: (local_mean_x10, count)}`` for card-list rendering."""
    ids = list(work_ids)
    if not ids:
        return {}
    rows = (
        LibraryEntry.objects.filter(
            _REAL_ACCOUNT, work_id__in=ids, rating_half_steps__isnull=False
        )
        .values("work_id")
        .annotate(mean=Avg("rating_half_steps"), n=Count("id"))
    )
    return {row["work_id"]: _scale(row["mean"], row["n"]) for row in rows}


def _confidence_weight(count: int) -> int:
    return min(max(count, 1), _CONFIDENCE_CAP)


def display_rating(
    work: GameWork,
    savepoint_stats: tuple[float | None, int] | None = None,
) -> float | None:
    """Return the 0-100 blended product rating, or ``None`` without data."""
    external_value = None if work.rating is None else float(work.rating)
    external_count = work.rating_count or 0
    local_value, local_count = (
        _savepoint_mean_and_count(work)
        if savepoint_stats is None
        else savepoint_stats
    )

    if external_value is None and local_value is None:
        return None
    if local_value is None:
        return round(external_value, 2)
    if external_value is None:
        return round(local_value, 2)

    external_weight = _confidence_weight(external_count)
    local_weight = _confidence_weight(local_count)
    blended = (external_value * external_weight + local_value * local_weight) / (
        external_weight + local_weight
    )
    return round(blended, 2)


def rating_breakdown(work: GameWork) -> dict[str, int]:
    """Return aggregate-only IGDB and SavePoint counts."""
    igdb_count = (work.rating_count or 0) if work.rating is not None else 0
    return {
        "igdb_count": igdb_count,
        "savepoint_count": _counted_savepoint_entries(work).count(),
    }
