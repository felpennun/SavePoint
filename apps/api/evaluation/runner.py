"""Reproducible multi-algorithm ranking runner (EVAL-01, EVAL-10)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef

from accounts.models import DemoAccountIdentity
from catalogue.corpus import evaluation_candidate_works, governed_works
from catalogue.models import CorpusRatingSnapshot, CorpusVersion, GameWork
from catalogue.popularity import popscore_snapshot_sha256
from evaluation.candidates import build
from evaluation.metrics import (
    catalogue_coverage_at_k,
    concentration_hhi_at_k,
    intra_list_diversity,
    map_at_k,
    ndcg_at_k,
    novelty_at_k,
    precision_at_k,
    prediction_coverage_at_k,
    recall_at_k,
)
from evaluation.protocol import Protocol
from evaluation.splits import user_split
from evaluation.statistics import StatisticsConfig, compare_paired_algorithms
from recommendations.content.features import (
    FEATURE_SET_VERSION,
    all_family_idf_profiles,
    coverage_report,
    corpus_rating_prior,
    feature_vector,
    tag_rating_profile,
)
from recommendations.content.rank import rank_content_v1
from recommendations.collaborative import rank_collaborative_user_knn_v1
from recommendations.hybrid import rank_hybrid_mmr_v1, rank_hybrid_weighted_cf_v1
from recommendations.published import CONTENT_ALGORITHM_IDS
from recommendations.models import WorkFeatureVector
from recommendations.baselines import rank_random_v1
from library.popularity import rank_popularity_v1
from library.models import LibraryEntry

K_VALUES = (5, 10, 20)
SYNTHETIC_MARKER = "synthetic-eval-user"


class SnapshotCoverageError(ValueError):
    """Raised when a run cannot be tied to the active immutable snapshot."""


def validate_active_population(users: list[Any], protocol: Protocol, corpus_version: str) -> dict[str, int]:
    """Fail closed when the active Phase 3 population or split is incomplete."""

    expected_population = protocol.raw.get("synthetic_population", {}).get("phase_3_population")
    split_total = sum(int(protocol.user_split[key]) for key in ("train", "validation", "test"))
    # Fixture protocols may deliberately use a different corpus and population;
    # the frozen production contract is checked only against its own corpus.
    if protocol.corpus_version == corpus_version:
        if expected_population is not None and len(users) != int(expected_population):
            raise ValueError(
                f"active synthetic population expects {expected_population} users; got {len(users)}"
            )
        if split_total != len(users):
            raise ValueError(
                f"user_split totals {split_total} users but active population has {len(users)}"
            )
    return {
        "active_user_count": len(users),
        "expected_user_count": int(expected_population or len(users)),
        "split_total": split_total,
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def snapshot_sha256(corpus_version: str) -> str:
    """Hash every governed snapshot row in one corpus version."""

    work_ids = evaluation_candidate_works(corpus_version).values_list("id", flat=True)
    rows = [
        (str(work_id), version, source, rating, count, total_count, retrieved_at.isoformat())
        for work_id, version, source, rating, count, total_count, retrieved_at in CorpusRatingSnapshot.objects.filter(
            work_id__in=work_ids, corpus_version=corpus_version
        ).values_list(
            "work_id", "corpus_version", "source", "rating", "rating_count",
            "total_rating_count", "retrieved_at"
        )
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
        tag_profile=_kwargs.get("tag_profile"),
        prepared=_kwargs.get("prepared"),
    )
    return {"candidate_ids": list(candidate_ids), **payload}


def _collaborative_algorithm(*, user, candidate_ids, corpus_version, **kwargs):
    payload = rank_collaborative_user_knn_v1(
        user,
        candidate_ids=candidate_ids,
        limit=max(K_VALUES),
        corpus_version=corpus_version,
        reference_user_ids=kwargs.get("prepared", {}).get("training_user_ids", ()),
        prepared=kwargs.get("prepared"),
    )
    return {"candidate_ids": list(candidate_ids), **payload}


def _hybrid_algorithm(*, user, candidate_ids, corpus_version, **kwargs):
    payload = rank_hybrid_weighted_cf_v1(
        user,
        candidate_ids=candidate_ids,
        limit=max(K_VALUES),
        corpus_version=corpus_version,
        reference_user_ids=kwargs.get("prepared", {}).get("training_user_ids", ()),
        prepared=kwargs.get("prepared"),
        tag_profile=kwargs.get("tag_profile"),
    )
    return {"candidate_ids": list(candidate_ids), **payload}


def _hybrid_mmr_algorithm(*, user, candidate_ids, corpus_version, **kwargs):
    payload = rank_hybrid_mmr_v1(
        user,
        candidate_ids=candidate_ids,
        limit=max(K_VALUES),
        corpus_version=corpus_version,
        reference_user_ids=kwargs.get("prepared", {}).get("training_user_ids", ()),
        prepared=kwargs.get("prepared"),
        tag_profile=kwargs.get("tag_profile"),
    )
    return {"candidate_ids": list(candidate_ids), **payload}


def default_algorithms() -> dict[str, Callable[..., Any]]:
    """Return the fixed baseline and published content-variant comparison set."""

    algorithms: dict[str, Callable[..., Any]] = {
        "random-v1": _random_algorithm,
        "popularity-v1": _popularity_algorithm,
    }
    # These three need their own callables, not _content_algorithm, and are
    # appended below in the exact order the frozen protocol declares them
    # (protocol.tuning.evaluation_algorithms), which run_evaluation_parallel
    # checks position by position.
    non_content = {"cf-user-knn-v1", "hybrid-weighted-cf-v1", "hybrid-mmr-v1"}
    algorithms.update({
        algorithm_id: _content_algorithm
        for algorithm_id in CONTENT_ALGORITHM_IDS
        if algorithm_id not in non_content
    })
    algorithms["cf-user-knn-v1"] = _collaborative_algorithm
    algorithms["hybrid-weighted-cf-v1"] = _hybrid_algorithm
    algorithms["hybrid-mmr-v1"] = _hybrid_mmr_algorithm
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


def _mean_applicable(values: list[float | None]) -> tuple[float | None, int]:
    """Return a mean only for observed values, retaining the denominator."""

    observed = [value for value in values if value is not None]
    if not observed:
        return None, 0
    return math.fsum(observed) / len(observed), len(observed)


def _headline_statistical_comparison(
    protocol: Protocol, algorithm_artifacts: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare the frozen headline metric without using it for tuning."""

    try:
        metric_name, k_value = protocol.headline.rsplit("@", 1)
        k_key = str(int(k_value))
    except (AttributeError, ValueError):
        return {
            "valid": False,
            "estimable": False,
            "method": "statistics-v1",
            "warnings": [f"invalid headline metric: {protocol.headline!r}"],
        }

    observations = {
        algorithm_id: {
            row["user_id"]: float(row["metrics"][k_key][metric_name])
            for row in artifact["per_user"]
        }
        for algorithm_id, artifact in algorithm_artifacts.items()
    }
    if len(observations) < 2:
        config = StatisticsConfig(seed=protocol.loo_seed)
        return {
            "valid": False,
            "estimable": False,
            "statistics_version": "statistics-v1",
            "family": protocol.headline,
            "configuration": config.as_dict(),
            "algorithm_order": sorted(observations),
            "user_count": 0,
            "warnings": ["at least two algorithms are required for comparison"],
        }
    return compare_paired_algorithms(
        observations,
        config=StatisticsConfig(seed=protocol.loo_seed),
        family=protocol.headline,
    )


