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
    genre_parts = {
        key.removeprefix("genre:"): value
        for key, value in parts.items()
        if key.startswith("genre:") and value > 0
    }
    denominator = math.fsum(value for value in parts.values() if value > 0)
    if denominator <= 0:
        contributions = []
    else:
        contributions = [
            {"genre": genre, "contribution_pct": round(value / denominator, 3)}
            for genre, value in genre_parts.items()
        ]
        contributions.sort(key=lambda item: (-item["contribution_pct"], item["genre"]))

    return {
        "contributions": contributions,
        "rating_term": round(candidate_rating_term, 6),
        "rating_term_is_fallback": rating_term_is_fallback,
        "variant": spec.algorithm_id,
    }
