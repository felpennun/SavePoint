"""Named, versioned content-recommendation variants (D-10/D-14)."""

from __future__ import annotations

from dataclasses import dataclass

from recommendations.content.features import FEATURE_SET_VERSION


@dataclass(frozen=True)
class VariantSpec:
    """Immutable configuration for one comparable recommender variant."""

    algorithm_id: str
    feature_set_version: str
    combine_mode: str
    params: dict[str, float | int]
    version: str


ALGORITHM_REGISTRY: dict[str, VariantSpec] = {
    "content-cbf-weighted-v1": VariantSpec(
        algorithm_id="content-cbf-weighted-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="weighted_sum",
        params={"w1": 0.7, "w2": 0.3, "w3": 0.0},
        version="v1",
    ),
    "content-cbf-multiplicative-v1": VariantSpec(
        algorithm_id="content-cbf-multiplicative-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="multiplicative",
        params={},
        version="v1",
    ),
    "content-cbf-twostage-v1": VariantSpec(
        algorithm_id="content-cbf-twostage-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="two_stage",
        params={"bands": 5},
        version="v1",
    ),
    "content-cbf-neg-v1": VariantSpec(
        algorithm_id="content-cbf-neg-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="negative_weighted_sum",
        # The positive part is the published weighted baseline.  The negative
        # similarity is subtracted at full scale rather than hidden behind an
        # uncalibrated multiplier; later tuning may publish a new variant id.
        params={"w1": 0.7, "w2": 0.3, "negative_penalty": 1.0},
        version="v1",
    ),
}