def _training_item_probabilities(user_ids: set[object]) -> dict[str, float]:
    """Freeze novelty frequencies from training users only, never the test split."""

    if not user_ids:
        return {}
    counts: dict[str, int] = {}
    for work_id in LibraryEntry.objects.filter(user_id__in=user_ids).values_list("work_id", flat=True):
        key = str(work_id)
        counts[key] = counts.get(key, 0) + 1
    total = sum(counts.values())
    return {work_id: count / total for work_id, count in counts.items()} if total else {}


def _prepared_candidate_vectors(
    works: Sequence[Any],
    signal_availability: Mapping[str, Any],
    family_idf: Mapping[str, Mapping[str, float]],
) -> dict[object, dict[str, float]]:
    """Load candidate feature vectors, preferring the shared ``WorkFeatureVector`` cache.

    This mirrors ``recommendations.content.rank._load_candidate_vectors``: the
    cache rows are the output of ``feature_vector()`` for ``FEATURE_SET_VERSION``
    (materialised by ``rebuild_feature_vectors``), so reading them here avoids
    recomputing every candidate vector once per algorithm without changing any
    scored value. Any work absent from the cache falls back to a direct compute
    with the same arguments the cache builder uses.
    """

    work_ids = [work.id for work in works]
    vectors: dict[object, dict[str, float]] = {
        row["work_id"]: row["vector_json"]
        for row in WorkFeatureVector.objects.filter(
            work_id__in=work_ids, feature_set_version=FEATURE_SET_VERSION
        ).values("work_id", "vector_json")
    }
    for work in works:
        if work.id in vectors:
            continue
        vectors[work.id] = feature_vector(
            work,
            include_franchise=signal_availability["include_franchise"],
            include_developer=signal_availability["include_developer"],
            tag_idf=family_idf.get("tag"),
            theme_idf=family_idf.get("theme"),
            mode_idf=family_idf.get("mode"),
            feature_idf=family_idf.get("feature"),
            platform_idf=family_idf.get("platform"),
            feature_set_version=FEATURE_SET_VERSION,
        )
    return vectors


