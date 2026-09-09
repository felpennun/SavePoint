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
from recommendations.content.features import FACET_WEIGHTS, FEATURE_SET_VERSION
from recommendations.content.variants import ALGORITHM_REGISTRY


GENRE_ALGORITHM_ID = "genre-taste-v1"
CONTENT_ALGORITHM_IDS = tuple(ALGORITHM_REGISTRY)
SECTION_ALGORITHM_IDS = (*CONTENT_ALGORITHM_IDS, GENRE_ALGORITHM_ID)
PUBLISHED_RESULT_LIMIT = 20


def configuration_fingerprint() -> str:
    """Identify every algorithm and signal rule used in a published snapshot."""

    payload = {
        "published_result_limit": PUBLISHED_RESULT_LIMIT,
        "feature_set_version": FEATURE_SET_VERSION,
        "facet_weights": FACET_WEIGHTS,
        "popscore": {
            "formula_version": POPSCORE_FORMULA_VERSION,
            "weights": POPSCORE_WEIGHTS,
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
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
