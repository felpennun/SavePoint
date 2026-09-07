"""Live product "display" rating (D-09).

The number a visitor sees on a card / detail page is a *product* value,
computed at read time: a confidence-weighted blend of the IGDB user rating
and the mean of SavePoint ``LibraryEntry.rating_half_steps`` (x10) for the
same restricted account set that ``rank_popularity_v1`` uses.

It is deliberately kept separate from the frozen research observation in
``CorpusRatingSnapshot`` (external-only, immutable per ``corpus_version``):
nothing in this module ever reads or writes a snapshot row. ``rating_breakdown``
exposes only aggregate counts -- never which specific users rated a work.
"""

from __future__ import annotations

from django.db.models import Avg, Count, Q

from catalogue.models import GameWork
from library.models import LibraryEntry

# Same anti-contamination account set as ``rank_popularity_v1``
# (library/popularity.py:44-49): a seeded ``demo_anchor`` or a bootstrapped
# ``demo_identity``. A self-registered visitor has neither, so their private
# ratings never move this public product number.
_REAL_ACCOUNT = Q(user__demo_anchor__isnull=False) | Q(user__demo_identity__isnull=False)

# Confidence ceiling: past this many ratings a source is treated as
# fully confident, so neither a huge IGDB sample nor a large local cohort can
# unboundedly swamp the other side of the blend.
_CONFIDENCE_CAP = 50


def _counted_savepoint_entries(work: GameWork):
    """The SavePoint rating rows that count toward the live number: rated,
    and from a demo/simulated account only."""
    return LibraryEntry.objects.filter(
        _REAL_ACCOUNT, work=work, rating_half_steps__isnull=False
    )


def _savepoint_mean_and_count(work: GameWork) -> tuple[float | None, int]:
    agg = _counted_savepoint_entries(work).aggregate(
        mean=Avg("rating_half_steps"), n=Count("id")
    )
    return _scale(agg["mean"], agg["n"] or 0)


def _scale(mean: float | None, n: int) -> tuple[float | None, int]:
    if n == 0 or mean is None:
        return None, 0
    # half-steps are 1..10; x10 lifts the mean onto the same 0-100 scale as
    # the external rating.
    return float(mean) * 10.0, n


def savepoint_rating_stats(work_ids: object) -> dict[object, tuple[float | None, int]]:
    """Bulk ``{work_id: (local_mean_x10, count)}`` for a page of works -- one
    query for the whole list, so a card list never scales queries with rows.
    Callers pass the result into the serializer context; ``display_rating``
    falls back to a per-work query when no stats map is supplied."""

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


def _confidence_weight(n: int) -> int:
    return min(max(n, 1), _CONFIDENCE_CAP)


def display_rating(
    work: GameWork,
    savepoint_stats: tuple[float | None, int] | None = None,
) -> float | None:
    """The 0-100 product rating for ``work``, or ``None`` when no source has a
    value (the caller renders "sin valoración" and the work drops out of
    rating sort / ``min_rating``, D-07).

    ``savepoint_stats`` is an optional pre-computed ``(local_mean_x10, count)``
    from :func:`savepoint_rating_stats` -- supply it for list rendering to
    keep the query count flat; omit it and a per-work aggregate runs."""

    external_value = None if work.rating is None else float(work.rating)
    external_n = work.rating_count or 0
    local_value, local_n = (
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

    w_external = _confidence_weight(external_n)
    w_local = _confidence_weight(local_n)
    blended = (external_value * w_external + local_value * w_local) / (
        w_external + w_local
    )
    return round(blended, 2)


def rating_breakdown(work: GameWork) -> dict[str, int]:
    """Aggregate-only provenance for the detail-page breakdown line
    ("Basada en la valoración de N usuarios de IGDB y M de SavePoint").
    Never exposes individual rows (threat T-02-05-02)."""

    igdb_count = (work.rating_count or 0) if work.rating is not None else 0
    return {
        "igdb_count": igdb_count,
        "savepoint_count": _counted_savepoint_entries(work).count(),
    }
