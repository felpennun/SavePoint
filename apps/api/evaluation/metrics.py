"""Hand-written top-N ranking metrics (D-22).

Binary relevance only for Phase 2 (leave-one-out has a single relevant item per
user), but every function is written for the general multi-positive case so
Phase 3 can reuse them unchanged. Pure stdlib — no scikit-learn, no numpy
(STACK: "implement project metrics explicitly").

Conventions
-----------
* ``ranked_ids`` is an ordered sequence of candidate ids, best first.
* ``relevant`` is a set/iterable of the ids that count as hits.
* ``precision_at_k`` divides by ``k`` (not by ``len(ranked_ids[:k])``), the
  standard top-N convention.
* nDCG uses binary gains and the ``1 / log2(rank + 1)`` discount
  (``i + 2`` for a 0-indexed ``i``); the ideal DCG ranks ``min(len(relevant), k)``
  hits first.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def _as_set(relevant: Iterable[object]) -> set[object]:
    return relevant if isinstance(relevant, (set, frozenset)) else set(relevant)


def precision_at_k(ranked_ids: Sequence[object], relevant: Iterable[object], k: int) -> float:
    """Fraction of the top ``k`` slots filled by a relevant item."""

    if k <= 0:
        return 0.0
    rel = _as_set(relevant)
    hits = sum(1 for wid in ranked_ids[:k] if wid in rel)
    return hits / k


def recall_at_k(ranked_ids: Sequence[object], relevant: Iterable[object], k: int) -> float:
    """Fraction of all relevant items retrieved within the top ``k``."""

    rel = _as_set(relevant)
    if not rel:
        return 0.0
    top = ranked_ids[:k] if k > 0 else []
    hits = sum(1 for wid in top if wid in rel)
    return hits / len(rel)


def dcg_at_k(ranked_ids: Sequence[object], relevant: Iterable[object], k: int) -> float:
    """Discounted cumulative gain over the top ``k`` with binary gains."""

    if k <= 0:
        return 0.0
    rel = _as_set(relevant)
    return math.fsum(
        1.0 / math.log2(i + 2) for i, wid in enumerate(ranked_ids[:k]) if wid in rel
    )


def idcg_at_k(num_relevant: int, k: int) -> float:
    """Ideal DCG: every hit packed into the first ``min(num_relevant, k)`` slots."""

    if k <= 0 or num_relevant <= 0:
        return 0.0
    return math.fsum(1.0 / math.log2(i + 2) for i in range(min(num_relevant, k)))


def ndcg_at_k(ranked_ids: Sequence[object], relevant: Iterable[object], k: int) -> float:
    """Normalised DCG in ``[0, 1]``; ``0.0`` when there is nothing to retrieve."""

    rel = _as_set(relevant)
    ideal = idcg_at_k(len(rel), k)
    if ideal == 0.0:
        return 0.0
    return dcg_at_k(ranked_ids, rel, k) / ideal


def average_precision_at_k(ranked_ids: Sequence[object], relevant: Iterable[object], k: int) -> float:
    """Average precision over the top ``k`` (the per-query term of MAP)."""

    rel = _as_set(relevant)
    if not rel or k <= 0:
        return 0.0
    running_hits = 0
    weighted = 0.0
    for i, wid in enumerate(ranked_ids[:k]):
        if wid in rel:
            running_hits += 1
            weighted += running_hits / (i + 1)
    denom = min(len(rel), k)
    return weighted / denom if denom else 0.0


def map_at_k(
    ranked_lists: Iterable[Sequence[object]],
    relevant_sets: Iterable[Iterable[object]],
    k: int,
) -> float:
    """Mean of :func:`average_precision_at_k` across queries."""

    pairs = list(zip(ranked_lists, relevant_sets, strict=True))
    if not pairs:
        return 0.0
    return math.fsum(
        average_precision_at_k(ranked, rel, k) for ranked, rel in pairs
    ) / len(pairs)
