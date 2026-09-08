"""Deterministic product-recency signal, separate from recommendation novelty."""

from __future__ import annotations

import math
from datetime import date


DEFAULT_HALF_LIFE_DAYS = 365


def recency_score(
    release_date: date | None,
    *,
    eligibility_cutoff_date: date,
    has_external_rating: bool,
    half_life_days: int = DEFAULT_HALF_LIFE_DAYS,
) -> float | None:
    """Return a bounded release-recency score or ``None`` when unavailable.

    Only already-released games with an observed external rating are eligible
    for the product novelty signal. A missing date is not interpreted as an
    old release, and a future release is never eligible.
    """

    if (
        release_date is None
        or release_date > eligibility_cutoff_date
        or not has_external_rating
        or half_life_days <= 0
    ):
        return None
    age_days = max(0, (eligibility_cutoff_date - release_date).days)
    return math.exp(-math.log(2) * age_days / half_life_days)
