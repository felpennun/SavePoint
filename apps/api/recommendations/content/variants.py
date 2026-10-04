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
    params: dict[str, float | int | str]
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
    "content-cbf-weighted-pop-v1": VariantSpec(
        algorithm_id="content-cbf-weighted-pop-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="weighted_sum",
        params={
            "w_content": 0.55,
            "w_rating": 0.25,
            "w_popscore": 0.20,
            "popscore_missing_floor": 0.0,
        },
        version="v1",
    ),
    "content-cbf-multiplicative-pop-v1": VariantSpec(
        algorithm_id="content-cbf-multiplicative-pop-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="multiplicative_popscore",
        params={"popscore_missing_floor": 0.0, "popscore_swing": 0.20},
        version="v1",
    ),
    "content-cbf-twostage-pop-v1": VariantSpec(
        algorithm_id="content-cbf-twostage-pop-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="two_stage_popscore",
        params={
            "bands": 5,
            "w_rating": 0.80,
            "w_popscore": 0.20,
            "popscore_missing_floor": 0.0,
        },
        version="v1",
    ),
    "content-cbf-neg-pop-v1": VariantSpec(
        algorithm_id="content-cbf-neg-pop-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="negative_weighted_sum_popscore",
        params={
            "w_content": 0.55,
            "w_rating": 0.25,
            "w_popscore": 0.20,
            "negative_penalty": 1.0,
            "popscore_missing_floor": 0.0,
        },
        version="v1",
    ),
    "recency-v1": VariantSpec(
        algorithm_id="recency-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="weighted_sum",
        params={
            "w_content": 0.20,
            # Volume is composed into rating-confidence, so it is not also
            # added as an independent term (which would double-count it).
            "w_rating": 0.20,
            "w_popscore": 0.20,
            "w_recency": 0.40,
            "year_decay": 0.35,
            "popscore_missing_floor": 0.0,
        },
        version="v1",
    ),
    "content-cbf-mmr-v1": VariantSpec(
        algorithm_id="content-cbf-mmr-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="mmr",
        params={
            "base_algorithm_id": "content-cbf-weighted-v1",
            "lambda": 0.80,
        },
        version="v1",
    ),
    "content-cbf-mmr-pop-v1": VariantSpec(
        algorithm_id="content-cbf-mmr-pop-v1",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="mmr",
        params={
            "base_algorithm_id": "content-cbf-weighted-pop-v1",
            "lambda": 0.80,
        },
        version="v1",
    ),
}

# Variants that exist only in the product (the web page), never in the offline
# comparison: ALGORITHM_REGISTRY is the frozen set the evaluation lab and the
# thesis document, so retuning a published section adds a new id here instead
# of editing a v1 entry or widening the lab.
#
# mmr-pop-v2 keeps lambda 0.80 and rebalances the relevance blend it re-ranks
# (content 0.4375 / rating 0.25 / PopScore 0.3125). Its effective weights are
# therefore content 0.35, rating 0.20, PopScore 0.25 and variety 0.20.
PRODUCT_VARIANT_REGISTRY: dict[str, VariantSpec] = {
    "content-cbf-weighted-pop-v2": VariantSpec(
        algorithm_id="content-cbf-weighted-pop-v2",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="weighted_sum",
        params={
            "w_content": 0.4375,
            "w_rating": 0.25,
            "w_popscore": 0.3125,
            "popscore_missing_floor": 0.0,
        },
        version="v2",
    ),
    "content-cbf-mmr-pop-v2": VariantSpec(
        algorithm_id="content-cbf-mmr-pop-v2",
        feature_set_version=FEATURE_SET_VERSION,
        combine_mode="mmr",
        params={
            "base_algorithm_id": "content-cbf-weighted-pop-v2",
            "lambda": 0.80,
        },
        version="v2",
    ),
}

# Every variant the ranker can score (lab + product-only).
RANKABLE_VARIANT_REGISTRY: dict[str, VariantSpec] = {
    **ALGORITHM_REGISTRY,
    **PRODUCT_VARIANT_REGISTRY,
}
