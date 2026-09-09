"""User taste profile for the content recommender (D-12).

``build_profile`` is the activity-weighted mean of the L2-normalised feature
vectors of the works in the user's library:

    profile = Sum( _entry_weight(status, rating) * normalize(vector(work)) )
              / Sum( _entry_weight(status, rating) )

``_entry_weight`` is reused verbatim from ``recommendations._weights`` (the
same signal the genre heuristic speaks). One
personal rating contributes its normalised value at power 2, so high seed
ratings have more influence than merely positive ones. One
resolved read of the library; cached ``WorkFeatureVector`` rows are preferred
with a fallback to computing the vector on the fly. A user with no
genre-bearing history profiles to ``{}``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from django.contrib.auth.models import AbstractBaseUser

from catalogue.models import GameWork
from library.models import LibraryEntry
from recommendations._weights import _entry_weight
from recommendations.content.features import FEATURE_SET_VERSION, coverage_report, feature_vector
from recommendations.models import WorkFeatureVector


_POSITIVE_STATUSES = {"completed", "playing"}
_POSITIVE_RATING_MINIMUM = 7  # 3.5 / 5 in LibraryEntry half-steps.
_NEGATIVE_GENRE_MINIMUM = 3


@dataclass(frozen=True)
class ProfileInputs:
    """Serializable, bounded evidence used to construct a taste profile.

    Low ratings never become negative values inside the ordinary profile.  A
    separate, named algorithm may opt into ``negative`` after the three-work
    safeguard, keeping the positive variants comparable and reversible.
    """

    positive: dict[str, float]
    negative: dict[str, float]
    positive_entry_count: int
    positive_rating_sum_half_steps: int
    negative_genres: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "positive_entry_count": self.positive_entry_count,
            "positive_rating_minimum_half_steps": _POSITIVE_RATING_MINIMUM,
            "positive_rating_sum_half_steps": self.positive_rating_sum_half_steps,
            "positive_rating_mean_half_steps": (
                self.positive_rating_sum_half_steps / self.positive_entry_count
                if self.positive_entry_count
                else None
            ),
            "own_rating_role": "seed_preference_intensity",
            "negative_genre_minimum": _NEGATIVE_GENRE_MINIMUM,
            "negative_genres": list(self.negative_genres),
        }


def _l2_normalize(vector: dict[str, float]) -> dict[str, float]:
    norm = math.sqrt(math.fsum(value * value for value in vector.values()))
    if not norm:
        return {}
    return {key: value / norm for key, value in vector.items()}


def _load_vectors(
    work_ids: list[object], corpus_version: str | None
) -> dict[object, dict[str, float]]:
    """Feature vector per work id -- cached rows first, computed fallback."""

    availability = coverage_report(corpus_version)
    # A cache row does not carry the coverage decision that produced it. Once
    # a newly imported facet clears its threshold, recompute instead of
    # silently reusing a vector produced while that facet was unavailable.
    vectors: dict[object, dict[str, float]] = {}
    if not (availability["include_franchise"] or availability["include_developer"]):
        vectors = {
            row["work_id"]: row["vector_json"]
            for row in WorkFeatureVector.objects.filter(
                work_id__in=work_ids, feature_set_version=FEATURE_SET_VERSION
            ).values("work_id", "vector_json")
        }
    missing = [work_id for work_id in work_ids if work_id not in vectors]
    if missing:
        for work in GameWork.objects.filter(id__in=missing).prefetch_related(
            "genres", "releases__platform", "franchises", "developers"
        ):
            vectors[work.id] = feature_vector(
                work,
                include_franchise=availability["include_franchise"],
                include_developer=availability["include_developer"],
            )
    return vectors


def build_profile(
    user: AbstractBaseUser, corpus_version: str | None = None  # noqa: ARG001
) -> dict[str, float]:
    """Return the positive component of :func:`build_profile_inputs`."""

    return build_profile_inputs(user, corpus_version).positive


def build_profile_inputs(
    user: AbstractBaseUser, corpus_version: str | None = None  # noqa: ARG001
) -> ProfileInputs:
    """Build separated positive and safeguarded negative taste evidence.

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
        return ProfileInputs({}, {}, 0, 0, ())

    vectors = _load_vectors([entry["work_id"] for entry in entries], corpus_version)

    accumulator: dict[str, float] = {}
    total_weight = 0.0
    positive_entry_count = 0
    positive_rating_sum_half_steps = 0
    negative_genre_counts: dict[str, int] = {}
    for entry in entries:
        status = entry["current_status"]
        rating = entry["rating_half_steps"]
        if status not in _POSITIVE_STATUSES or rating is None:
            continue
        normalized = _l2_normalize(vectors.get(entry["work_id"]) or {})
        if not normalized:
            continue

        if rating < _POSITIVE_RATING_MINIMUM:
            for key in normalized:
                if key.startswith("genre:"):
                    negative_genre_counts[key] = negative_genre_counts.get(key, 0) + 1
            continue

        weight = _entry_weight(entry["current_status"], entry["rating_half_steps"])
        if weight <= 0:
            continue
        positive_entry_count += 1
        positive_rating_sum_half_steps += rating
        total_weight += weight
        for key, value in normalized.items():
            accumulator[key] = accumulator.get(key, 0.0) + weight * value

    positive = (
        {key: value / total_weight for key, value in accumulator.items()}
        if total_weight > 0 and accumulator
        else {}
    )
    negative_genres = tuple(
        sorted(
            key for key, count in negative_genre_counts.items() if count >= _NEGATIVE_GENRE_MINIMUM
        )
    )
    negative = _l2_normalize({key: float(negative_genre_counts[key]) for key in negative_genres})
    return ProfileInputs(
        positive,
        negative,
        positive_entry_count,
        positive_rating_sum_half_steps,
        negative_genres,
    )
