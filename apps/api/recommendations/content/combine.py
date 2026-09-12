"""Rating-term and score-combination primitives for content variants."""

from __future__ import annotations

import math
from statistics import median

from catalogue.models import CorpusRatingSnapshot, GameWork
from recommendations.content.features import (
    compose_rating_confidence,
    tag_rating_profile,
    rating_bayesian_normalized,
    rating_final,
    rating_quality_signal,
)
from recommendations.content.variants import VariantSpec


def _candidate_snapshot_rating(
    work: GameWork, corpus_version: str | None
) -> tuple[float | None, int, int | None]:
    snapshots = CorpusRatingSnapshot.objects.filter(work=work, rating__isnull=False)
    if corpus_version is not None:
        snapshots = snapshots.filter(corpus_version=corpus_version)
    rows = list(snapshots.values_list("rating", "rating_count", "total_rating_count"))
    if not rows:
        return None, 0, None

    total_count = sum(count for _rating, count, _total_count in rows)
    if total_count:
        rating = math.fsum(rating * count for rating, count, _total_count in rows) / total_count
    else:
        rating = math.fsum(rating for rating, _count, _total_count in rows) / len(rows)
    total_rating_count = max(
        (value for _rating, _count, value in rows if value is not None),
        default=None,
    )
    return rating, total_count, total_rating_count


def rating_term(
    work: GameWork,
    corpus_version: str | None,
    tag_profile: dict[str, float] | None = None,
    snapshot_stats: dict[object, tuple[float | None, int, int | None]] | None = None,
    rating_prior: float | None = None,
) -> tuple[float, bool]:
    """Return a bounded external-rating signal and whether it is imputed.

    An observed candidate snapshot rating is used directly after the shared
    quality transformation. The corpus genre profile is only a fallback for a
    candidate without an observed rating, and that result is flagged.
    """

    profile = tag_profile if tag_profile is not None else tag_rating_profile(corpus_version)
    # GameWorkCuratedLabel keeps one evidence row per independent curation
    # source for the same tag (see catalogue/serializers.py::_tags), so a
    # bare work.curated_labels.all() can repeat a slug -- deduplicate before
    # taking the median or a doubly-evidenced tag counts twice.
    candidate_tag_slugs = {tag.slug for tag in work.curated_labels.all()}
    tag_values = [profile[slug] for slug in candidate_tag_slugs if slug in profile]
    if snapshot_stats is None:
        own_rating, _rating_count, _total_rating_count = _candidate_snapshot_rating(work, corpus_version)
    else:
        own_rating, _rating_count, _total_rating_count = snapshot_stats.get(work.id, (None, 0, None))

    if own_rating is None:
        if not tag_values:
            return 0.0, True
        return rating_quality_signal(float(median(tag_values))) or 0.0, True

    normalized = rating_bayesian_normalized(
        own_rating, _total_rating_count, rating_prior
    )
    return rating_final(normalized, _total_rating_count) or 0.0, False


def combine(
    cosine_similarity: float,
    candidate_rating_term: float,
    own_rating: float | None,
    spec: VariantSpec,
    *,
    negative_similarity: float = 0.0,
    recency_score: float | None = None,
    rating_volume: float | None = None,
    popscore: float | None = None,
) -> float:
    """Dispatch to a named variant's deterministic score function."""

    cosine_similarity = max(0.0, min(1.0, cosine_similarity))
    candidate_rating_term = max(0.0, min(1.0, candidate_rating_term))
    negative_similarity = max(0.0, min(1.0, negative_similarity))
    bounded_recency = (
        None if recency_score is None else max(0.0, min(1.0, recency_score))
    )
    bounded_volume = (
        None if rating_volume is None else max(0.0, min(1.0, rating_volume))
    )
    bounded_popscore = (
        None if popscore is None else max(0.0, min(1.0, popscore))
    )
    missing_popscore_floor = spec.params.get("popscore_missing_floor")
    effective_popscore = bounded_popscore
    if effective_popscore is None and missing_popscore_floor is not None:
        effective_popscore = max(0.0, min(1.0, float(missing_popscore_floor)))
    rating_confidence = compose_rating_confidence(candidate_rating_term, bounded_volume) or 0.0

    if spec.combine_mode == "weighted_sum":
        # ``w1``/``w2``/``w3`` remain accepted for v1 compatibility. New
        # protocol grids use names that identify the signal being weighted.
        weights = [
            (float(spec.params.get("w_content", spec.params.get("w1", 0.0))), cosine_similarity),
            (float(spec.params.get("w_rating", spec.params.get("w2", 0.0))), rating_confidence),
            (float(spec.params.get("w_popscore", 0.0)), effective_popscore),
            (float(spec.params.get("w_recency", 0.0)), bounded_recency),
            (float(spec.params.get("w3", 0.0)), None if own_rating is None else max(0.0, min(1.0, own_rating))),
        ]
        active = [(weight, value) for weight, value in weights if weight > 0 and value is not None]
        total_weight = math.fsum(weight for weight, _value in active)
        return math.fsum(weight * value for weight, value in active) / total_weight if total_weight else 0.0
    if spec.combine_mode == "multiplicative":
        return cosine_similarity * rating_confidence
    if spec.combine_mode == "multiplicative_popscore":
        swing = max(0.0, min(1.0, float(spec.params.get("popscore_swing", 0.20))))
        popscore_factor = 1.0 - swing + (2.0 * swing * (effective_popscore or 0.0))
        return cosine_similarity * rating_confidence * popscore_factor
    if spec.combine_mode == "two_stage":
        bands = max(1, int(spec.params.get("bands", 5)))
        band = min(bands - 1, int(cosine_similarity * bands))
        # The integer band dominates; rating only orders candidates inside it.
        return band + (rating_confidence / (bands + 1))
    if spec.combine_mode == "two_stage_popscore":
        bands = max(1, int(spec.params.get("bands", 5)))
        band = min(bands - 1, int(cosine_similarity * bands))
        w_rating = max(0.0, float(spec.params.get("w_rating", 0.80)))
        w_popscore = max(0.0, float(spec.params.get("w_popscore", 0.20)))
        total = w_rating + w_popscore
        tie_break = (
            (w_rating * rating_confidence + w_popscore * (effective_popscore or 0.0)) / total
            if total
            else 0.0
        )
        return band + (tie_break / (bands + 1))
    if spec.combine_mode == "negative_weighted_sum":
        positive = (
            float(spec.params.get("w1", 0.0)) * cosine_similarity
            + float(spec.params.get("w2", 0.0)) * rating_confidence
        )
        penalty = float(spec.params.get("negative_penalty", 0.0)) * negative_similarity
        return max(0.0, positive - penalty)
    if spec.combine_mode == "negative_weighted_sum_popscore":
        positive = (
            float(spec.params.get("w_content", 0.55)) * cosine_similarity
            + float(spec.params.get("w_rating", 0.25)) * rating_confidence
            + float(spec.params.get("w_popscore", 0.20)) * (effective_popscore or 0.0)
        )
        penalty = float(spec.params.get("negative_penalty", 0.0)) * negative_similarity
        return max(0.0, positive - penalty)
    if spec.combine_mode == "recency_only":
        return bounded_recency or 0.0
    raise ValueError(f"Unsupported content combination mode: {spec.combine_mode}")
