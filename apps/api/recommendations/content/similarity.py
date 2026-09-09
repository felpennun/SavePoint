"""Similarity primitives over sparse feature dicts (D-12), stdlib only.

All feature weights are >= 0 (see ``content/features.py``), so cosine is
naturally bounded to ``[0, 1]``. ``math.fsum`` keeps the dot-product and the
norms order-independent and drift-resistant over the ~10 non-zero terms a
governed feature vector carries.
"""

from __future__ import annotations

import math

from recommendations.content.features import FACET_WEIGHTS

FeatureVector = dict[str, float]

_CORE_FACETS = ("genre", "platform")
_OPTIONAL_FACETS = ("franchise", "developer")


def _facet_values(vector: FeatureVector, facet: str) -> dict[str, float]:
    prefix = f"{facet}:"
    return {key: value for key, value in vector.items() if key.startswith(prefix) and value > 0}


def _facet_affinity(
    profile: FeatureVector, candidate: FeatureVector, facet: str
) -> tuple[float, dict[str, float]]:
    """Return the user's weighted affinity for candidate values in one facet."""

    profile_values = _facet_values(profile, facet)
    candidate_values = _facet_values(candidate, facet)
    if not profile_values or not candidate_values:
        return 0.0, {}
    profile_total = math.fsum(profile_values.values())
    if profile_total <= 0:
        return 0.0, {}
    overlap = {
        key: profile_values[key]
        for key in profile_values.keys() & candidate_values.keys()
    }
    return min(1.0, math.fsum(overlap.values()) / profile_total), overlap


def facet_similarity(profile: FeatureVector, candidate: FeatureVector) -> dict:
    """Compare a candidate using fixed core weights and gated optional bonuses.

    Genre and platform form the candidate's core similarity. Saga and developer
    cannot score merely because a candidate has those fields: they contribute
    only when their values overlap with the user's weighted profile. Missing
    optional metadata is neutral and never redistributes a bonus to the work.
    """

    facet_scores: dict[str, float] = {}
    matched_parts: dict[str, float] = {}
    active_core_weight = 0.0
    core_numerator = 0.0
    for facet in _CORE_FACETS:
        affinity, overlap = _facet_affinity(profile, candidate, facet)
        facet_scores[facet] = affinity
        profile_values = _facet_values(profile, facet)
        candidate_values = _facet_values(candidate, facet)
        if profile_values and candidate_values:
            weight = FACET_WEIGHTS[facet]
            active_core_weight += weight
            core_numerator += weight * affinity
        profile_total = math.fsum(profile_values.values())
        if profile_total > 0:
            for key, value in overlap.items():
                matched_parts[key] = FACET_WEIGHTS[facet] * value / profile_total

    core = core_numerator / active_core_weight if active_core_weight else 0.0

    optional_numerator = 0.0
    for facet in _OPTIONAL_FACETS:
        affinity, overlap = _facet_affinity(profile, candidate, facet)
        facet_scores[facet] = affinity
        optional_numerator += FACET_WEIGHTS[facet] * affinity
        profile_values = _facet_values(profile, facet)
        profile_total = math.fsum(profile_values.values())
        if profile_total > 0:
            for key, value in overlap.items():
                matched_parts[key] = FACET_WEIGHTS[facet] * value / profile_total

    # Optional facets are positive confirmation only. The headroom multiplier
    # keeps them bounded and prevents a sparse saga/developer field from
    # overturning the genre/platform signal.
    score = min(1.0, core + ((1.0 - core) * optional_numerator))
    return {
        "score": score,
        "core_score": core,
        "optional_bonus": score - core,
        "facet_scores": facet_scores,
        "parts": matched_parts,
    }


def cosine(p: FeatureVector, v: FeatureVector) -> float:
    """Return the cosine of the angle between two sparse feature vectors.

    ``0.0`` when either side is empty or has zero norm. Exactly ``1.0`` when
    the two mappings are equal (cosine of any non-zero vector with itself is
    mathematically 1; the equality short-circuit makes that exact rather than
    ``1.0`` minus a rounding error). Clamped into ``[0, 1]`` otherwise so
    floating-point drift can never push a self-similarity above 1.
    """

    if not p or not v:
        return 0.0

    norm_p = math.sqrt(math.fsum(x * x for x in p.values()))
    norm_v = math.sqrt(math.fsum(x * x for x in v.values()))
    if not norm_p or not norm_v:
        return 0.0
    if p == v:
        return 1.0

    numerator = math.fsum(p[k] * v[k] for k in p.keys() & v.keys())
    return max(0.0, min(1.0, numerator / (norm_p * norm_v)))
