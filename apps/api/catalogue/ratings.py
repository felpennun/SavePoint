"""Live product "display" rating (D-09).

The number a visitor sees on a card / detail page is a *product* value,
computed at read time. It is deliberately kept separate from the frozen
research observation in ``CorpusRatingSnapshot`` (external-only, immutable
per ``corpus_version``): nothing in this module ever reads or writes a
snapshot row.

Task 1 (tracer) ships the external-only path. Task 3 expands
``display_rating`` into the confidence-weighted blend of the IGDB user
rating and the mean of SavePoint ``LibraryEntry.rating_half_steps`` for the
same restricted account set as ``rank_popularity_v1``.
"""

from __future__ import annotations

from catalogue.models import GameWork


def display_rating(work: GameWork) -> float | None:
    """The 0-100 product rating for ``work``, or ``None`` when no source has
    a value (the caller then renders "sin valoración" and the work is
    excluded from rating sort / ``min_rating``)."""

    if work.rating is None:
        return None
    return round(float(work.rating), 2)
