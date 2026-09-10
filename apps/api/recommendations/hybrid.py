"""Shared hybrid content and explicit-rating collaborative recommenders."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Iterable

from django.contrib.auth.models import AbstractBaseUser

from catalogue.corpus import evaluation_candidate_works
from catalogue.models import GameWork
from recommendations.collaborative import ALGORITHM_ID as COLLABORATIVE_ALGORITHM_ID
from recommendations.collaborative import rank_collaborative_user_knn_v1
from recommendations.content.diversity import mmr_rerank
from recommendations.content.features import (
    FEATURE_SET_VERSION,
    coverage_report,
    feature_vector,
    tag_idf_profile,
)
from recommendations.content.rank import rank_content_v1


ALGORITHM_ID = "hybrid-weighted-cf-v1"
MMR_ALGORITHM_ID = "hybrid-mmr-v1"
CONTENT_WEIGHT = 0.60
COLLABORATIVE_WEIGHT = 0.40
MMR_LAMBDA = 0.80
MMR_POOL_MULTIPLIER = 5
MMR_MIN_POOL = 100
PUBLISHED_LIMIT = 20


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _pool_size(limit: int) -> int:
    return max(MMR_MIN_POOL, MMR_POOL_MULTIPLIER * max(1, int(limit)))


def _hybrid_relevance(
    user: AbstractBaseUser,
    *,
    candidate_ids: tuple[object, ...],
    pool_limit: int,
    corpus_version: str | None,
    reference_user_ids: Iterable[object] | None,
    prepared: dict[str, Any] | None,
    tag_profile: dict[str, float] | None,
    should_continue: Callable[[], bool] | None,
) -> tuple[dict[str, Any], dict[str, Any], list[tuple[float, str, dict[str, Any]]]]:
    """Calculate one hybrid relevance pool for both published variants."""

    content = rank_content_v1(
        user,
        "content-cbf-weighted-v1",
        limit=pool_limit,
        _limit_cap=pool_limit,
        corpus_version=corpus_version,
        candidate_ids=set(candidate_ids),
        min_rating_count=None,
        tag_profile=tag_profile,
        prepared=prepared,
        should_continue=should_continue,
    )
    # The collaborative ranker keeps its public 50-result presentation cap.
    # The content side supplies the larger MMR candidate pool; collaborative
    # evidence is still merged whenever it exists for a pool member.
    collaborative = rank_collaborative_user_knn_v1(
        user,
        candidate_ids=candidate_ids,
        limit=min(50, pool_limit),
        corpus_version=corpus_version,
        reference_user_ids=reference_user_ids,
        prepared=prepared,
        should_continue=should_continue,
    )
    content_by_id = {item["work_id"]: item for item in content["results"]}
    collaborative_by_id = {item["work_id"]: item for item in collaborative["results"]}
    ranked: list[tuple[float, str, dict[str, Any]]] = []
    for work_id in sorted(set(content_by_id) | set(collaborative_by_id)):
        content_item = content_by_id.get(work_id)
        collaborative_item = collaborative_by_id.get(work_id)
        content_score = float(content_item["score"]) if content_item else 0.0
        collaborative_score = float(collaborative_item["score"]) if collaborative_item else 0.0
        if collaborative["insufficient_history"]:
            score = content_score
            effective_collaborative_weight = 0.0
        else:
            score = CONTENT_WEIGHT * content_score + COLLABORATIVE_WEIGHT * collaborative_score
            effective_collaborative_weight = COLLABORATIVE_WEIGHT
        base = dict(content_item or collaborative_item)
        base.update(
            {
                "score": round(score, 6),
                "rating_term": round(score, 6),
                "rating_term_is_fallback": bool(
                    content_item and content_item.get("rating_term_is_fallback", False)
                ),
                "signals": {
                    **(base.get("signals") or {}),
                    "hybrid_content_score": round(content_score, 6),
                    "hybrid_collaborative_score": round(collaborative_score, 6),
                    "hybrid_content_weight": CONTENT_WEIGHT,
                    "hybrid_collaborative_weight": effective_collaborative_weight,
                    "hybrid_collaborative_fallback": collaborative_item is None
                    or collaborative["insufficient_history"],
                    "hybrid_relevance_score": round(score, 6),
                },
            }
        )
        ranked.append((score, base["slug"], base))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    return content, collaborative, ranked


def _vectors_for_items(
    items: Iterable[dict[str, Any]],
    *,
    candidate_ids: tuple[object, ...],
    corpus_version: str | None,
    prepared: dict[str, Any] | None,
) -> dict[str, dict[str, float]]:
    """Load the exact fs-v12 vectors used by the shared content ranker."""

    item_list = list(items)
    requested = {str(item["work_id"]) for item in item_list}
    prepared_vectors = (prepared or {}).get("vectors")
    if prepared_vectors is not None:
        return {
            str(work_id): vector
            for work_id, vector in prepared_vectors.items()
            if str(work_id) in requested
        }

    if prepared is not None:
        works = [
            work for work in prepared.get("works", []) if str(work.id) in requested
        ]
    else:
        works = list(
            evaluation_candidate_works(corpus_version)
            .filter(id__in=requested)
            .prefetch_related("curated_labels", "releases__platform", "franchises", "developers")
        )
    availability = coverage_report(corpus_version)
    tag_idf = (prepared or {}).get("tag_idf") or tag_idf_profile(corpus_version)
    return {
        str(work.id): feature_vector(
            work,
            include_franchise=availability["include_franchise"],
            include_developer=availability["include_developer"],
            tag_idf=tag_idf,
            feature_set_version=FEATURE_SET_VERSION,
        )
        for work in works
    }


def _payload(
    *,
    algorithm_id: str,
    content: dict[str, Any],
    collaborative: dict[str, Any],
    results: list[dict[str, Any]],
    parameters: dict[str, Any],
    limitation: str,
) -> dict[str, Any]:
    return {
        "algorithm_id": algorithm_id,
        "generated_at": content["generated_at"],
        "input_snapshot_sha256": _hash_payload(
            {
                "content": content["input_snapshot_sha256"],
                "collaborative": collaborative["input_snapshot_sha256"],
                "algorithm_id": algorithm_id,
                "parameters": parameters,
                "results": [item["work_id"] for item in results],
            }
        ),
        "feature_set_version": FEATURE_SET_VERSION,
        "corpus_version": content.get("corpus_version"),
        "snapshot_sha256": content.get("snapshot_sha256", "")
        or collaborative.get("snapshot_sha256", ""),
        "popscore_snapshot_sha256": content.get("popscore_snapshot_sha256", "")
        or collaborative.get("popscore_snapshot_sha256", ""),
        "parameters": parameters,
        "insufficient_history": content["insufficient_history"],
        "limitation": limitation,
        "results": results,
    }


def rank_hybrid_weighted_cf_v1(
    user: AbstractBaseUser,
    *,
    candidate_ids: Iterable[object],
    limit: int = 20,
    corpus_version: str | None = None,
    reference_user_ids: Iterable[object] | None = None,
    prepared: dict[str, Any] | None = None,
    tag_profile: dict[str, float] | None = None,
    should_continue: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Combine the existing Weighted ranker with user-kNN evidence."""

    candidate_ids = tuple(candidate_ids)
    content, collaborative, ranked = _hybrid_relevance(
        user,
        candidate_ids=candidate_ids,
        pool_limit=50,
        corpus_version=corpus_version,
        reference_user_ids=reference_user_ids,
        prepared=prepared,
        tag_profile=tag_profile,
        should_continue=should_continue,
    )
    bounded_limit = max(1, min(50, int(limit)))
    parameters = {
        "content_algorithm_id": "content-cbf-weighted-v1",
        "collaborative_algorithm_id": COLLABORATIVE_ALGORITHM_ID,
        "content_weight": CONTENT_WEIGHT,
        "collaborative_weight": COLLABORATIVE_WEIGHT,
    }
    return _payload(
        algorithm_id=ALGORITHM_ID,
        content=content,
        collaborative=collaborative,
        results=[item for _score, _slug, item in ranked[:bounded_limit]],
        parameters=parameters,
        limitation=(
            "Hybrid ranking combining the existing Weighted content score with "
            "explicit-rating user-kNN; content ranking is used when the "
            "collaborative neighbourhood is unavailable."
        ),
    )


