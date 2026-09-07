"""Cosine similarity over sparse feature dicts (D-12), stdlib only.

All feature weights are >= 0 (see ``content/features.py``), so cosine is
naturally bounded to ``[0, 1]``. ``math.fsum`` keeps the dot-product and the
norms order-independent and drift-resistant over the ~10 non-zero terms a
governed feature vector carries.
"""

from __future__ import annotations

import math

FeatureVector = dict[str, float]


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
