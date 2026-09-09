"""Deterministic calendar-year novelty signal for recent releases."""

from __future__ import annotations

from datetime import date


DEFAULT_YEAR_DECAY = 0.35


def recency_score(
    release_date: date | None,
    *,
    eligibility_cutoff_date: date,
    has_external_rating: bool,
    year_decay: float = DEFAULT_YEAR_DECAY,
) -> float | None:
    """Return a bounded calendar-year score or ``None`` when unavailable.

    Only already-released games with an observed external rating are eligible
    for the product novelty signal. A missing date is not interpreted as an
    old release, and a future release is never eligible. Every release in the
    cutoff year scores ``1.0``; each previous calendar year is multiplied by
    ``year_decay``. This makes the current year and the previous year explicit
    novelty buckets rather than allowing a long-tailed day-level half-life to
    keep very old works competitive.
    """

    if (
        release_date is None
        or release_date > eligibility_cutoff_date
        or not has_external_rating
        or not 0.0 < year_decay <= 1.0
    ):
        return None
    year_gap = max(0, eligibility_cutoff_date.year - release_date.year)
    return year_decay**year_gap
