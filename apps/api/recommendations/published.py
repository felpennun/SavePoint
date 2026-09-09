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
    RATING_QUALITY_POWER,
    RATING_SIGNAL_VERSION,
    RATING_VOLUME_BOOST,
    RATING_VOLUME_FLOOR,
)
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.content.similarity import SIMILARITY_RULE_VERSION


GENRE_ALGORITHM_ID = "genre-taste-v1"
CONTENT_ALGORITHM_IDS = tuple(ALGORITHM_REGISTRY)
SECTION_ALGORITHM_IDS = (*CONTENT_ALGORITHM_IDS, GENRE_ALGORITHM_ID)
PUBLISHED_RESULT_LIMIT = 20


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
        "popscore": {
            "formula_version": POPSCORE_FORMULA_VERSION,
            "weights": POPSCORE_WEIGHTS,
        },
        "rating_confidence": {
            "version": RATING_SIGNAL_VERSION,
            "quality_power": RATING_QUALITY_POWER,
            "volume_boost": RATING_VOLUME_BOOST,
            "volume_floor": RATING_VOLUME_FLOOR,
            "volume_source": "total_rating_count",
        },
        "content_algorithms": {
            algorithm_id: {
                "combine_mode": spec.combine_mode,
                "params": spec.params,
                "version": spec.version,
            }
            for algorithm_id, spec in ALGORITHM_REGISTRY.items()
        },
        "genre_algorithm_id": GENRE_ALGORITHM_ID,
        "genre_order": "taste_score_desc_catalogue_rating_desc_slug_asc",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
