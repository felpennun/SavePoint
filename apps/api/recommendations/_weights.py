"""Shared library-activity weighting for every recommender in this app.

Promoted here from ``genre_heuristic.py`` (Plan 02-10) so the genre-taste
heuristic (REC-10), the content-based profile (``content/profile.py``, D-12),
and anything else that must speak the same "how much does this interaction
count" language import one definition instead of copying the table.

``genre_heuristic.py`` re-exports these names for backwards compatibility, so
``from recommendations.genre_heuristic import _entry_weight`` keeps working.
"""

from __future__ import annotations

# Mirrors the activity weighting used by the personalised genre heuristic and
# the content profile. The public popularity baseline intentionally keeps its
# own non-personal aggregate formula and does not consume private ratings.
# ``abandoned`` contributes nothing: a bounced-off title is not evidence of
# taste.
_STATUS_WEIGHTS: dict[str, float] = {
    "completed": 3.0,
    "playing": 2.0,
    "pending": 1.0,
    "abandoned": 0.0,
}

# Personal ratings are deliberately nonlinear: a high rating is stronger
# evidence of positive taste than a merely positive rating. Half-steps are
# normalised to [0, 1] and squared before being added to the status weight.
_RATING_DIVISOR = 10
RATING_INTENSITY_POWER = 2.0


def _rating_intensity(rating_half_steps: int | None) -> float:
    """Return the nonlinear positive-intensity contribution of a rating."""

    if rating_half_steps is None:
        return 0.0
    normalised = max(0.0, min(1.0, rating_half_steps / _RATING_DIVISOR))
    return normalised**RATING_INTENSITY_POWER


def _entry_weight(status: str | None, rating_half_steps: int | None) -> float:
    """Activity weight of one ``LibraryEntry`` from its status and rating."""

    return _STATUS_WEIGHTS.get(status or "", 0.0) + _rating_intensity(rating_half_steps)
