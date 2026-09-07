"""Request-time ranking for the versioned content recommender."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from catalogue.corpus import governed_works
from catalogue.models import CorpusRatingSnapshot, GameWork
from library.models import LibraryEntry
from recommendations.content.combine import combine, rating_term
from recommendations.content.explain import explain
from recommendations.content.features import FEATURE_SET_VERSION, feature_vector, genre_rating_profile
from recommendations.content.profile import build_profile
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


def _load_candidate_vectors(works: list[GameWork], spec: VariantSpec) -> dict[object, dict[str, float]]:
    work_ids = [work.id for work in works]
    cached = {
        row["work_id"]: row["vector_json"]
        for row in WorkFeatureVector.objects.filter(
            work_id__in=work_ids, feature_set_version=spec.feature_set_version
        ).values("work_id", "vector_json")
    }
    for work in works:
        cached.setdefault(work.id, feature_vector(work, feature_set_version=FEATURE_SET_VERSION))
    return cached


def _base_item(work: GameWork, score: float, evidence: dict) -> dict:
    return {
        "work_id": str(work.id),
        "slug": work.canonical_slug,
        "title": work.title_en or work.original_title,
        "score": round(score, 6),
        "contributions": evidence["contributions"],
        "rating_term": evidence["rating_term"],
        "rating_term_is_fallback": evidence["rating_term_is_fallback"],
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
    profile: dict[str, float],
    results: list[dict],
    *,
    insufficient_history: bool,
    limitation: str,
) -> dict:
    return {
        "algorithm_id": spec.algorithm_id,
        "generated_at": generated_at.isoformat(),
        "input_snapshot_sha256": _fingerprint(profile, results),
        "feature_set_version": spec.feature_set_version,
        "corpus_version": corpus_version,
        "snapshot_sha256": snapshot_sha256,
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
) -> list[dict]:
    genre_profile = genre_rating_profile(corpus_version)
    vectors = _load_candidate_vectors(works, spec)
    scored: list[tuple[float, str, dict]] = []
    for work in works:
        vector = vectors[work.id]
        rt, fallback = rating_term(work, corpus_version, genre_profile)
        evidence = explain(
            vector,
            profile,
            {key: 0.0 for key in vector},
            spec,
            candidate_rating_term=rt,
            rating_term_is_fallback=fallback,
        )
        item = _base_item(work, rt, evidence)
        scored.append((rt, work.canonical_slug, item))
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [item for _score, _slug, item in scored[:limit]]


def rank_content_v1(
    user: AbstractBaseUser,
    algorithm_id: str,
    limit: int | None = _DEFAULT_LIMIT,
    corpus_version: str | None = None,
    generated_at: datetime | None = None,
) -> dict:
    """Rank governed unseen works for the authenticated owner."""

    spec = ALGORITHM_REGISTRY[algorithm_id]
    limit = _clamp_limit(limit)
    generated_at = generated_at or datetime.now(timezone.utc)

    seen_ids = set(LibraryEntry.objects.filter(user=user).values_list("work_id", flat=True))
    history_count = (
        LibraryEntry.objects.filter(user=user, work__genres__isnull=False)
        .values("work_id")
        .distinct()
        .count()
    )
    candidates = list(
        governed_works(corpus_version)
        .exclude(id__in=seen_ids)
        .filter(genres__isnull=False)
        .prefetch_related("genres", "releases__platform")
        .distinct()
    )
    snapshot_sha256 = _snapshot_sha256(corpus_version, {work.id for work in candidates} | seen_ids)
    profile = build_profile(user, corpus_version)

    if history_count < _COLD_START_ENTRIES:
        results = _cold_start_results(candidates, limit, spec, corpus_version, profile)
        return _dto(
            spec,
            generated_at,
            corpus_version,
            snapshot_sha256,
            profile,
            results,
            insufficient_history=True,
            limitation=_COLD_START_LIMITATION,
        )

    genre_profile = genre_rating_profile(corpus_version)
    vectors = _load_candidate_vectors(candidates, spec)
    scored: list[tuple[float, str, dict]] = []
    for work in candidates:
        vector = vectors[work.id]
        similarity = cosine(profile, vector)
        parts = {
            key: profile[key] * vector[key]
            for key in profile.keys() & vector.keys()
        }
        rt, fallback = rating_term(work, corpus_version, genre_profile)
        score = combine(similarity, rt, None, spec)
        evidence = explain(
            vector,
            profile,
            parts,
            spec,
            candidate_rating_term=rt,
            rating_term_is_fallback=fallback,
        )
        item = _base_item(work, score, evidence)
        scored.append((score, work.canonical_slug, item))

    scored.sort(key=lambda row: (-row[0], row[1]))
    results = [item for _score, _slug, item in scored[:limit]]
    return _dto(
        spec,
        generated_at,
        corpus_version,
        snapshot_sha256,
        profile,
        results,
        insufficient_history=False,
        limitation=_LIMITATION,
    )
