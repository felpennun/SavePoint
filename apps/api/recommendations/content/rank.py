"""Request-time ranking for the versioned content recommender."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timezone
from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from catalogue.corpus import evaluation_candidate_works
from catalogue.models import CorpusRatingSnapshot, GameWork
from catalogue.popularity import normalised_popscore_by_work, popscore_snapshot_sha256
from library.models import LibraryEntry
from recommendations.content.combine import combine, rating_term
from recommendations.content.explain import explain
from recommendations.content.features import (
    FEATURE_SET_VERSION,
    coverage_report,
    feature_vector,
    genre_rating_profile,
    normalise_rating,
    normalise_rating_volume,
)
from recommendations.content.profile import ProfileInputs, build_profile_inputs
from recommendations.content.recency import recency_score
from recommendations.content.similarity import cosine
from recommendations.content.variants import ALGORITHM_REGISTRY, VariantSpec
from recommendations.models import WorkFeatureVector


_MIN_LIMIT = 1
_MAX_LIMIT = 50
_DEFAULT_LIMIT = 20
_COLD_START_ENTRIES = 3
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


def _clamp_limit(limit: int | None) -> int:
    if limit is None:
        return _DEFAULT_LIMIT
    return max(_MIN_LIMIT, min(_MAX_LIMIT, int(limit)))


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _snapshot_sha256(corpus_version: str | None, work_ids: set[object]) -> str:
    snapshots = CorpusRatingSnapshot.objects.filter(work_id__in=work_ids)
    if corpus_version is not None:
        snapshots = snapshots.filter(corpus_version=corpus_version)
    rows = [
        (str(work_id), version, source, rating, count, retrieved_at.isoformat())
        for work_id, version, source, rating, count, retrieved_at in snapshots.values_list(
            "work_id", "corpus_version", "source", "rating", "rating_count", "retrieved_at"
        )
    ]
    rows.sort()
    return _hash_payload(rows)


def _load_candidate_vectors(
    works: list[GameWork],
    spec: VariantSpec,
    corpus_version: str | None,
    prepared_vectors: dict[object, dict[str, float]] | None = None,
) -> dict[object, dict[str, float]]:
    if prepared_vectors is not None:
        return {
            work.id: prepared_vectors[work.id]
            for work in works
            if work.id in prepared_vectors
        }
    availability = coverage_report(corpus_version)
    work_ids = [work.id for work in works]
    cached: dict[object, dict[str, float]] = {}
    if not (availability["include_franchise"] or availability["include_developer"]):
        cached = {
            row["work_id"]: row["vector_json"]
            for row in WorkFeatureVector.objects.filter(
                work_id__in=work_ids, feature_set_version=spec.feature_set_version
            ).values("work_id", "vector_json")
        }
    for work in works:
        cached.setdefault(
            work.id,
            feature_vector(
                work,
                include_franchise=availability["include_franchise"],
                include_developer=availability["include_developer"],
                feature_set_version=FEATURE_SET_VERSION,
            ),
        )
    return cached


def _candidate_signals(
    work: GameWork,
    snapshot_stats: dict[object, tuple[float, int]],
    volume_ceiling: int,
    popscore_by_work: dict[object, float],
    recency_by_work: dict[object, float],
) -> dict:
    """Return only scalar signals backed by the frozen local snapshot."""

    has_snapshot = work.id in snapshot_stats
    rating, rating_count = snapshot_stats.get(work.id, (None, 0))
    return {
        "external_rating": normalise_rating(rating),
        "rating_volume": (
            normalise_rating_volume(rating_count, volume_ceiling) if has_snapshot else None
        ),
        "release_date": work.first_release_date.isoformat() if work.first_release_date else None,
        "recency_score": recency_by_work.get(work.id),
        "popscore": popscore_by_work.get(work.id),
    }


def _recency_by_work(
    works: list[GameWork],
    snapshot_stats: dict[object, tuple[float | None, int]],
    eligibility_cutoff_date: date,
    half_life_days: int,
) -> dict[object, float]:
    return {
        work.id: score
        for work in works
        if (
            score := recency_score(
                work.first_release_date,
                eligibility_cutoff_date=eligibility_cutoff_date,
                has_external_rating=snapshot_stats.get(work.id, (None, 0))[0] is not None,
                half_life_days=half_life_days,
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
    snapshot_stats: dict[object, tuple[float, int]],
    genre_profile: dict[str, float],
    popscore_by_work: dict[object, float],
    recency_by_work: dict[object, float],
) -> list[dict]:
    vectors = _load_candidate_vectors(works, spec, corpus_version)
    volume_ceiling = max((count for _rating, count in snapshot_stats.values()), default=0)
    scored: list[tuple[float, str, dict]] = []
    for work in works:
        vector = vectors[work.id]
        rt, fallback = rating_term(work, corpus_version, genre_profile, snapshot_stats)
        evidence = explain(
            vector,
            profile,
            {key: 0.0 for key in vector},
            spec,
            candidate_rating_term=rt,
            rating_term_is_fallback=fallback,
        )
        score = combine(
            0.0,
            rt,
            None,
            spec,
            recency_score=recency_by_work.get(work.id),
        )
        item = _base_item(
            work,
            score,
            evidence,
            _candidate_signals(
                work, snapshot_stats, volume_ceiling, popscore_by_work, recency_by_work
            ),
        )
        scored.append((score, work.canonical_slug, item))
    scored.sort(key=lambda row: (-row[0], row[1]))
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
    genre_profile: dict[str, float] | None = None,
    prepared: dict[str, Any] | None = None,
) -> dict:
    """Rank governed unseen works for the authenticated owner."""

    spec = ALGORITHM_REGISTRY[algorithm_id]
    limit = _clamp_limit(limit)
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
            candidate_query.filter(genres__isnull=False)
            .prefetch_related("genres", "releases__platform", "franchises", "developers")
            .distinct()
        )
        snapshot_sha256 = _snapshot_sha256(corpus_version, {work.id for work in candidates} | seen_ids)
    profile_inputs = build_profile_inputs(user, corpus_version)
    profile = profile_inputs.positive
    resolved_genre_profile = (
        genre_profile
        if genre_profile is not None
        else (prepared.get("genre_profile") if prepared is not None else None)
    ) or genre_rating_profile(corpus_version)
    if prepared is not None and "snapshot_stats" in prepared:
        snapshot_stats = prepared["snapshot_stats"]
    else:
        snapshot_rows = CorpusRatingSnapshot.objects.filter(
            work_id__in=[work.id for work in candidates], rating__isnull=False
        )
        if corpus_version is not None:
            snapshot_rows = snapshot_rows.filter(corpus_version=corpus_version)
        per_work_snapshots: dict[object, list[tuple[float, int]]] = {}
        for work_id, rating, rating_count in snapshot_rows.values_list("work_id", "rating", "rating_count"):
            per_work_snapshots.setdefault(work_id, []).append((rating, rating_count))
        snapshot_stats = {
            work_id: (
                math.fsum(rating * count for rating, count in rows) / sum(count for _rating, count in rows)
                if sum(count for _rating, count in rows)
                else math.fsum(rating for rating, _count in rows) / len(rows),
                sum(count for _rating, count in rows),
            )
            for work_id, rows in per_work_snapshots.items()
        }

    if profile_inputs.positive_entry_count < _COLD_START_ENTRIES or not profile:
        popscore_by_work = normalised_popscore_by_work(
            corpus_version, [work.id for work in candidates]
        )
        recency_by_work = _recency_by_work(
            candidates,
            snapshot_stats,
            eligibility_cutoff_date,
            int(spec.params.get("half_life_days", 365)),
        )
        results = _cold_start_results(
            candidates,
            limit,
            spec,
            corpus_version,
            profile,
            snapshot_stats,
            resolved_genre_profile,
            popscore_by_work,
            recency_by_work,
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
        spec,
        corpus_version,
        prepared_vectors=(prepared or {}).get("vectors"),
    )
    volume_ceiling = max((count for _rating, count in snapshot_stats.values()), default=0)
    popscore_by_work = normalised_popscore_by_work(corpus_version, [work.id for work in candidates])
    recency_by_work = _recency_by_work(
        candidates,
        snapshot_stats,
        eligibility_cutoff_date,
        int(spec.params.get("half_life_days", 365)),
    )
    scored: list[tuple[float, str, dict]] = []
    for work in candidates:
        vector = vectors[work.id]
        similarity = cosine(profile, vector)
        parts = {
            key: profile[key] * vector[key]
            for key in profile.keys() & vector.keys()
        }
        rt, fallback = rating_term(work, corpus_version, resolved_genre_profile, snapshot_stats)
        negative_similarity = cosine(profile_inputs.negative, vector)
        score = combine(
            similarity,
            rt,
            None,
            spec,
            negative_similarity=negative_similarity,
            recency_score=recency_by_work.get(work.id),
        )
        evidence = explain(
            vector,
            profile,
            parts,
            spec,
            candidate_rating_term=rt,
            rating_term_is_fallback=fallback,
            negative_similarity=negative_similarity,
        )
        item = _base_item(
            work,
            score,
            evidence,
            _candidate_signals(
                work, snapshot_stats, volume_ceiling, popscore_by_work, recency_by_work
            ),
        )
        scored.append((score, work.canonical_slug, item))

    scored.sort(key=lambda row: (-row[0], row[1]))
    results = [item for _score, _slug, item in scored[:limit]]
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
