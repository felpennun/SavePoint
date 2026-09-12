"""Cross-process shared-signal cache for the content recommender (2026-09-11).

Every one of the 13 dependent algorithm variants in
``recommendations.published.SIGNAL_DEPENDENT_ALGORITHM_IDS`` scores candidates
through the exact same ``rank_content_v1`` warm loop
(``recommendations/content/rank.py``): for a given (user, corpus_version,
tag data) pair, ``rating_term`` and ``facet_similarity`` are identical no
matter which variant is asking. The offline evaluation runner exploits this
by sharing one in-process ``prepared`` dict across all 16 algorithms in a
single Python process. The live product queue cannot do that the same way --
each variant runs in its own dedicated worker container
(``infra/compose.yaml``) -- so this module is the cross-process equivalent:
one dedicated ``content-signals-v1`` job computes the O(candidates) loop once
per (user, collection revision, configuration) and persists it to
``RecommendationSignalCache``; every dependent job then reads that row and
rehydrates it into the same ``prepared`` cache shape ``rank_content_v1``
already knows how to consume, skipping the loop entirely.

Dependent jobs never wait on a lock or a blocking call for this: the queue's
claim query (``recommendations.jobs._claim_next_job``) simply does not surface
a dependent job until its signals row exists, so a worker with nothing else
to do polls again on its normal ``--poll-seconds`` interval instead of
recomputing anything itself.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any, Callable, Iterable

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Exists, OuterRef

from catalogue.corpus import evaluation_candidate_works
from catalogue.models import CorpusRatingSnapshot, GameWork
from library.models import LibraryEntry
from recommendations.cancellation import RecommendationComputationCancelled
from recommendations.content.combine import rating_term
from recommendations.content.features import all_family_idf_profiles, corpus_rating_prior, tag_rating_profile
from recommendations.content.profile import ProfileInputs, build_profile_inputs
from recommendations.content.rank import _load_candidate_vectors, _snapshot_sha256
from recommendations.content.similarity import facet_similarity
from recommendations.content.variants import ALGORITHM_REGISTRY
from recommendations.models import RecommendationSignalCache


_CANCELLATION_CHECK_INTERVAL = 128
# Any registered variant works here -- _load_candidate_vectors only reads
# ``spec.feature_set_version``, which every variant shares (FEATURE_SET_VERSION).
_ANY_SPEC = ALGORITHM_REGISTRY["content-cbf-weighted-v1"]


def _ensure_current(should_continue: Callable[[], bool] | None) -> None:
    if should_continue is not None and not should_continue():
        raise RecommendationComputationCancelled


def build_corpus_bundle(
    user: AbstractBaseUser,
    corpus_version: str | None,
    candidate_ids: Iterable[object],
    *,
    should_continue: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Build the same corpus-wide bundle ``rank_content_v1`` builds when unprepared.

    This is the part every dependent worker still computes for itself (a
    handful of queries, not the expensive per-candidate Python loop) -- kept
    here so the signals job and every dependent job build it identically.
    Only ``candidate_ids`` (a user's own eligible set) and the user's own
    library (folded into the snapshot hash, matching ``rank_content_v1``'s
    unprepared path exactly) vary per user; everything else is corpus-wide.
    """

    requested_ids = set(candidate_ids)
    candidates = list(
        evaluation_candidate_works(corpus_version)
        .filter(id__in=requested_ids)
        .filter(Exists(GameWork.objects.filter(pk=OuterRef("pk"), curated_labels__isnull=False)))
    )
    _ensure_current(should_continue)
    family_idf = all_family_idf_profiles(corpus_version)
    tag_profile = tag_rating_profile(corpus_version)
    vectors = _load_candidate_vectors(
        candidates, _ANY_SPEC, corpus_version, family_idf=family_idf, should_continue=should_continue
    )
    snapshot_rows = CorpusRatingSnapshot.objects.filter(
        work_id__in=[work.id for work in candidates], rating__isnull=False
    )
    if corpus_version is not None:
        snapshot_rows = snapshot_rows.filter(corpus_version=corpus_version)
    per_work: dict[object, list[tuple[float | None, int, int | None]]] = {}
    for work_id, rating, rating_count, total_rating_count in snapshot_rows.values_list(
        "work_id", "rating", "rating_count", "total_rating_count"
    ):
        per_work.setdefault(work_id, []).append((rating, rating_count, total_rating_count))
    snapshot_stats = {
        work_id: (
            (
                math.fsum(rating * count for rating, count, _total in rows if rating is not None)
                / sum(count for rating, count, _total in rows if rating is not None)
                if sum(count for rating, count, _total in rows if rating is not None)
                else None
            ),
            sum(count for _rating, count, _total in rows),
            max((total for _rating, _count, total in rows if total is not None), default=None),
        )
        for work_id, rows in per_work.items()
    }
    rating_prior = corpus_rating_prior(corpus_version, eligibility_cutoff_date=date.today())
    seen_ids = set(LibraryEntry.objects.filter(user=user).values_list("work_id", flat=True))
    snapshot_sha256 = _snapshot_sha256(corpus_version, {work.id for work in candidates} | seen_ids)
    return {
        "works": candidates,
        "vectors": vectors,
        "tag_profile": tag_profile,
        "family_idf": family_idf,
        "snapshot_stats": snapshot_stats,
        "snapshot_sha256": snapshot_sha256,
        "rating_prior": rating_prior,
    }


