"""Deterministic maximal-marginal-relevance re-ranking primitives."""

from __future__ import annotations

from typing import Callable

from recommendations.content.similarity import cosine


def mmr_rerank(
    scored: list[tuple[float, str, dict]],
    vectors: dict[object, dict[str, float]],
    *,
    lambda_value: float = 0.80,
    should_continue: Callable[[], bool] | None = None,
) -> list[dict]:
    """Greedily select relevant but non-redundant items.

    ``scored`` contains the base ranker's relevance score. MMR is a
    presentation/ranking layer: it preserves that score as evidence and only
    uses the selection score to choose the order. Pairwise redundancy is the
    cosine similarity of the already versioned feature vectors.
    """

    if not scored:
        return []
    value = max(0.0, min(1.0, float(lambda_value)))
    remaining = list(scored)
    vector_by_id = {str(work_id): vector for work_id, vector in vectors.items()}
    selected: list[dict] = []
    selected_ids: list[str] = []
    while remaining:
        if should_continue is not None and not should_continue():
            from recommendations.cancellation import RecommendationComputationCancelled

            raise RecommendationComputationCancelled

        best_index = 0
        best_key: tuple[float, float, str] | None = None
        best_mmr = 0.0
        best_redundancy = 0.0
        for index, (relevance, slug, item) in enumerate(remaining):
            item_id = str(item["work_id"])
            if not selected_ids:
                redundancy = 0.0
            else:
                candidate_vector = vector_by_id.get(item_id, {})
                redundancy = max(
                    (
                        cosine(candidate_vector, vector_by_id.get(selected_id, {}))
                        for selected_id in selected_ids
                    ),
                    default=0.0,
                )
            bounded_relevance = max(0.0, min(1.0, float(relevance)))
            mmr_score = (
                bounded_relevance
                if not selected_ids
                else value * bounded_relevance - (1.0 - value) * redundancy
            )
            key = (-mmr_score, -bounded_relevance, _stable_slug(slug))
            if best_key is None or key < best_key:
                best_index = index
                best_key = key
                best_mmr = mmr_score
                best_redundancy = redundancy

        _relevance, _slug, item = remaining.pop(best_index)
        copied = {**item, "signals": {**item.get("signals", {})}}
        copied["signals"].update(
            {
                "mmr_relevance": round(max(0.0, min(1.0, float(_relevance))), 6),
                "mmr_redundancy": round(best_redundancy, 6),
                "mmr_score": round(best_mmr, 6),
            }
        )
        copied["score"] = round(best_mmr, 6)
        selected.append(copied)
        selected_ids.append(item["work_id"])
    return selected


def _stable_slug(value: str) -> str:
    """Keep tie-breaking deterministic even for malformed fixture slugs."""

    return str(value)