def build_evaluation_context(
    protocol: Protocol,
    corpus_version: str,
    split: str = "test",
) -> dict[str, Any]:
    """Build everything one evaluation run needs, independent of which algorithm scores it.

    Split out of ``run()`` (2026-09-11) so a parallel caller can build this
    once in the parent process and let every algorithm worker reuse it,
    instead of every worker process rebuilding the same candidate sets and
    corpus-wide signals from scratch. Pair with
    ``precompute_shared_content_signals`` to also share the O(candidates x
    users) content loop itself -- see ``run_evaluation_parallel``.
    """

    if split not in {"train", "validation", "test"}:
        raise ValueError("split must be train, validation, or test")
    validate_snapshot_coverage(corpus_version)
    actual_snapshot_hash = snapshot_sha256(corpus_version)
    if protocol.snapshot_sha256 and protocol.snapshot_sha256 != actual_snapshot_hash:
        raise SnapshotCoverageError("snapshot checksum differs from frozen protocol")
    actual_popscore_hash = popscore_snapshot_sha256(corpus_version)
    expected_popscore_hash = protocol.raw.get("popscore_snapshot_sha256")
    if expected_popscore_hash and expected_popscore_hash != actual_popscore_hash:
        raise SnapshotCoverageError("PopScore checksum differs from frozen protocol")

    user_model = get_user_model()
    users = list(
        user_model.objects.filter(
            demo_identity__marker=SYNTHETIC_MARKER,
        ).order_by("id")
    )
    population_report = validate_active_population(users, protocol, corpus_version)
    partition = user_split([user.pk for user in users], protocol)
    user_ids = set(getattr(partition, split))
    training_probabilities = _training_item_probabilities(set(partition.train))
    selected_users = [user for user in users if user.pk in user_ids]
    # heldout_ids is always a frozenset (one element under leave_one_out_per_user,
    # one or more under the candidate v15 leave_fraction_out_dominant_tag_per_user
    # strategy) -- see evaluation.candidates.build().
    candidates_by_user: list[tuple[Any, list[Any], frozenset, str]] = []
    skipped_user_count = 0
    for user in selected_users:
        built = build(user, protocol, corpus_version)
        if built is None:
            skipped_user_count += 1
            continue
        candidate_ids, heldout_ids, candidate_hash = built
        candidates_by_user.append((user, list(candidate_ids), heldout_ids, candidate_hash))
    if not candidates_by_user:
        raise ValueError(f"no evaluable synthetic users in {split} split")

    evaluation_tag_profile = tag_rating_profile(corpus_version)
    evaluation_family_idf = all_family_idf_profiles(corpus_version)
    signal_availability = coverage_report(corpus_version)
    # Exists(), not .filter(curated_labels__isnull=False): the latter JOINs the
    # curated_labels M2M and duplicates a work once per label (bug fixed
    # 2026-09-11 -- a work with N labels was scored and ranked N times,
    # inflating precision/recall/nDCG/MAP past their [0,1] bounds whenever it
    # ranked highly). recommendations/content/rank.py's own product-facing
    # candidate query already uses this Exists() pattern for the same reason;
    # this mirrors it so the offline `prepared["works"]` path matches it.
    evaluation_works = list(
        evaluation_candidate_works(corpus_version)
        .filter(Exists(GameWork.objects.filter(pk=OuterRef("pk"), curated_labels__isnull=False)))
        .prefetch_related("curated_labels", "releases__platform", "franchises", "developers")
    )
    snapshot_rows = CorpusRatingSnapshot.objects.filter(
        work_id__in=[work.id for work in evaluation_works], rating__isnull=False,
        corpus_version=corpus_version,
    )
    per_work_snapshots: dict[object, list[tuple[float, int, int | None]]] = {}
    for work_id, rating, rating_count, total_rating_count in snapshot_rows.values_list(
        "work_id", "rating", "rating_count", "total_rating_count"
    ):
        per_work_snapshots.setdefault(work_id, []).append(
            (rating, rating_count, total_rating_count)
        )
    evaluation_snapshot_stats = {
        work_id: (
            math.fsum(rating * count for rating, count, _total_count in rows) / sum(count for _rating, count, _total_count in rows)
            if sum(count for _rating, count, _total_count in rows)
            else math.fsum(rating for rating, _count, _total_count in rows) / len(rows),
            sum(count for _rating, count, _total_count in rows),
            max(
                (total_count for _rating, _count, total_count in rows if total_count is not None),
                default=None,
            ),
        )
        for work_id, rows in per_work_snapshots.items()
    }
    evaluation_prepared = {
        "works": evaluation_works,
        "vectors": _prepared_candidate_vectors(
            evaluation_works, signal_availability, evaluation_family_idf
        ),
        "tag_profile": evaluation_tag_profile,
        "family_idf": evaluation_family_idf,
        "snapshot_stats": evaluation_snapshot_stats,
        "snapshot_sha256": actual_snapshot_hash,
        "popscore_snapshot_sha256": actual_popscore_hash,
        "training_user_ids": tuple(partition.train),
        # Shared across every algorithm_id, same corpus_version + date for the
        # whole run: computing it once here (instead of per rank_content_v1
        # call) avoids one CorpusRatingSnapshot aggregate query per algorithm
        # per user. rank_content_v1 already prefers prepared["rating_prior"]
        # when present.
        "rating_prior": corpus_rating_prior(corpus_version, eligibility_cutoff_date=date.today()),
    }
    vector_by_id = {
        str(work_id): vector for work_id, vector in evaluation_prepared["vectors"].items()
    }
    candidate_universe = {
        str(candidate_id)
        for _user, candidate_ids, _heldout_ids, _candidate_hash in candidates_by_user
        for candidate_id in candidate_ids
    }
    # frozenset iteration order is not stable across processes (str hash
    # randomisation), so the manifest row joins a *sorted* rendering of the
    # held-out ids rather than str()-ing the frozenset directly.
    all_manifest_rows = [
        (str(user.pk), ",".join(sorted(str(h) for h in heldout_ids)), candidate_hash)
        for user, _candidate_ids, heldout_ids, candidate_hash in candidates_by_user
    ]
    split_manifest_hash = _hash_payload(sorted(all_manifest_rows))

    return {
        "corpus_version": corpus_version,
        "split": split,
        "actual_snapshot_hash": actual_snapshot_hash,
        "actual_popscore_hash": actual_popscore_hash,
        "population_report": population_report,
        "selected_users": selected_users,
        "candidates_by_user": candidates_by_user,
        "skipped_user_count": skipped_user_count,
        "training_probabilities": training_probabilities,
        "evaluation_prepared": evaluation_prepared,
        "vector_by_id": vector_by_id,
        "candidate_universe": candidate_universe,
        "split_manifest_sha256": split_manifest_hash,
    }


