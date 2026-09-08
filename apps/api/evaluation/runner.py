"""Reproducible multi-algorithm ranking runner (EVAL-01, EVAL-10)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import DemoAccountIdentity
from catalogue.corpus import evaluation_candidate_works, governed_works
from catalogue.models import CorpusRatingSnapshot, CorpusVersion
from evaluation.candidates import build
from evaluation.metrics import map_at_k, ndcg_at_k, precision_at_k, recall_at_k
from evaluation.protocol import Protocol
from evaluation.splits import user_split
from recommendations.content.features import FEATURE_SET_VERSION, feature_vector, genre_rating_profile
from recommendations.content.rank import rank_content_v1
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.baselines import rank_random_v1
from library.popularity import rank_popularity_v1

K_VALUES = (5, 10, 20)
SYNTHETIC_MARKER = "synthetic-eval-user"


class SnapshotCoverageError(ValueError):
    """Raised when a run cannot be tied to the active immutable snapshot."""


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def snapshot_sha256(corpus_version: str) -> str:
    """Hash every governed snapshot row in one corpus version."""

    work_ids = governed_works(corpus_version).values_list("id", flat=True)
    rows = [
        (str(work_id), version, source, rating, count, retrieved_at.isoformat())
        for work_id, version, source, rating, count, retrieved_at in CorpusRatingSnapshot.objects.filter(
            work_id__in=work_ids, corpus_version=corpus_version
        ).values_list("work_id", "corpus_version", "source", "rating", "rating_count", "retrieved_at")
    ]
    rows.sort()
    return _hash_payload(rows)


def validate_snapshot_coverage(corpus_version: str) -> None:
    """Fail closed on live-rated works that are absent from the active snapshot.

    Unrated governed works are intentionally outside the coverage denominator.
    A stale snapshot for a rated work is reported as version drift rather than
    being silently treated as coverage for the requested corpus.
    """

    if not CorpusVersion.objects.filter(version=corpus_version, is_active=True).exists():
        raise SnapshotCoverageError(
            f"corpus_version {corpus_version!r} is not the active CorpusVersion"
        )

    governed = evaluation_candidate_works(corpus_version)
    rated_ids = set(governed.filter(rating__isnull=False).values_list("id", flat=True))
    if not rated_ids:
        return

    active_rows = list(
        CorpusRatingSnapshot.objects.filter(
            work_id__in=rated_ids, corpus_version=corpus_version
        ).values_list("work_id", "corpus_version")
    )
    active_ids = {work_id for work_id, _version in active_rows}
    if any(version != corpus_version for _work_id, version in active_rows):
        raise SnapshotCoverageError("snapshot corpus_version mismatch with active CorpusVersion")

    missing_ids = rated_ids - active_ids
    if missing_ids:
        stale_versions = set(
            CorpusRatingSnapshot.objects.filter(work_id__in=missing_ids)
            .exclude(corpus_version=corpus_version)
            .values_list("corpus_version", flat=True)
        )
        if stale_versions:
            raise SnapshotCoverageError(
                "snapshot corpus_version mismatch with active CorpusVersion "
                f"(found {sorted(stale_versions)!r}, expected {corpus_version!r})"
            )
        raise SnapshotCoverageError(
            f"missing CorpusRatingSnapshot for {len(missing_ids)} governed live-rated works"
        )


def _code_commit() -> str:
    supplied_commit = os.environ.get("SAVEPOINT_CODE_COMMIT", "").strip()
    if supplied_commit:
        return supplied_commit
    repo_root = Path(settings.BASE_DIR).parent.parent
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _seed_for_user(protocol: Protocol, user_id: object) -> int:
    digest = hashlib.sha256(f"{protocol.loo_seed}:{user_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _random_algorithm(*, user, candidate_ids, protocol, corpus_version, algorithm_id, **_kwargs):
    payload = rank_random_v1(
        user,
        seed=_seed_for_user(protocol, user.pk),
        limit=max(K_VALUES),
        corpus_version=corpus_version,
        candidate_ids=candidate_ids,
    )
    return {"candidate_ids": list(candidate_ids), **payload}


def _popularity_algorithm(*, candidate_ids, algorithm_id, **_kwargs):
    payload = rank_popularity_v1(candidate_ids=candidate_ids, limit=max(K_VALUES))
    return {"candidate_ids": list(candidate_ids), **payload}


def _content_algorithm(*, user, candidate_ids, corpus_version, algorithm_id, **_kwargs):
    payload = rank_content_v1(
        user,
        algorithm_id,
        limit=max(K_VALUES),
        corpus_version=corpus_version,
        candidate_ids=candidate_ids,
        min_rating_count=None,
        genre_profile=_kwargs.get("genre_profile"),
        prepared=_kwargs.get("prepared"),
    )
    return {"candidate_ids": list(candidate_ids), **payload}


def default_algorithms() -> dict[str, Callable[..., Any]]:
    """Return the fixed five-algorithm comparison set."""

    algorithms: dict[str, Callable[..., Any]] = {
        "random-v1": _random_algorithm,
        "popularity-v1": _popularity_algorithm,
    }
    algorithms.update({algorithm_id: _content_algorithm for algorithm_id in ALGORITHM_REGISTRY})
    return algorithms


def _ranked_ids(result: Any) -> tuple[list[str], set[str] | None]:
    declared_candidates: set[str] | None = None
    if isinstance(result, Mapping):
        if "candidate_ids" in result:
            declared_candidates = {str(value) for value in result["candidate_ids"]}
        raw_results = result.get("ranked_ids", result.get("results", []))
        if isinstance(raw_results, Mapping):
            raw_results = raw_results.get("results", [])
        values = [
            item.get("work_id") if isinstance(item, Mapping) else item
            for item in raw_results
        ]
    else:
        values = list(result)
    return [str(value) for value in values if value is not None], declared_candidates


def _average(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {"precision": 0.0, "recall": 0.0, "ndcg": 0.0, "map": 0.0}
    return {
        key: round(math.fsum(row[key] for row in rows) / len(rows), 8)
        for key in ("precision", "recall", "ndcg", "map")
    }


def run(
    protocol: Protocol,
    corpus_version: str,
    algorithms: Mapping[str, Callable[..., Any]] | None = None,
    *,
    split: str = "test",
) -> dict[str, Any]:
    """Run each algorithm against one immutable candidate set per user."""

    if split not in {"train", "validation", "test"}:
        raise ValueError("split must be train, validation, or test")
    validate_snapshot_coverage(corpus_version)
    actual_snapshot_hash = snapshot_sha256(corpus_version)
    if protocol.snapshot_sha256 and protocol.snapshot_sha256 != actual_snapshot_hash:
        raise SnapshotCoverageError("snapshot checksum differs from frozen protocol")

    user_model = get_user_model()
    users = list(
        user_model.objects.filter(
            demo_identity__marker=SYNTHETIC_MARKER,
        ).order_by("id")
    )
    partition = user_split([user.pk for user in users], protocol)
    user_ids = set(getattr(partition, split))
    selected_users = [user for user in users if user.pk in user_ids]
    candidates_by_user: list[tuple[Any, list[Any], Any, str]] = []
    skipped_user_count = 0
    for user in selected_users:
        built = build(user, protocol, corpus_version)
        if built is None:
            skipped_user_count += 1
            continue
        candidate_ids, heldout_id, candidate_hash = built
        candidates_by_user.append((user, list(candidate_ids), heldout_id, candidate_hash))
    if not candidates_by_user:
        raise ValueError(f"no evaluable synthetic users in {split} split")

    algorithm_map = dict(algorithms or default_algorithms())
    algorithm_artifacts: dict[str, Any] = {}
    evaluation_genre_profile = genre_rating_profile(corpus_version)
    evaluation_works = list(
        evaluation_candidate_works(corpus_version)
        .filter(genres__isnull=False)
        .prefetch_related("genres", "releases__platform")
    )
    snapshot_rows = CorpusRatingSnapshot.objects.filter(
        work_id__in=[work.id for work in evaluation_works], rating__isnull=False,
        corpus_version=corpus_version,
    )
    per_work_snapshots: dict[object, list[tuple[float, int]]] = {}
    for work_id, rating, rating_count in snapshot_rows.values_list("work_id", "rating", "rating_count"):
        per_work_snapshots.setdefault(work_id, []).append((rating, rating_count))
    evaluation_snapshot_stats = {
        work_id: (
            math.fsum(rating * count for rating, count in rows) / sum(count for _rating, count in rows)
            if sum(count for _rating, count in rows)
            else math.fsum(rating for rating, _count in rows) / len(rows),
            sum(count for _rating, count in rows),
        )
        for work_id, rows in per_work_snapshots.items()
    }
    evaluation_prepared = {
        "works": evaluation_works,
        "vectors": {
            work.id: feature_vector(work, feature_set_version=FEATURE_SET_VERSION)
            for work in evaluation_works
        },
        "genre_profile": evaluation_genre_profile,
        "snapshot_stats": evaluation_snapshot_stats,
        "snapshot_sha256": actual_snapshot_hash,
    }
    all_manifest_rows = [
        (str(user.pk), str(heldout_id), candidate_hash)
        for user, _candidate_ids, heldout_id, candidate_hash in candidates_by_user
    ]
    split_manifest_hash = _hash_payload(sorted(all_manifest_rows))

    for algorithm_id, algorithm in algorithm_map.items():
        per_user: list[dict[str, Any]] = []
        metric_rows: dict[str, list[dict[str, float]]] = {str(k): [] for k in K_VALUES}
        for user, candidate_ids, heldout_id, candidate_hash in candidates_by_user:
            result = algorithm(
                user=user,
                algorithm_id=algorithm_id,
                candidate_ids=tuple(candidate_ids),
                heldout_work_id=heldout_id,
                protocol=protocol,
                corpus_version=corpus_version,
                genre_profile=evaluation_genre_profile,
                prepared=evaluation_prepared,
            )
            ranked_ids, declared_candidates = _ranked_ids(result)
            if declared_candidates is not None:
                assert declared_candidates == {str(value) for value in candidate_ids}, (
                    f"algorithm {algorithm_id} received a different candidate set"
                )
            candidate_strings = {str(value) for value in candidate_ids}
            assert set(ranked_ids) <= candidate_strings, (
                f"algorithm {algorithm_id} returned an id outside its candidate set"
            )
            relevant = {str(heldout_id)}
            row: dict[str, Any] = {
                "user_id": str(user.pk),
                "heldout_work_id": str(heldout_id),
                "candidate_sha256": candidate_hash,
                "heldout_rank": (
                    ranked_ids.index(str(heldout_id)) + 1
                    if str(heldout_id) in ranked_ids
                    else None
                ),
                "metrics": {},
            }
            for k in K_VALUES:
                metrics = {
                    "precision": precision_at_k(ranked_ids, relevant, k),
                    "recall": recall_at_k(ranked_ids, relevant, k),
                    "ndcg": ndcg_at_k(ranked_ids, relevant, k),
                    "map": map_at_k([ranked_ids], [relevant], k),
                }
                row["metrics"][str(k)] = metrics
                metric_rows[str(k)].append(metrics)
            per_user.append(row)

        aggregates = {k: _average(rows) for k, rows in metric_rows.items()}
        algorithm_artifacts[algorithm_id] = {
            "algorithm_id": algorithm_id,
            "per_user": per_user,
            "aggregates": aggregates,
        }

    return {
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.frozen_hash(),
        "code_commit": _code_commit(),
        "corpus_version": corpus_version,
        "snapshot_sha256": actual_snapshot_hash,
        "feature_set_version": FEATURE_SET_VERSION,
        "seeds": {
            "leave_one_out": protocol.loo_seed,
            "user_split": protocol.user_split_seed,
        },
        "split": split,
        "evaluation_population": {
            "requested_user_count": len(selected_users),
            "evaluated_user_count": len(candidates_by_user),
            "skipped_user_count": skipped_user_count,
            "skipped_reason": "no eligible positive item for leave-one-out",
        },
        "split_manifest_sha256": split_manifest_hash,
        "algorithms": algorithm_artifacts,
        "simulation": True,
        "limitation": protocol.limitation,
    }
