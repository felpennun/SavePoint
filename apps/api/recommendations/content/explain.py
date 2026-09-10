"""Deterministic, feature-grounded explanations (D-16/REC-08)."""

from __future__ import annotations

import math

from recommendations.content.variants import VariantSpec


def explain(
    candidate_vector: dict[str, float],
    profile: dict[str, float],
    cos_numerator_parts: dict[str, float] | VariantSpec | None = None,
    spec: VariantSpec | None = None,
    *,
    candidate_rating_term: float = 0.0,
    rating_term_is_fallback: bool = False,
    negative_similarity: float = 0.0,
) -> dict:
    """Build numeric contribution evidence without generated prose.

    ``cos_numerator_parts`` is normally supplied by the ranker. When omitted,
    it is recomputed from the two sparse vectors, which keeps this helper easy
    to use in tests and evaluation code.
    """

    if isinstance(cos_numerator_parts, VariantSpec) and spec is None:
        spec = cos_numerator_parts
        cos_numerator_parts = None
    if spec is None:
        raise TypeError("explain() requires a VariantSpec")

    parts = cos_numerator_parts or {
        key: profile[key] * candidate_vector[key]
        for key in profile.keys() & candidate_vector.keys()
    }
    positive_parts = [(key, value) for key, value in parts.items() if value > 0]
    tag_parts = {
        key.removeprefix("tag:"): value
        for key, value in positive_parts
        if key.startswith("tag:")
    }
    denominator = math.fsum(value for value in parts.values() if value > 0)
    if denominator <= 0:
        contributions = []
    else:
        contributions = [
            {"tag": tag, "contribution_pct": round(value / denominator, 3)}
            for tag, value in tag_parts.items()
        ]
        contributions.sort(key=lambda item: (-item["contribution_pct"], item["tag"]))

    # These are presentation-neutral tokens, not generated prose.  They only
    # name an overlap actually present in the two vectors, so a caller can
    # localise at most two of them without inventing a causal explanation.
    reason_signals = []
    for key, value in positive_parts:
        facet, separator, slug = key.partition(":")
        if not separator:
            continue
        reason_signals.append(
            {
                "kind": facet,
                "value": slug,
                "contribution_pct": round(value / denominator, 3) if denominator > 0 else 0.0,
            }
        )
    reason_signals.sort(key=lambda item: (-item["contribution_pct"], item["kind"], item["value"]))

    return {
        "contributions": contributions,
        "reason_signals": reason_signals[:2],
        "rating_term": round(candidate_rating_term, 6),
        "rating_term_is_fallback": rating_term_is_fallback,
        "negative_similarity": round(max(0.0, negative_similarity), 6),
        "variant": spec.algorithm_id,
    }
