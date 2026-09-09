"""Rating-term and score-combination primitives for content variants."""

from __future__ import annotations

import math
from statistics import median

from catalogue.models import CorpusRatingSnapshot, GameWork
from recommendations.content.features import genre_rating_profile
from recommendations.content.variants import VariantSpec


_RATING_SCALE = 100.0
_CONFIDENCE_PRIOR = 1000.0


def _normalise_rating(value: float) -> float:
    return max(0.0, min(1.0, value / _RATING_SCALE))


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
    genre_profile: dict[str, float] | None = None,
    snapshot_stats: dict[object, tuple[float | None, int, int | None]] | None = None,
) -> tuple[float, bool]:
    """Return a bounded external-rating signal and whether it is imputed.

    A candidate snapshot rating is blended with the mean rating of its genres.
    Confidence is deliberately explicit and reproducible: 1,000 ratings is the
    full-confidence prior. If the candidate has no snapshot rating, its genre
    median is used and the result is flagged as a fallback.
    """

    profile = genre_profile if genre_profile is not None else genre_rating_profile(corpus_version)
    genre_values = [profile[genre.slug] for genre in work.genres.all() if genre.slug in profile]
    if snapshot_stats is None:
        own_rating, rating_count, _total_rating_count = _candidate_snapshot_rating(work, corpus_version)
    else:
        own_rating, rating_count, _total_rating_count = snapshot_stats.get(work.id, (None, 0, None))

    if own_rating is None:
        if not genre_values:
            return 0.0, True
        return _normalise_rating(float(median(genre_values))), True

    own_term = _normalise_rating(own_rating)
    if not genre_values:
        return own_term, False

    genre_term = _normalise_rating(math.fsum(genre_values) / len(genre_values))
    confidence = min(1.0, rating_count / _CONFIDENCE_PRIOR)
    return (own_term * confidence) + (genre_term * (1.0 - confidence)), False


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

    if spec.combine_mode == "weighted_sum":
        # ``w1``/``w2``/``w3`` remain accepted for v1 compatibility. New
        # protocol grids use names that identify the signal being weighted.
        weights = [
            (float(spec.params.get("w_content", spec.params.get("w1", 0.0))), cosine_similarity),
            (float(spec.params.get("w_rating", spec.params.get("w2", 0.0))), candidate_rating_term),
            (float(spec.params.get("w_volume", 0.0)), bounded_volume),
            (float(spec.params.get("w_popscore", 0.0)), bounded_popscore),
            (float(spec.params.get("w_recency", 0.0)), bounded_recency),
            (float(spec.params.get("w3", 0.0)), None if own_rating is None else max(0.0, min(1.0, own_rating))),
        ]
        active = [(weight, value) for weight, value in weights if weight > 0 and value is not None]
        total_weight = math.fsum(weight for weight, _value in active)
        return math.fsum(weight * value for weight, value in active) / total_weight if total_weight else 0.0
    if spec.combine_mode == "multiplicative":
        return cosine_similarity * candidate_rating_term
    if spec.combine_mode == "two_stage":
        bands = max(1, int(spec.params.get("bands", 5)))
        band = min(bands - 1, int(cosine_similarity * bands))
        # The integer band dominates; rating only orders candidates inside it.
        return band + (candidate_rating_term / (bands + 1))
    if spec.combine_mode == "negative_weighted_sum":
        positive = (
            float(spec.params.get("w1", 0.0)) * cosine_similarity
            + float(spec.params.get("w2", 0.0)) * candidate_rating_term
        )
        penalty = float(spec.params.get("negative_penalty", 0.0)) * negative_similarity
        return max(0.0, positive - penalty)
    if spec.combine_mode == "recency_only":
        return bounded_recency or 0.0
    raise ValueError(f"Unsupported content combination mode: {spec.combine_mode}")