def rank_hybrid_mmr_v1(
    user: AbstractBaseUser,
    *,
    candidate_ids: Iterable[object],
    limit: int = PUBLISHED_LIMIT,
    corpus_version: str | None = None,
    reference_user_ids: Iterable[object] | None = None,
    prepared: dict[str, Any] | None = None,
    tag_profile: dict[str, float] | None = None,
    should_continue: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Apply fs-v12 MMR to the shared hybrid relevance pool."""

    candidate_ids = tuple(candidate_ids)
    bounded_limit = max(1, min(50, int(limit)))
    pool_limit = _pool_size(bounded_limit)
    content, collaborative, ranked = _hybrid_relevance(
        user,
        candidate_ids=candidate_ids,
        pool_limit=pool_limit,
        corpus_version=corpus_version,
        reference_user_ids=reference_user_ids,
        prepared=prepared,
        tag_profile=tag_profile,
        should_continue=should_continue,
    )
    pool = ranked[:pool_limit]
    vectors = _vectors_for_items(
        (item for _score, _slug, item in pool),
        candidate_ids=candidate_ids,
        corpus_version=corpus_version,
        prepared=prepared,
    )
    results = mmr_rerank(
        pool,
        vectors,
        lambda_value=MMR_LAMBDA,
        should_continue=should_continue,
    )[:bounded_limit]
    parameters = {
        "base_algorithm_id": ALGORITHM_ID,
        "content_algorithm_id": "content-cbf-weighted-v1",
        "collaborative_algorithm_id": COLLABORATIVE_ALGORITHM_ID,
        "content_weight": CONTENT_WEIGHT,
        "collaborative_weight": COLLABORATIVE_WEIGHT,
        "lambda": MMR_LAMBDA,
        "pool_size": pool_limit,
        "pool_rule": "max(100, 5*K)",
        "feature_set_version": FEATURE_SET_VERSION,
        "presentation_limit": PUBLISHED_LIMIT,
    }
    return _payload(
        algorithm_id=MMR_ALGORITHM_ID,
        content=content,
        collaborative=collaborative,
        results=results,
        parameters=parameters,
        limitation=(
            "Hybrid Weighted plus explicit-rating user-kNN relevance is re-ranked "
            "with deterministic MMR over an fs-v12 candidate pool; sparse "
            "collaborative history falls back to Weighted relevance."
        ),
    )