def precompute_shared_content_signals(
    context: dict[str, Any],
    *,
    should_continue: Callable[[], bool] | None = None,
) -> None:
    """Populate the per-(user,work) content signals every algorithm reuses.

    Mutates ``context["evaluation_prepared"]`` in place, adding the same
    ``_profile_cache`` / ``_rating_term_cache`` / ``_similarity_cache`` keys
    ``rank_content_v1`` already knows how to read (2026-09-11,
    ``recommendations/content/rank.py``) -- but pre-populated for *every*
    user in this run's split up front, not lazily per call. ``rating_term``
    never depends on the user, so it is computed once per work regardless of
    how many users are in the split; ``facet_similarity`` (positive and
    negative) is computed once per (user, work) -- the same total volume of
    work ``run_evaluation`` already pays across its 16 sequential algorithm
    calls, just done once instead of once per algorithm.

    This only saves anything for a parallel caller if the worker *processes*
    inherit this already-populated memory via ``fork`` copy-on-write rather
    than each rebuilding it or having it re-pickled to them -- see the
    module-level ``_SHARED_CONTEXT`` in ``run_evaluation_parallel``, built
    and precomputed in the parent process before any worker is forked.
    """

    from recommendations.content.combine import rating_term
    from recommendations.content.profile import ProfileInputs, build_profile_inputs
    from recommendations.content.similarity import facet_similarity

    prepared = context["evaluation_prepared"]
    works = prepared["works"]
    vectors = prepared["vectors"]
    tag_profile = prepared["tag_profile"]
    family_idf = prepared["family_idf"]
    snapshot_stats = prepared["snapshot_stats"]
    rating_prior = prepared["rating_prior"]
    corpus_version = context["corpus_version"]

    rating_term_cache: dict[Any, tuple[float, bool]] = {}
    for index, work in enumerate(works):
        if index % 512 == 0 and should_continue is not None and not should_continue():
            return
        rating_term_cache[work.id] = rating_term(
            work, corpus_version, tag_profile, snapshot_stats, rating_prior
        )

    profile_cache: dict[Any, ProfileInputs] = {}
    similarity_cache: dict[tuple[Any, Any], tuple[dict, float]] = {}
    for user, _candidate_ids, _heldout_id, _candidate_hash in context["candidates_by_user"]:
        if should_continue is not None and not should_continue():
            return
        profile_inputs = build_profile_inputs(user, corpus_version, family_idf)
        profile_cache[user.pk] = profile_inputs
        for work in works:
            vector = vectors.get(work.id)
            if vector is None:
                continue
            similarity_evidence = facet_similarity(profile_inputs.positive, vector)
            negative_similarity = facet_similarity(profile_inputs.negative, vector)["score"]
            similarity_cache[(user.pk, work.id)] = (similarity_evidence, negative_similarity)

    prepared["_rating_term_cache"] = rating_term_cache
    prepared["_profile_cache"] = profile_cache
    prepared["_similarity_cache"] = similarity_cache


