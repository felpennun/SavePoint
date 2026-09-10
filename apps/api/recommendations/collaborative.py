"""Explicit-rating user-neighbour collaborative recommendation ranker."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from django.contrib.auth.models import AbstractBaseUser

from catalogue.corpus import evaluation_candidate_works
from catalogue.models import GameWork
from library.models import LibraryEntry
from recommendations.cancellation import RecommendationComputationCancelled
from recommendations.content.features import FEATURE_SET_VERSION


ALGORITHM_ID = "cf-user-knn-v1"
ALGORITHM_VERSION = "cf-user-knn-v1"
NEIGHBOR_K = 20
MIN_COMMON_RATED_WORKS = 2


def _ensure_current(should_continue: Callable[[], bool] | None) -> None:
    if should_continue is not None and not should_continue():
        raise RecommendationComputationCancelled


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _work_map(
    candidate_ids: Iterable[object],
    corpus_version: str | None,
    prepared: dict[str, Any] | None,
) -> dict[str, GameWork]:
    requested = {str(value) for value in candidate_ids}
    if prepared is not None:
        return {
            str(work.id): work
            for work in prepared.get("works", [])
            if str(work.id) in requested
        }
    query = evaluation_candidate_works(corpus_version).filter(id__in=requested)
    return {
        str(work.id): work
        for work in query.prefetch_related("curated_labels", "releases__platform", "franchises", "developers")
    }


def _ratings_by_user(
    user_ids: Iterable[object],
    *,
    target_user_id: object,
) -> dict[str, dict[str, float]]:
    requested = {str(value) for value in user_ids}
    requested.discard(str(target_user_id))
    if not requested:
        return {}
    rows = LibraryEntry.objects.filter(
        user_id__in=requested,
        rating_half_steps__isnull=False,
    ).values_list("user_id", "work_id", "rating_half_steps")
    ratings: dict[str, dict[str, float]] = {}
    for user_id, work_id, rating in rows:
        ratings.setdefault(str(user_id), {})[str(work_id)] = max(0.0, min(1.0, float(rating) / 10.0))
    return ratings


def _target_ratings(user: AbstractBaseUser) -> dict[str, float]:
    return {
        str(work_id): max(0.0, min(1.0, float(rating) / 10.0))
        for work_id, rating in LibraryEntry.objects.filter(
            user=user,
            rating_half_steps__isnull=False,
        ).values_list("work_id", "rating_half_steps")
    }


def _cosine_on_overlap(target: dict[str, float], other: dict[str, float]) -> tuple[float, int]:
    overlap = sorted(set(target) & set(other))
    if len(overlap) < MIN_COMMON_RATED_WORKS:
        return 0.0, len(overlap)
    target_mean = math.fsum(target[key] for key in overlap) / len(overlap)
    other_mean = math.fsum(other[key] for key in overlap) / len(overlap)
    target_centered = [target[key] - target_mean for key in overlap]
    other_centered = [other[key] - other_mean for key in overlap]
    denominator = math.sqrt(math.fsum(value * value for value in target_centered)) * math.sqrt(
        math.fsum(value * value for value in other_centered)
    )
    if denominator == 0:
        return 0.0, len(overlap)
    return math.fsum(left * right for left, right in zip(target_centered, other_centered)) / denominator, len(overlap)


def _dto_item(work: GameWork, score: float, *, neighbor_count: int, fallback: bool) -> dict[str, Any]:
    return {
        "work_id": str(work.id),
        "slug": work.canonical_slug,
        "title": work.title_en or work.original_title,
        "score": round(score, 6),
        "contributions": [],
        "rating_term": round(score, 6),
        "rating_term_is_fallback": fallback,
        "reason_signals": [],
        "negative_similarity": 0.0,
        "signals": {
            "external_rating": None,
            "rating_quality": None,
            "rating_confidence": None,
            "rating_volume": None,
            "popscore": None,
            "popscore_imputed": False,
            "recency_score": None,
            "collaborative_score": round(score, 6),
            "neighbor_count": neighbor_count,
        },
    }


def rank_collaborative_user_knn_v1(
    user: AbstractBaseUser,
    *,
    candidate_ids: Iterable[object],
    limit: int = 20,
    corpus_version: str | None = None,
    reference_user_ids: Iterable[object] | None = None,
    prepared: dict[str, Any] | None = None,
    should_continue: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Rank candidates from the positive neighbourhood of one user.

    Similarity is Pearson-style cosine over mean-centred explicit ratings. The
    frozen offline run supplies training users as the reference population;
    the web worker uses every other user with at least one explicit rating.
    """

    _ensure_current(should_continue)
    target = _target_ratings(user)
    uses_web_reference_population = reference_user_ids is None
    if uses_web_reference_population:
        reference_user_ids = LibraryEntry.objects.exclude(user=user).values_list("user_id", flat=True).distinct()
    reference_ids = sorted({str(value) for value in reference_user_ids if str(value) != str(user.pk)})
    reference_ratings = _ratings_by_user(reference_ids, target_user_id=user.pk)
    neighbours: list[tuple[float, str, int]] = []
    for index, (reference_id, ratings) in enumerate(reference_ratings.items()):
        if index % 128 == 0:
            _ensure_current(should_continue)
        similarity, overlap = _cosine_on_overlap(target, ratings)
        if similarity > 0:
            neighbours.append((similarity, reference_id, overlap))
    neighbours.sort(key=lambda row: (-row[0], row[1]))
    neighbours = neighbours[:NEIGHBOR_K]

    candidate_strings = sorted({str(value) for value in candidate_ids})
    works = _work_map(candidate_strings, corpus_version, prepared)
    weighted_scores: dict[str, tuple[float, float, int]] = {}
    for candidate in candidate_strings:
        numerator = 0.0
        denominator = 0.0
        neighbor_count = 0
        for similarity, reference_id, _overlap in neighbours:
            rating = reference_ratings[reference_id].get(candidate)
            if rating is None:
                continue
            numerator += similarity * rating
            denominator += similarity
            neighbor_count += 1
        if denominator:
            weighted_scores[candidate] = (numerator / denominator, denominator, neighbor_count)

    global_frequency: dict[str, float] = {}
    for ratings in reference_ratings.values():
        for work_id in ratings:
            global_frequency[work_id] = global_frequency.get(work_id, 0.0) + 1.0
    reference_count = len(reference_ratings)
    ranked: list[tuple[float, str, dict[str, Any]]] = []
    for index, candidate in enumerate(candidate_strings):
        if index % 128 == 0:
            _ensure_current(should_continue)
        work = works.get(candidate)
        if work is None:
            continue
        if candidate in weighted_scores:
            score, _weight, neighbor_count = weighted_scores[candidate]
            fallback = False
        else:
            score = global_frequency.get(candidate, 0.0) / reference_count if reference_count else 0.0
            neighbor_count = 0
            fallback = True
        ranked.append((score, work.canonical_slug, _dto_item(work, score, neighbor_count=neighbor_count, fallback=fallback)))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    results = [item for _score, _slug, item in ranked[: max(1, min(50, int(limit)))]]
    generated_at = datetime.now(timezone.utc)
    input_hash = _hash_payload({
        "algorithm": ALGORITHM_VERSION,
        "user_id": str(user.pk),
        "candidate_ids": candidate_strings,
        "target_ratings": sorted(target.items()),
        "reference_user_ids": reference_ids,
        "neighbour_ids": [row[1] for row in neighbours],
    })
    snapshot_hash = (prepared or {}).get("snapshot_sha256", "")
    popscore_hash = (prepared or {}).get("popscore_snapshot_sha256", "")
    return {
        "algorithm_id": ALGORITHM_ID,
        "generated_at": generated_at.isoformat(),
        "input_snapshot_sha256": input_hash,
        "feature_set_version": FEATURE_SET_VERSION,
        "corpus_version": corpus_version,
        "snapshot_sha256": snapshot_hash,
        "popscore_snapshot_sha256": popscore_hash,
        "parameters": {
            "neighbor_k": NEIGHBOR_K,
            "min_common_rated_works": MIN_COMMON_RATED_WORKS,
            "rating_scale": "rating_half_steps / 10",
            "reference_population": "all_other_users" if uses_web_reference_population else "training_users",
        },
        "insufficient_history": not bool(neighbours),
        "limitation": "Explicit-rating user-kNN over the selected reference population; sparse histories fall back to reference interaction frequency.",
        "results": results,
    }
