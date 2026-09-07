"""User taste profile for the content recommender (D-12).

``build_profile`` is the activity-weighted mean of the L2-normalised feature
vectors of the works in the user's library:

    profile = Sum( _entry_weight(status, rating) * normalize(vector(work)) )
              / Sum( _entry_weight(status, rating) )

``_entry_weight`` is reused verbatim from ``recommendations._weights`` (the
same signal the genre heuristic and the popularity baseline speak). One
resolved read of the library; cached ``WorkFeatureVector`` rows are preferred
with a fallback to computing the vector on the fly. A user with no
genre-bearing history profiles to ``{}``.
"""

from __future__ import annotations

import math

from django.contrib.auth.models import AbstractBaseUser

from catalogue.models import GameWork
from library.models import LibraryEntry
from recommendations._weights import _entry_weight
from recommendations.content.features import FEATURE_SET_VERSION, feature_vector
from recommendations.models import WorkFeatureVector


def _l2_normalize(vector: dict[str, float]) -> dict[str, float]:
    norm = math.sqrt(math.fsum(value * value for value in vector.values()))
    if not norm:
        return {}
    return {key: value / norm for key, value in vector.items()}


def _load_vectors(work_ids: list[object]) -> dict[object, dict[str, float]]:
    """Feature vector per work id -- cached rows first, computed fallback."""

    vectors: dict[object, dict[str, float]] = {
        row["work_id"]: row["vector_json"]
        for row in WorkFeatureVector.objects.filter(
            work_id__in=work_ids, feature_set_version=FEATURE_SET_VERSION
        ).values("work_id", "vector_json")
    }
    missing = [work_id for work_id in work_ids if work_id not in vectors]
    if missing:
        for work in GameWork.objects.filter(id__in=missing).prefetch_related(
            "genres", "releases__platform"
        ):
            vectors[work.id] = feature_vector(work)
    return vectors


def build_profile(
    user: AbstractBaseUser, corpus_version: str | None = None  # noqa: ARG001
) -> dict[str, float]:
    """Return the activity-weighted, L2-normalised-input taste profile.

    ``corpus_version`` is accepted for call-site symmetry with the rest of the
    laboratory; the profile is built from the user's own library regardless of
    which governed version a candidate is later scored against.
    """

    entries = list(
        LibraryEntry.objects.filter(user=user).values(
            "work_id", "current_status", "rating_half_steps"
        )
    )
    if not entries:
        return {}

    vectors = _load_vectors([entry["work_id"] for entry in entries])

    accumulator: dict[str, float] = {}
    total_weight = 0.0
    for entry in entries:
        weight = _entry_weight(entry["current_status"], entry["rating_half_steps"])
        if weight <= 0:
            continue
        normalized = _l2_normalize(vectors.get(entry["work_id"]) or {})
        if not normalized:
            continue
        total_weight += weight
        for key, value in normalized.items():
            accumulator[key] = accumulator.get(key, 0.0) + weight * value

    if total_weight <= 0 or not accumulator:
        return {}
    return {key: value / total_weight for key, value in accumulator.items()}
