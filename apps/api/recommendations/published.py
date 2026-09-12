"""One versioned catalogue of recommendation sections published to users.

The offline comparison imports ``CONTENT_ALGORITHM_IDS`` from here, and the
asynchronous product queue uses ``SECTION_ALGORITHM_IDS``. This prevents a
worker, the product page, and the experiment runner from silently drifting
onto different named algorithms or signal weights.
"""

from __future__ import annotations

import hashlib
import json

from catalogue.popularity import POPSCORE_FORMULA_VERSION, POPSCORE_WEIGHTS
from catalogue.corpus import (
    MIN_RECOMMENDATION_TOTAL_RATING_COUNT,
    RECOMMENDATION_ELIGIBILITY_RULE,
)
from recommendations.content.features import (
    FACET_WEIGHTS,
    FEATURE_SET_VERSION,
    RATING_BAYESIAN_PRIOR_COUNT,
    RATING_CONFIDENCE_PRIOR_COUNT,
    RATING_QUALITY_POWER,
    RATING_SIGNAL_VERSION,
    TAG_IDF_FORMULA_VERSION,
    TAG_IDF_SMOOTHING,
)
from recommendations.collaborative import ALGORITHM_ID as COLLABORATIVE_ALGORITHM_ID
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.content.similarity import SIMILARITY_RULE_VERSION
from recommendations.hybrid import (
    ALGORITHM_ID as HYBRID_ALGORITHM_ID,
    MMR_ALGORITHM_ID as HYBRID_MMR_ALGORITHM_ID,
    MMR_LAMBDA,
    MMR_MIN_POOL,
    MMR_POOL_MULTIPLIER,
    PUBLISHED_LIMIT as HYBRID_MMR_LIMIT,
    COLLABORATIVE_WEIGHT,
    CONTENT_WEIGHT,
)


TAG_ALGORITHM_ID = "tag-taste-v1"
# Kept as a Python/API compatibility alias for the existing queue wiring.
GENRE_ALGORITHM_ID = TAG_ALGORITHM_ID
BASE_CONTENT_ALGORITHM_IDS = tuple(ALGORITHM_REGISTRY)
PHASE4_ALGORITHM_IDS = (
    COLLABORATIVE_ALGORITHM_ID,
    HYBRID_ALGORITHM_ID,
    HYBRID_MMR_ALGORITHM_ID,
)
CONTENT_ALGORITHM_IDS = (*BASE_CONTENT_ALGORITHM_IDS, *PHASE4_ALGORITHM_IDS)
SECTION_ALGORITHM_IDS = (*CONTENT_ALGORITHM_IDS, GENRE_ALGORITHM_ID)
PUBLISHED_RESULT_LIMIT = 20

# The signals job (D-TBD, 2026-09-11) is not itself a published section -- it
# has no product-facing result_payload and is deliberately excluded from
# SECTION_ALGORITHM_IDS/_publish_if_complete -- it is an internal dependency
# every worker in SIGNAL_DEPENDENT_ALGORITHM_IDS waits on before it may be
# claimed (recommendations/jobs.py, _claim_next_job). Every base content
# variant scores through rank_content_v1 directly; the two hybrids embed a
# rank_content_v1("content-cbf-weighted-v1", ...) sub-call, so they share the
# same dependency. cf-user-knn-v1 and tag-taste-v1 never call rank_content_v1
# and are therefore not dependents.
SIGNAL_ALGORITHM_ID = "content-signals-v1"
SIGNAL_DEPENDENT_ALGORITHM_IDS = (
    *BASE_CONTENT_ALGORITHM_IDS,
    HYBRID_ALGORITHM_ID,
    HYBRID_MMR_ALGORITHM_ID,
)


def configuration_fingerprint() -> str:
    """Identify every algorithm and signal rule used in a published snapshot."""

    payload = {
        "published_result_limit": PUBLISHED_RESULT_LIMIT,
        "candidate_policy": {
            "rule": RECOMMENDATION_ELIGIBILITY_RULE,
            "min_total_rating_count": MIN_RECOMMENDATION_TOTAL_RATING_COUNT,
        },
        "feature_set_version": FEATURE_SET_VERSION,
        "similarity_rule_version": SIMILARITY_RULE_VERSION,
        "facet_weights": FACET_WEIGHTS,
        "family_idf": {
            "formula_version": TAG_IDF_FORMULA_VERSION,
            "smoothing": TAG_IDF_SMOOTHING,
            "formula": "ln((N_family + smoothing) / (df_value + smoothing)) + 1",
            "normalisation": "per_work_l2_to_each_families_own_facet_weight",
            "families": ("tag", "theme", "mode", "feature", "platform"),
        },
        "popscore": {
            "formula_version": POPSCORE_FORMULA_VERSION,
            "weights": POPSCORE_WEIGHTS,
        },
        "rating_confidence": {
            "version": RATING_SIGNAL_VERSION,
            "quality_power": RATING_QUALITY_POWER,
            "prior_source": "total_rating_count_weighted_frozen_corpus_mean",
            "prior_count": RATING_BAYESIAN_PRIOR_COUNT,
            "confidence_prior_count": RATING_CONFIDENCE_PRIOR_COUNT,
            "observation_count_source": "total_rating_count",
            "quality_formula": "rating_bayesian_normalized ** 2",
            "confidence_formula": "n / (n + m)",
            "final_formula": "rating_quality * rating_confidence",
        },
        "content_algorithms": {
            algorithm_id: {
                "combine_mode": spec.combine_mode,
                "params": spec.params,
                "version": spec.version,
            }
            for algorithm_id, spec in ALGORITHM_REGISTRY.items()
        },
        "phase4_algorithms": {
            COLLABORATIVE_ALGORITHM_ID: {
                "version": "cf-user-knn-v1",
                "neighbor_k": 20,
                "min_common_rated_works": 2,
                "reference_population": "training_users_offline_all_other_users_web",
            },
            HYBRID_ALGORITHM_ID: {
                "version": "hybrid-weighted-cf-v1",
                "content_weight": CONTENT_WEIGHT,
                "collaborative_weight": COLLABORATIVE_WEIGHT,
            },
            HYBRID_MMR_ALGORITHM_ID: {
                "version": HYBRID_MMR_ALGORITHM_ID,
                "base_algorithm_id": HYBRID_ALGORITHM_ID,
                "content_weight": CONTENT_WEIGHT,
                "collaborative_weight": COLLABORATIVE_WEIGHT,
                "lambda": MMR_LAMBDA,
                "pool_rule": f"max({MMR_MIN_POOL}, {MMR_POOL_MULTIPLIER}*K)",
                "feature_set_version": FEATURE_SET_VERSION,
                "presentation_limit": HYBRID_MMR_LIMIT,
            },
        },
        "tag_algorithm_id": TAG_ALGORITHM_ID,
        "tag_order": "taste_score_desc_catalogue_rating_desc_slug_asc",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
