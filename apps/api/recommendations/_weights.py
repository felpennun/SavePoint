"""Shared library-activity weighting for every recommender in this app.

Promoted here from ``genre_heuristic.py`` (Plan 02-10) so the genre-taste
heuristic (REC-10), the content-based profile (``content/profile.py``, D-12),
and anything else that must speak the same "how much does this interaction
count" language import one definition instead of copying the table.

``genre_heuristic.py`` re-exports these names for backwards compatibility, so
``from recommendations.genre_heuristic import _entry_weight`` keeps working.
"""

from __future__ import annotations

# Mirrors ``library/popularity.py``'s status weighting so the personal
# heuristic, the public baseline, and the content profile all agree.
# ``abandoned`` contributes nothing: a bounced-off title is not evidence of
# taste.
_STATUS_WEIGHTS: dict[str, float] = {
    "completed": 3.0,
    "playing": 2.0,
    "pending": 1.0,
    "abandoned": 0.0,
}

# A rating adds ``rating_half_steps / 10`` (0.1 .. 1.0), identical to the
# popularity baseline's rating contribution.
_RATING_DIVISOR = 10


def _entry_weight(status: str | None, rating_half_steps: int | None) -> float:
    """Activity weight of one ``LibraryEntry`` from its status and rating."""

    return _STATUS_WEIGHTS.get(status or "", 0.0) + (rating_half_steps or 0) / _RATING_DIVISOR
