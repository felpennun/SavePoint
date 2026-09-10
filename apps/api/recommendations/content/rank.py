"""Request-time ranking for the versioned content recommender."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timezone
from typing import Any, Callable

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Exists, OuterRef

from catalogue.corpus import evaluation_candidate_works
from catalogue.models import CorpusRatingSnapshot, GameWork
from catalogue.popularity import normalised_popscore_by_work, popscore_snapshot_sha256
from library.models import LibraryEntry
from recommendations.content.combine import combine, rating_term
from recommendations.cancellation import RecommendationComputationCancelled
from recommendations.content.diversity import mmr_rerank
from recommendations.content.explain import explain
from recommendations.content.features import (
    bayesian_rating,
    FEATURE_SET_VERSION,
    corpus_rating_prior,
    coverage_report,
    feature_vector,
    tag_rating_profile,
    normalise_rating,
    normalise_rating_volume,
    rating_bayesian_normalized,
    rating_confidence,
    rating_final,
    rating_quality,
    tag_idf_profile,
)
from recommendations.content.profile import ProfileInputs, build_profile_inputs
from recommendations.content.recency import recency_score
from recommendations.content.similarity import facet_similarity
from recommendations.content.variants import ALGORITHM_REGISTRY, VariantSpec
from recommendations.models import WorkFeatureVector


_MIN_LIMIT = 1
_MAX_LIMIT = 50
_DEFAULT_LIMIT = 20
_COLD_START_ENTRIES = 3
_CANCELLATION_CHECK_INTERVAL = 128
_MMR_POOL_MULTIPLIER = 5
_MMR_MIN_POOL = 100
_LIMITATION = (
    "Deterministic content-based ranking over the frozen corpus and external "
    "rating snapshot. It is offline simulation evidence, not evidence about "
    "real SavePoint users. Excludes every work already present in the signed-in "
    "user's library."
)
_COLD_START_LIMITATION = (
    "Insufficient genre history for a personalised content profile; results "
    "fall back to globally popular governed genres. This is offline simulation "
    "evidence, not evidence about real SavePoint users."
)


def _clamp_limit(limit: int | None, maximum: int = _MAX_LIMIT) -> int:
    if limit is None:
        return _DEFAULT_LIMIT
    return max(_MIN_LIMIT, min(maximum, int(limit)))


def _base_spec(spec: VariantSpec) -> VariantSpec:
    if spec.combine_mode != "mmr":
        return spec
    base_algorithm_id = spec.params.get("base_algorithm_id")
    if not isinstance(base_algorithm_id, str) or base_algorithm_id not in ALGORITHM_REGISTRY:
        raise ValueError(f"Invalid MMR base algorithm for {spec.algorithm_id}")
    return ALGORITHM_REGISTRY[base_algorithm_id]


def _ensure_current(should_continue: Callable[[], bool] | None) -> None:
    if should_continue is not None and not should_continue():
        raise RecommendationComputationCancelled


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _snapshot_sha256(corpus_version: str | None, work_ids: set[object]) -> str:
    snapshots = CorpusRatingSnapshot.objects.filter(work_id__in=work_ids)
    if corpus_version is not None:
        snapshots = snapshots.filter(corpus_version=corpus_version)
    rows = [
        (str(work_id), version, source, rating, count, total_count, retrieved_at.isoformat())
        for work_id, version, source, rating, count, total_count, retrieved_at in snapshots.values_list(
            "work_id", "corpus_version", "source", "rating", "rating_count",
            "total_rating_count", "retrieved_at"
        )
    ]
    rows.sort()
    return _hash_payload(rows)


def _load_candidate_vectors(
    works: list[GameWork],
    spec: VariantSpec,
    corpus_version: str | None,
    prepared_vectors: dict[object, dict[str, float]] | None = None,
    tag_idf: dict[str, float] | None = None,
    should_continue: Callable[[], bool] | None = None,
) -> dict[object, dict[str, float]]:
    if prepared_vectors is not None:
        return {
            work.id: prepared_vectors[work.id]
            for work in works
            if work.id in prepared_vectors
        }
    availability = coverage_report(corpus_version)
    work_ids = [work.id for work in works]
    cached: dict[object, dict[str, float]] = {
        row["work_id"]: row["vector_json"]
        for row in WorkFeatureVector.objects.filter(
            work_id__in=work_ids, feature_set_version=spec.feature_set_version
        ).values("work_id", "vector_json")
    }
    missing_work_map = {
        work.id: work
        for work in GameWork.objects.filter(id__in=[work_id for work_id in work_ids if work_id not in cached])
        .prefetch_related("curated_labels", "releases__platform", "franchises", "developers")
    }
    for index, work in enumerate(works):
        if index % _CANCELLATION_CHECK_INTERVAL == 0:
            _ensure_current(should_continue)
        if work.id in cached:
            continue
        source_work = missing_work_map.get(work.id, work)
        cached[work.id] = feature_vector(
            source_work,
            include_franchise=availability["include_franchise"],
            include_developer=availability["include_developer"],
            tag_idf=tag_idf,
            feature_set_version=FEATURE_SET_VERSION,
        )
    return cached


def _candidate_signals(
    work: GameWork,
    snapshot_stats: dict[object, tuple[float | None, int, int | None]],
    volume_ceiling: int,
    popscore_by_work: dict[object, float],
    recency_by_work: dict[object, float],
    rating_prior: float | None,
) -> dict:
    """Return only scalar signals backed by the frozen local snapshot."""

    has_snapshot = work.id in snapshot_stats
    rating, _rating_count, total_rating_count = snapshot_stats.get(work.id, (None, 0, None))
    bayesian_adjusted = bayesian_rating(rating, total_rating_count, rating_prior)
    bayesian_normalized = rating_bayesian_normalized(
        rating, total_rating_count, rating_prior
    )
    quality = rating_quality(bayesian_normalized)
    confidence = (
        rating_confidence(total_rating_count) if rating is not None else None
    )
    return {
        "external_rating": normalise_rating(rating),
        "bayesian_rating": bayesian_adjusted,
        "rating_bayesian_normalized": bayesian_normalized,
        "rating_quality": quality,
        "rating_confidence": confidence,
        "rating_final": rating_final(bayesian_normalized, total_rating_count),
        "rating_volume": (
            normalise_rating_volume(total_rating_count, volume_ceiling) if has_snapshot else None
        ),
        "release_date": work.first_release_date.isoformat() if work.first_release_date else None,
        "recency_score": recency_by_work.get(work.id),
        "popscore": popscore_by_work.get(work.id),
    }


def _scored_signals(
    spec: VariantSpec,
    work: GameWork,
    snapshot_stats: dict[object, tuple[float | None, int, int | None]],
    volume_ceiling: int,
    popscore_by_work: dict[object, float],
    recency_by_work: dict[object, float],
    rating_term_value: float,
    rating_prior: float | None,
) -> dict:
    signals = _candidate_signals(
        work,
        snapshot_stats,
        volume_ceiling,
        popscore_by_work,
        recency_by_work,
        rating_prior,
    )
    missing_popscore_floor = spec.params.get("popscore_missing_floor")
    signals["popscore_imputed"] = False
    if signals["popscore"] is None and missing_popscore_floor is not None:
        signals["popscore"] = max(0.0, min(1.0, float(missing_popscore_floor)))
        signals["popscore_imputed"] = True
    # ``rating_term_value`` is the exact final signal used by the combination.
    # Preserve the observed confidence above and expose the fallback term as a
    # separate field instead of pretending a genre fallback has IGDB volume.
    signals["rating_term"] = rating_term_value
    signals["rating_final"] = signals["rating_final"] or rating_term_value
    signals["rating_term_is_fallback"] = signals["rating_bayesian_normalized"] is None
    return signals


def _recency_by_work(
    works: list[GameWork],
    snapshot_stats: dict[object, tuple[float | None, int, int | None]],
    eligibility_cutoff_date: date,
    year_decay: float,
) -> dict[object, float]:
    return {
        work.id: score
        for work in works
        if (
            score := recency_score(
                work.first_release_date,
                eligibility_cutoff_date=eligibility_cutoff_date,
                has_external_rating=snapshot_stats.get(work.id, (None, 0, None))[0] is not None,
                year_decay=year_decay,
            )
        ) is not None
    }


def _base_item(work: GameWork, score: float, evidence: dict, signals: dict) -> dict:
    return {
        "work_id": str(work.id),
        "slug": work.canonical_slug,
        "title": work.title_en or work.original_title,
        "score": round(score, 6),
        "contributions": evidence["contributions"],
        "rating_term": evidence["rating_term"],
        "rating_term_is_fallback": evidence["rating_term_is_fallback"],
        "reason_signals": evidence["reason_signals"],
        "negative_similarity": evidence["negative_similarity"],
        "signals": signals,
    }


def _fingerprint(profile: dict[str, float], results: list[dict]) -> str:
    return _hash_payload(
        {
            "profile": sorted((key, round(value, 9)) for key, value in profile.items()),
            "results": [
                (
                    item["slug"],
                    item["score"],
                    item["rating_term"],
                    item["rating_term_is_fallback"],
                    item["negative_similarity"],
                    item["signals"],
                )
                for item in results
            ],
        }
    )

def _dto(
    spec: VariantSpec,
    generated_at: datetime,
    corpus_version: str | None,
    snapshot_sha256: str,
    popscore_snapshot_sha256: str | None,
    profile_inputs: ProfileInputs,
    results: list[dict],
    *,
    insufficient_history: bool,
    limitation: str,
) -> dict:
    return {
        "algorithm_id": spec.algorithm_id,
        "generated_at": generated_at.isoformat(),
        "input_snapshot_sha256": _fingerprint(profile_inputs.positive, results),
        "feature_set_version": spec.feature_set_version,
        "corpus_version": corpus_version,
        "snapshot_sha256": snapshot_sha256,
        "popscore_snapshot_sha256": popscore_snapshot_sha256,
        "parameters": spec.params,
        "profile_inputs": profile_inputs.as_dict(),
        "signal_availability": coverage_report(corpus_version),
        "insufficient_history": insufficient_history,
        "limitation": limitation,
        "results": results,
    }


def _cold_start_results(
    works: list[GameWork],
    limit: int,
    spec: VariantSpec,
    corpus_version: str | None,
    profile: dict[str, float],
    snapshot_stats: dict[object, tuple[float | None, int, int | None]],
    tag_profile: dict[str, float],
    popscore_by_work: dict[object, float],
    recency_by_work: dict[object, float],
    rating_prior: float | None,
    tag_idf: dict[str, float],
    should_continue: Callable[[], bool] | None,
) -> list[dict]:
    base_spec = _base_spec(spec)
    vectors = _load_candidate_vectors(
        works,
        base_spec,
        corpus_version,
        tag_idf=tag_idf,
        should_continue=should_continue,
    )
    volume_ceiling = max(
        (total_count or 0 for _rating, _count, total_count in snapshot_stats.values()),
        default=0,
    )
    scored: list[tuple[float, str, dict]] = []
    for index, work in enumerate(works):
        if index % _CANCELLATION_CHECK_INTERVAL == 0:
            _ensure_current(should_continue)
        vector = vectors[work.id]
        rt, fallback = rating_term(
            work,
            corpus_version,
            tag_profile,
            snapshot_stats,
            rating_prior,
        )
        signals = _scored_signals(
            base_spec,
            work,
            snapshot_stats,
            volume_ceiling,
            popscore_by_work,
            recency_by_work,
            rt,
            rating_prior,
        )
        similarity_evidence = facet_similarity(profile, vector)
        evidence = explain(
            vector,
            profile,
            similarity_evidence["parts"],
            base_spec,
            candidate_rating_term=signals["rating_final"] or 0.0,
            rating_term_is_fallback=fallback,
        )
        score = combine(
            0.0,
            rt,
            None,
            base_spec,
            recency_score=recency_by_work.get(work.id),
            rating_volume=signals["rating_volume"],
            popscore=signals["popscore"],
        )
        item = _base_item(
            work,
            score,
            evidence,
            signals,
        )
        scored.append((score, work.canonical_slug, item))
    scored.sort(key=lambda row: (-row[0], row[1]))
    if spec.combine_mode == "mmr":
        return mmr_rerank(
            scored[: max(limit * _MMR_POOL_MULTIPLIER, _MMR_MIN_POOL)],
            vectors,
            lambda_value=float(spec.params.get("lambda", 0.80)),
            should_continue=should_continue,
        )[:limit]
    return [item for _score, _slug, item in scored[:limit]]


def rank_content_v1(
    user: AbstractBaseUser,
    algorithm_id: str,
    limit: int | None = _DEFAULT_LIMIT,
    corpus_version: str | None = None,
    candidate_ids: set[object] | tuple[object, ...] | None = None,
    generated_at: datetime | None = None,
    eligibility_cutoff_date: date | None = None,
    min_rating_count: int | None = None,
    tag_profile: dict[str, float] | None = None,
    tag_idf: dict[str, float] | None = None,
    prepared: dict[str, Any] | None = None,
    should_continue: Callable[[], bool] | None = None,
    _limit_cap: int | None = None,
) -> dict:
    """Rank governed unseen works for the authenticated owner."""

    spec = ALGORITHM_REGISTRY[algorithm_id]
    base_spec = _base_spec(spec)
    _ensure_current(should_continue)
    limit = _clamp_limit(limit, _limit_cap or _MAX_LIMIT)
    generated_at = generated_at or datetime.now(timezone.utc)
    eligibility_cutoff_date = eligibility_cutoff_date or generated_at.date()
    seen_ids = set(LibraryEntry.objects.filter(user=user).values_list("work_id", flat=True))
    requested_ids = set(candidate_ids) if candidate_ids is not None else None
    if prepared is not None:
        candidates = [
            work
            for work in prepared["works"]
            if requested_ids is None or work.id in requested_ids
        ]
        snapshot_sha256 = prepared.get("snapshot_sha256", "")
    else:
        candidate_query = evaluation_candidate_works(corpus_version)
        if requested_ids is not None:
            candidate_query = candidate_query.filter(id__in=requested_ids)
        else:
            candidate_query = candidate_query.exclude(id__in=seen_ids)
        candidates = list(
            candidate_query.filter(
                Exists(GameWork.objects.filter(pk=OuterRef("pk"), curated_labels__isnull=False))
            )
        )
        snapshot_sha256 = _snapshot_sha256(corpus_version, {work.id for work in candidates} | seen_ids)
    _ensure_current(should_continue)
    resolved_tag_idf = (
        tag_idf
        if tag_idf is not None
        else (prepared.get("tag_idf") if prepared is not None else None)
    ) or tag_idf_profile(corpus_version)
    profile_inputs = build_profile_inputs(user, corpus_version, resolved_tag_idf)
    profile = profile_inputs.positive
    resolved_tag_profile = (
        tag_profile
        if tag_profile is not None
        else (prepared.get("tag_profile") if prepared is not None else None)
    ) or tag_rating_profile(corpus_version)
    if prepared is not None and "snapshot_stats" in prepared:
        snapshot_stats = prepared["snapshot_stats"]
    else:
        snapshot_rows = CorpusRatingSnapshot.objects.filter(
            work_id__in=[work.id for work in candidates], rating__isnull=False
        )
        if corpus_version is not None:
            snapshot_rows = snapshot_rows.filter(corpus_version=corpus_version)
        per_work_snapshots: dict[object, list[tuple[float | None, int, int | None]]] = {}
        for work_id, rating, rating_count, total_rating_count in snapshot_rows.values_list(
            "work_id", "rating", "rating_count", "total_rating_count"
        ):
            per_work_snapshots.setdefault(work_id, []).append(
                (rating, rating_count, total_rating_count)
            )
        snapshot_stats = {
            work_id: (
                (
                    math.fsum(rating * count for rating, count, _total_count in rows if rating is not None)
                    / sum(count for rating, count, _total_count in rows if rating is not None)
                    if sum(_count for rating, _count, _total_count in rows if rating is not None)
                    else None
                ),
                sum(count for _rating, count, _total_count in rows),
                max(
                    (total_count for _rating, _count, total_count in rows if total_count is not None),
                    default=None,
                ),
            )
            for work_id, rows in per_work_snapshots.items()
        }

    rating_prior = (
        prepared.get("rating_prior") if prepared is not None else None
    ) or corpus_rating_prior(
        corpus_version,
        eligibility_cutoff_date=eligibility_cutoff_date,
    )

    if profile_inputs.positive_entry_count < _COLD_START_ENTRIES or not profile:
        popscore_by_work = normalised_popscore_by_work(
            corpus_version, [work.id for work in candidates]
        )
        recency_by_work = _recency_by_work(
            candidates,
            snapshot_stats,
            eligibility_cutoff_date,
            float(spec.params.get("year_decay", 0.35)),
        )
        results = _cold_start_results(
            candidates,
            limit,
            spec,
            corpus_version,
            profile,
            snapshot_stats,
            resolved_tag_profile,
            popscore_by_work,
            recency_by_work,
            rating_prior,
            resolved_tag_idf,
            should_continue,
        )
        return _dto(
            spec,
            generated_at,
            corpus_version,
            snapshot_sha256,
            popscore_snapshot_sha256(corpus_version),
            profile_inputs,
            results,
            insufficient_history=True,
            limitation=_COLD_START_LIMITATION,
        )

    vectors = _load_candidate_vectors(
        candidates,
        base_spec,
        corpus_version,
        prepared_vectors=(prepared or {}).get("vectors"),
        tag_idf=resolved_tag_idf,
        should_continue=should_continue,
    )
    volume_ceiling = max(
        (total_count or 0 for _rating, _count, total_count in snapshot_stats.values()),
        default=0,
    )
    popscore_by_work = normalised_popscore_by_work(corpus_version, [work.id for work in candidates])
    recency_by_work = _recency_by_work(
        candidates,
        snapshot_stats,
        eligibility_cutoff_date,
        float(spec.params.get("year_decay", 0.35)),
    )
    scored: list[tuple[float, str, dict]] = []
    for index, work in enumerate(candidates):
        if index % _CANCELLATION_CHECK_INTERVAL == 0:
            _ensure_current(should_continue)
        vector = vectors[work.id]
        similarity_evidence = facet_similarity(profile, vector)
        similarity = similarity_evidence["score"]
        parts = similarity_evidence["parts"]
        rt, fallback = rating_term(
            work,
            corpus_version,
            resolved_tag_profile,
            snapshot_stats,
            rating_prior,
        )
        signals = _scored_signals(
            base_spec,
            work,
            snapshot_stats,
            volume_ceiling,
            popscore_by_work,
            recency_by_work,
            rt,
            rating_prior,
        )
        negative_similarity = facet_similarity(profile_inputs.negative, vector)["score"]
        score = combine(
            similarity,
            rt,
            None,
            base_spec,
            negative_similarity=negative_similarity,
            recency_score=recency_by_work.get(work.id),
            rating_volume=signals["rating_volume"],
            popscore=signals["popscore"],
        )
        evidence = explain(
            vector,
            profile,
            parts,
            spec,
            candidate_rating_term=signals["rating_final"] or 0.0,
            rating_term_is_fallback=fallback,
            negative_similarity=negative_similarity,
        )
        item = _base_item(
            work,
            score,
            evidence,
            signals,
        )
        scored.append((score, work.canonical_slug, item))

    scored.sort(key=lambda row: (-row[0], row[1]))
    results = (
        mmr_rerank(
            scored[: max(limit * _MMR_POOL_MULTIPLIER, _MMR_MIN_POOL)],
            vectors,
            lambda_value=float(spec.params.get("lambda", 0.80)),
            should_continue=should_continue,
        )[:limit]
        if spec.combine_mode == "mmr"
        else [item for _score, _slug, item in scored[:limit]]
    )
    return _dto(
        spec,
        generated_at,
        corpus_version,
        snapshot_sha256,
        popscore_snapshot_sha256(corpus_version),
        profile_inputs,
        results,
        insufficient_history=False,
        limitation=_LIMITATION,
    )