def run(
    protocol: Protocol,
    corpus_version: str,
    algorithms: Mapping[str, Callable[..., Any]] | None = None,
    *,
    split: str = "test",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run each algorithm against one immutable candidate set per user.

    ``context`` (2026-09-11) is the dict :func:`build_evaluation_context`
    returns; passing one in skips rebuilding it, so a caller that already
    built (and optionally signal-precomputed) it once can reuse it across
    several ``run()`` calls -- each scoring a different, disjoint algorithm
    subset -- without rebuilding the shared candidate sets or corpus-wide
    signals every time. Omitting it (the default) preserves exactly the
    previous behaviour of building everything fresh inside this call.
    """

    if context is not None and context["split"] != split:
        raise ValueError(
            f"context was built for split={context['split']!r}, but run() was called with split={split!r}"
        )
    ctx = context if context is not None else build_evaluation_context(protocol, corpus_version, split)
    candidates_by_user = ctx["candidates_by_user"]
    evaluation_prepared = ctx["evaluation_prepared"]
    training_probabilities = ctx["training_probabilities"]
    candidate_universe = ctx["candidate_universe"]
    vector_by_id = ctx["vector_by_id"]

    algorithm_map = dict(algorithms or default_algorithms())
    algorithm_artifacts: dict[str, Any] = {}
    algorithm_count = len(algorithm_map)
    for algorithm_index, (algorithm_id, algorithm) in enumerate(algorithm_map.items(), start=1):
        algorithm_started = time.perf_counter()
        per_user: list[dict[str, Any]] = []
        metric_rows: dict[str, list[dict[str, float]]] = {str(k): [] for k in K_VALUES}
        ranked_lists: dict[str, list[list[str]]] = {str(k): [] for k in K_VALUES}
        candidate_lists: dict[str, list[list[str]]] = {str(k): [] for k in K_VALUES}
        beyond_rows: dict[str, list[dict[str, float | None]]] = {str(k): [] for k in K_VALUES}
        for user, candidate_ids, heldout_ids, candidate_hash in candidates_by_user:
            result = algorithm(
                user=user,
                algorithm_id=algorithm_id,
                candidate_ids=tuple(candidate_ids),
                heldout_work_ids=heldout_ids,
                protocol=protocol,
                corpus_version=corpus_version,
                tag_profile=evaluation_prepared["tag_profile"],
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
            assert len(ranked_ids) == len(set(ranked_ids)), (
                f"algorithm {algorithm_id} returned a ranked list with duplicate ids "
                f"for user {user.pk} (metrics like nDCG/recall assume one entry per id)"
            )
            # One heldout id under leave_one_out_per_user; one or more under
            # the candidate v15 leave_fraction_out_dominant_tag_per_user
            # strategy -- evaluation.metrics is already written for the
            # general multi-relevant case, so this needs no metric changes.
            relevant = {str(h) for h in heldout_ids}
            row: dict[str, Any] = {
                "user_id": str(user.pk),
                "heldout_work_ids": sorted(relevant),
                "candidate_sha256": candidate_hash,
                "heldout_ranks": {
                    h: (ranked_ids.index(h) + 1 if h in ranked_ids else None)
                    for h in sorted(relevant)
                },
                "metrics": {},
                "beyond_accuracy": {},
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
                top_k = ranked_ids[:k]
                beyond = {
                    "intra_list_diversity": intra_list_diversity(top_k, vector_by_id),
                    "novelty": novelty_at_k(top_k, training_probabilities, k),
                    "recommended_count": len(top_k),
                }
                row["beyond_accuracy"][str(k)] = beyond
                ranked_lists[str(k)].append(top_k)
                candidate_lists[str(k)].append(sorted(candidate_strings))
                beyond_rows[str(k)].append(beyond)
            per_user.append(row)

        aggregates = {k: _average(rows) for k, rows in metric_rows.items()}
        beyond_aggregates: dict[str, dict[str, Any]] = {}
        for k in K_VALUES:
            key = str(k)
            exposed = {item for ranked in ranked_lists[key] for item in ranked}
            catalogue_coverage = catalogue_coverage_at_k(
                ranked_lists[key], candidate_universe, k
            )
            prediction_coverage = prediction_coverage_at_k(
                ranked_lists[key], candidate_lists[key], k
            )
            concentration = concentration_hhi_at_k(ranked_lists[key], k)
            ild, ild_count = _mean_applicable(
                [row["intra_list_diversity"] for row in beyond_rows[key]]
            )
            novelty, novelty_count = _mean_applicable(
                [row["novelty"] for row in beyond_rows[key]]
            )
            candidate_slots = sum(min(k, len(candidates)) for candidates in candidate_lists[key])
            prediction_slots = sum(len(ranked) for ranked in ranked_lists[key])
            beyond_aggregates[key] = {
                "catalogue_coverage": {
                    "value": catalogue_coverage,
                    "numerator": len(exposed & candidate_universe),
                    "denominator": len(candidate_universe),
                },
                "prediction_coverage": {
                    "value": prediction_coverage,
                    "numerator": prediction_slots,
                    "denominator": candidate_slots,
                },
                "concentration_hhi": {
                    "value": concentration,
                    "denominator": prediction_slots,
                },
                "intra_list_diversity": {
                    "value": ild,
                    "applicable_user_count": ild_count,
                    "user_count": len(beyond_rows[key]),
                },
                "novelty": {
                    "value": novelty,
                    "applicable_user_count": novelty_count,
                    "user_count": len(beyond_rows[key]),
                    "source": "training_interactions",
                },
            }
        algorithm_seconds = round(time.perf_counter() - algorithm_started, 6)
        algorithm_artifacts[algorithm_id] = {
            "algorithm_id": algorithm_id,
            "per_user": per_user,
            "aggregates": aggregates,
            "beyond_accuracy": beyond_aggregates,
            "duration_seconds": algorithm_seconds,
        }
        print(
            f"[eval] {algorithm_index}/{algorithm_count} {algorithm_id} "
            f"done in {algorithm_seconds:.1f}s "
            f"({len(candidates_by_user)} users)",
            file=sys.stderr,
            flush=True,
        )

    return {
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.frozen_hash(),
        "code_commit": _code_commit(),
        "corpus_version": corpus_version,
        "snapshot_sha256": ctx["actual_snapshot_hash"],
        "popscore_snapshot_sha256": ctx["actual_popscore_hash"],
        "feature_set_version": FEATURE_SET_VERSION,
        "seeds": {
            "leave_one_out": protocol.loo_seed,
            "user_split": protocol.user_split_seed,
        },
        "split": split,
        "evaluation_population": {
            **ctx["population_report"],
            "requested_user_count": len(ctx["selected_users"]),
            "evaluated_user_count": len(candidates_by_user),
            "skipped_user_count": ctx["skipped_user_count"],
            "skipped_reason": "no eligible positive item for leave-one-out",
        },
        "split_manifest_sha256": ctx["split_manifest_sha256"],
        "algorithms": algorithm_artifacts,
        "statistical_comparisons": {
            protocol.headline: _headline_statistical_comparison(protocol, algorithm_artifacts),
        },
        "simulation": True,
        "limitation": protocol.limitation,
    }
