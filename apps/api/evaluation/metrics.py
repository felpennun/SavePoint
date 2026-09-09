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


def _top_k_lists(ranked_lists: Iterable[Sequence[object]], k: int) -> list[list[object]]:
    """Materialise bounded recommendation lists without treating ``k <= 0`` as data."""

    if k <= 0:
        return []
    return [list(ranked[:k]) for ranked in ranked_lists]


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


def catalogue_coverage_at_k(
    ranked_lists: Iterable[Sequence[object]], candidate_universe: Iterable[object], k: int
) -> float | None:
    """Fraction of the eligible candidate universe exposed in any top-``k`` list."""

    universe = set(candidate_universe)
    if not universe:
        return None
    exposed = {item for ranked in _top_k_lists(ranked_lists, k) for item in ranked}
    return len(exposed & universe) / len(universe)


def prediction_coverage_at_k(
    ranked_lists: Iterable[Sequence[object]], candidate_lists: Iterable[Sequence[object]], k: int
) -> float | None:
    """Fraction of candidate slots for which a ranker emitted a valid top-``k`` item.

    This detects a ranker that cannot score part of a shared candidate manifest;
    it is intentionally separate from catalogue coverage, which measures variety.
    """

    pairs = list(zip(ranked_lists, candidate_lists, strict=True))
    denominator = math.fsum(min(k, len(candidates)) for _ranked, candidates in pairs if k > 0)
    if denominator <= 0:
        return None
    numerator = math.fsum(min(k, len(ranked)) for ranked, _candidates in pairs if k > 0)
    return numerator / denominator


def concentration_hhi_at_k(ranked_lists: Iterable[Sequence[object]], k: int) -> float | None:
    """Herfindahl-Hirschman concentration of item exposure across top-``k`` lists."""

    exposures: dict[object, int] = {}
    total = 0
    for ranked in _top_k_lists(ranked_lists, k):
        for item in ranked:
            exposures[item] = exposures.get(item, 0) + 1
            total += 1
    if total == 0:
        return None
    return math.fsum((count / total) ** 2 for count in exposures.values())


def intra_list_diversity(
    ranked_ids: Sequence[object], vectors: dict[object, dict[str, float]]
) -> float | None:
    """Mean pairwise cosine distance, or ``None`` when it is not estimable."""

    if len(ranked_ids) < 2:
        return None
    selected = [vectors.get(item) for item in ranked_ids]
    if any(vector is None for vector in selected):
        return None

    distances: list[float] = []
    for index, left in enumerate(selected[:-1]):
        assert left is not None
        left_norm = math.sqrt(math.fsum(value * value for value in left.values()))
        for right in selected[index + 1 :]:
            assert right is not None
            right_norm = math.sqrt(math.fsum(value * value for value in right.values()))
            if left_norm == 0 or right_norm == 0:
                return None
            shared = left.keys() & right.keys()
            similarity = math.fsum(left[key] * right[key] for key in shared) / (left_norm * right_norm)
            distances.append(max(0.0, min(1.0, 1.0 - similarity)))
    return math.fsum(distances) / len(distances) if distances else None


def novelty_at_k(
    ranked_ids: Sequence[object], item_probabilities: dict[object, float], k: int
) -> float | None:
    """Mean self-information ``-log2(p_i)`` over a top-``k`` list.

    A zero or missing training probability is not silently converted to an
    infinite novelty score: it is reported as not estimable instead.
    """

    items = list(ranked_ids[:k]) if k > 0 else []
    if not items:
        return None
    probabilities = [item_probabilities.get(item) for item in items]
    if any(value is None or value <= 0.0 or value > 1.0 for value in probabilities):
        return None
    return math.fsum(-math.log2(value) for value in probabilities if value is not None) / len(items)