def build_and_store_signal_cache(
    *,
    user: AbstractBaseUser,
    requested_revision: int,
    configuration_fingerprint: str,
    corpus_version: str | None,
    bundle: dict[str, Any],
    should_continue: Callable[[], bool] | None = None,
) -> RecommendationSignalCache:
    """Compute and persist one user's shared content signals (the signals job).

    ``bundle`` is the dict returned by :func:`build_corpus_bundle`.
    """

    candidates: list[GameWork] = bundle["works"]
    vectors: dict[Any, dict[str, float]] = bundle["vectors"]
    tag_profile: dict[str, float] = bundle["tag_profile"]
    family_idf: dict[str, dict[str, float]] = bundle["family_idf"]
    snapshot_stats = bundle["snapshot_stats"]
    rating_prior = bundle["rating_prior"]

    profile_inputs = build_profile_inputs(user, corpus_version, family_idf)
    rating_term_by_work: dict[str, list[Any]] = {}
    similarity_by_work: dict[str, list[Any]] = {}
    for index, work in enumerate(candidates):
        if index % _CANCELLATION_CHECK_INTERVAL == 0:
            _ensure_current(should_continue)
        vector = vectors.get(work.id)
        if vector is None:
            continue
        rt, fallback = rating_term(work, corpus_version, tag_profile, snapshot_stats, rating_prior)
        rating_term_by_work[str(work.id)] = [rt, fallback]
        similarity_evidence = facet_similarity(profile_inputs.positive, vector)
        negative_similarity = facet_similarity(profile_inputs.negative, vector)["score"]
        similarity_by_work[str(work.id)] = [similarity_evidence, negative_similarity]

    row, _created = RecommendationSignalCache.objects.update_or_create(
        user=user,
        requested_revision=requested_revision,
        configuration_fingerprint=configuration_fingerprint,
        defaults={
            "corpus_version": corpus_version,
            "profile_inputs_json": {
                "positive": profile_inputs.positive,
                "negative": profile_inputs.negative,
                "positive_entry_count": profile_inputs.positive_entry_count,
                "positive_rating_sum_half_steps": profile_inputs.positive_rating_sum_half_steps,
                "negative_tags": list(profile_inputs.negative_tags),
            },
            "rating_term_json": rating_term_by_work,
            "similarity_json": similarity_by_work,
        },
    )
    return row


def load_prepared(
    row: RecommendationSignalCache,
    *,
    user: AbstractBaseUser,
    bundle: dict[str, Any],
) -> dict[str, Any]:
    """Merge a stored signal row into a full ``prepared`` dict for ``rank_content_v1``.

    JSON keys are always strings, so stored work ids are mapped back onto the
    real ``work.id`` values on ``bundle["works"]`` (the same governed-candidate
    query every dependent worker builds itself) rather than assumed to be a
    particular primary-key type.
    """

    payload = row.profile_inputs_json
    profile_inputs = ProfileInputs(
        positive=payload["positive"],
        negative=payload["negative"],
        positive_entry_count=payload["positive_entry_count"],
        positive_rating_sum_half_steps=payload["positive_rating_sum_half_steps"],
        negative_tags=tuple(payload["negative_tags"]),
    )
    id_by_str = {str(work.id): work.id for work in bundle["works"]}
    rating_term_cache = {
        id_by_str[work_id]: (entry[0], entry[1])
        for work_id, entry in row.rating_term_json.items()
        if work_id in id_by_str
    }
    similarity_cache = {
        (user.pk, id_by_str[work_id]): (entry[0], entry[1])
        for work_id, entry in row.similarity_json.items()
        if work_id in id_by_str
    }
    return {
        **bundle,
        "_profile_cache": {user.pk: profile_inputs},
        "_rating_term_cache": rating_term_cache,
        "_similarity_cache": similarity_cache,
    }
