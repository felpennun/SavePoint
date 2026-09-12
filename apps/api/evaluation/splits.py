"""Leave-one-out-per-user split and the disjoint train/validation/test user
partition (EVAL-01, EVAL-02; D-17, D-18, D-21).

The candidate set built here is identical for every algorithm given the same
user and seed (EVAL-01): eligible governed works (non-null IGDB user rating
and at least five total IGDB ratings) minus the user's *remaining* library,
plus the single eligible held-out item (D-18, RESEARCH Pitfall 6). Its
``sha256`` is returned so a run can freeze the per-user candidate manifest.

Leakage note (EVAL-02): the genre rating profile (D-13) is a *corpus* statistic
derived from the immutable ``CorpusRatingSnapshot`` of the active
``corpus_version`` -- not from user data -- so it is leakage-safe across the
train/validation/test partition. Any statistic that *were* derived from users
would have to be computed on the ``train`` partition only.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import uuid
from datetime import date
from typing import NamedTuple

from catalogue.corpus import evaluation_candidate_works
from catalogue.models import GameWork
from library.models import LibraryEntry
from recommendations._weights import _entry_weight
from recommendations.content.features import tag_idf_profile
from recommendations.content.profile import _l2_normalize, _load_vectors, build_profile_inputs


class LeaveOneOut(NamedTuple):
    """Result of holding one relevant-positive item out for a user.

    ``GameWork`` primary keys are UUIDs, so the id collections are
    ``frozenset[uuid.UUID]`` and the manifest hash is taken over their
    sorted string forms.
    """

    heldout_work_id: uuid.UUID
    candidate_ids: frozenset[uuid.UUID]
    remaining_library_ids: frozenset[uuid.UUID]
    candidate_manifest_sha256: str


class LeaveFractionOut(NamedTuple):
    """Result of holding out a dominant-tag-focused fraction of a user's positives.

    Candidate protocol v15 (2026-09-12, not yet frozen). Unlike
    :class:`LeaveOneOut`, more than one item can be held out, and the count
    is adaptive per user rather than fixed: it starts at
    ``ceil(protocol.dominant_tag_loo_fraction * pool_size)`` (``pool_size``
    being how many of the user's rating-floor-eligible positives share their
    own single most-weighted content tag) and backs off by one whenever
    removing that many would knock that tag out of first place in the
    user's *remaining* profile -- but never below 1, which always wins over
    the dominance check. A user is therefore never excluded outright by this
    mechanism (unlike ``leave_one_out``, which excludes a user with zero
    eligible positives): worst case, exactly one item is held out and the
    tag may end up ranked lower in what remains. ``achieved_rank`` records
    which happened (``1`` if dominance was preserved, ``>=2`` if it was
    demoted) purely for reporting -- see the 2026-09-12 session note on why
    a demoted-but-still-present tag is still a meaningful signal
    (``facet_similarity`` weighs every matching profile tag, not only the
    top one).
    """

    heldout_work_ids: frozenset[uuid.UUID]
    dominant_tag: str
    achieved_rank: int
    candidate_ids: frozenset[uuid.UUID]
    remaining_library_ids: frozenset[uuid.UUID]
    candidate_manifest_sha256: str


class UserSplit(NamedTuple):
    """Disjoint train/validation/test partition of the synthetic user ids."""

    train: tuple[int, ...]
    validation: tuple[int, ...]
    test: tuple[int, ...]


def relevant_positive_ids(
    user,
    protocol,
    corpus_version: str | None = None,
    eligibility_cutoff_date: date | None = None,
) -> set[object]:
    """Work ids the user counts as a positive under the frozen relevance rule.

    D-17: ``current_status == "completed"`` **or** ``rating_half_steps`` at or
    above ``protocol.relevance.rating_half_steps_gte``.
    """

    rule = protocol.relevance
    want_completed = bool(rule.get("completed"))
    floor = int(rule["rating_half_steps_gte"])

    positives: set[object] = set()
    for work_id, status, rating in LibraryEntry.objects.filter(user=user).values_list(
        "work_id", "current_status", "rating_half_steps"
    ):
        if (want_completed and status == "completed") or (rating is not None and rating >= floor):
            positives.add(work_id)
    if corpus_version is not None or eligibility_cutoff_date is not None:
        eligible_ids = set(
            evaluation_candidate_works(
                corpus_version,
                eligibility_cutoff_date=eligibility_cutoff_date,
            ).values_list("id", flat=True)
        )
        positives &= eligible_ids
    return positives


def leave_one_out(
    user,
    seed,
    protocol,
    corpus_version: str | None = None,
    eligibility_cutoff_date: date | None = None,
) -> LeaveOneOut | None:
    """Hold one relevant-positive item out for ``user`` and build its candidate set.

    Returns ``None`` when the user has no relevant-positive item — the caller
    excludes them from the evaluation rather than crashing.

    The held-out item is chosen deterministically by
    ``random.Random(f"{seed}:{user.pk}")``, so two runs with the same seed
    produce the same held-out item and the same candidate manifest hash.
    """

    positives = relevant_positive_ids(
        user,
        protocol,
        corpus_version,
        eligibility_cutoff_date,
    )
    if not positives:
        return None

    # protocol_version 14 (D-TBD): the held-out item must also clear a
    # catalogue-quality floor on its own external rating, not just the
    # user's personal taste rule -- otherwise a personally-loved but
    # externally under-rated title gets pulled down by rating_confidence/
    # PopScore in most of the 16 variants regardless of how well the
    # algorithm actually modelled the user's taste. Absent on older frozen
    # protocols, so this is a no-op there.
    heldout_min_rating = protocol.heldout_min_external_rating
    if heldout_min_rating is not None:
        positives = {
            work_id
            for work_id, rating in GameWork.objects.filter(
                id__in=positives
            ).values_list("id", "rating")
            if rating is not None and rating >= heldout_min_rating
        }
        if not positives:
            return None

    rng = random.Random(f"{seed}:{user.pk}")
    heldout = rng.choice(sorted(positives))

    library_ids = set(
        LibraryEntry.objects.filter(user=user).values_list("work_id", flat=True)
    )
    remaining_library_ids = library_ids - {heldout}

    eligible_ids = set(
        evaluation_candidate_works(
            corpus_version,
            eligibility_cutoff_date=eligibility_cutoff_date,
        ).values_list("id", flat=True)
    )
    candidate_ids = (eligible_ids - remaining_library_ids) | {heldout}

    manifest = hashlib.sha256(
        json.dumps(sorted(str(cid) for cid in candidate_ids), separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return LeaveOneOut(
        heldout_work_id=heldout,
        candidate_ids=frozenset(candidate_ids),
        remaining_library_ids=frozenset(remaining_library_ids),
        candidate_manifest_sha256=manifest,
    )


def _profile_from_entries(
    entries: list[dict], vectors: dict[object, dict[str, float]]
) -> dict[str, float]:
    """Weighted, L2-normalised content profile over an explicit entry list.

    Mirrors ``recommendations.content.profile.build_profile_inputs``'s
    positive-accumulation formula exactly, but over a caller-supplied entry
    list rather than a live query -- so a caller can simulate the profile
    that would result from excluding specific work ids without touching the
    database.
    """

    accumulator: dict[str, float] = {}
    total_weight = 0.0
    for entry in entries:
        status = entry["current_status"]
        rating = entry["rating_half_steps"]
        if status not in {"completed", "playing"} or rating is None or rating < 7:
            continue
        normalized = _l2_normalize(vectors.get(entry["work_id"]) or {})
        if not normalized:
            continue
        weight = _entry_weight(status, rating)
        if weight <= 0:
            continue
        total_weight += weight
        for key, value in normalized.items():
            accumulator[key] = accumulator.get(key, 0.0) + weight * value
    if total_weight <= 0 or not accumulator:
        return {}
    return {key: value / total_weight for key, value in accumulator.items()}


def _rank_of(tag: str, profile: dict[str, float]) -> int | None:
    ranked = sorted(profile.items(), key=lambda kv: -kv[1])
    for index, (candidate_tag, _weight) in enumerate(ranked, start=1):
        if candidate_tag == tag:
            return index
    return None


def leave_fraction_out_dominant_tag(
    user,
    seed,
    protocol,
    corpus_version: str | None = None,
    eligibility_cutoff_date: date | None = None,
) -> LeaveFractionOut | None:
    """Hold out an adaptive, dominant-tag-focused fraction of a user's positives.

    Returns ``None`` when the user has no rating-floor-eligible positive at
    all, or when their single most-weighted profile facet is not a content
    tag (e.g. a platform they own almost everything on) -- this mechanism is
    specifically about content-tag recovery, so a user without one is not
    eligible for it, mirroring how ``leave_one_out`` excludes a user with no
    eligible positive rather than guessing.
    """

    positives = relevant_positive_ids(user, protocol, corpus_version, eligibility_cutoff_date)
    if not positives:
        return None

    heldout_min_rating = protocol.heldout_min_external_rating
    if heldout_min_rating is not None:
        positives = {
            work_id
            for work_id, rating in GameWork.objects.filter(id__in=positives).values_list("id", "rating")
            if rating is not None and rating >= heldout_min_rating
        }
        if not positives:
            return None

    tag_idf = tag_idf_profile(corpus_version)
    profile_inputs = build_profile_inputs(user, corpus_version, tag_idf)
    if not profile_inputs.positive:
        return None
    dominant_tag = max(profile_inputs.positive.items(), key=lambda kv: kv[1])[0]
    if not dominant_tag.startswith("tag:"):
        return None
    dominant_slug = dominant_tag.split(":", 1)[1]

    same_tag_pool = sorted(
        GameWork.objects.filter(id__in=positives, curated_labels__slug=dominant_slug).values_list(
            "id", flat=True
        )
    )
    if not same_tag_pool:
        return None

    fraction = protocol.dominant_tag_loo_fraction
    pool_size = len(same_tag_pool)
    target_n = max(1, min(pool_size, math.ceil(fraction * pool_size)))

    rng = random.Random(f"{seed}:{user.pk}:dominant-tag")
    shuffled_pool = list(same_tag_pool)
    rng.shuffle(shuffled_pool)

    library_entries = list(
        LibraryEntry.objects.filter(user=user).values("work_id", "current_status", "rating_half_steps")
    )
    vectors = _load_vectors([entry["work_id"] for entry in library_entries], corpus_version, tag_idf)

    n = target_n
    heldout: list[uuid.UUID] = shuffled_pool[:1]
    achieved_rank = 0
    while n >= 1:
        candidate_heldout = shuffled_pool[:n]
        excluded = set(candidate_heldout)
        remaining_entries = [entry for entry in library_entries if entry["work_id"] not in excluded]
        new_profile = _profile_from_entries(remaining_entries, vectors)
        rank = _rank_of(dominant_tag, new_profile) if new_profile else None
        if n == 1 or rank == 1:
            heldout = candidate_heldout
            achieved_rank = rank if rank is not None else n + 1  # worse than any observed rank
            break
        n -= 1

    heldout_ids = frozenset(heldout)
    library_ids = {entry["work_id"] for entry in library_entries}
    remaining_library_ids = library_ids - heldout_ids

    eligible_ids = set(
        evaluation_candidate_works(
            corpus_version,
            eligibility_cutoff_date=eligibility_cutoff_date,
        ).values_list("id", flat=True)
    )
    candidate_ids = (eligible_ids - remaining_library_ids) | heldout_ids

    manifest = hashlib.sha256(
        json.dumps(sorted(str(cid) for cid in candidate_ids), separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return LeaveFractionOut(
        heldout_work_ids=heldout_ids,
        dominant_tag=dominant_tag,
        achieved_rank=achieved_rank,
        candidate_ids=frozenset(candidate_ids),
        remaining_library_ids=frozenset(remaining_library_ids),
        candidate_manifest_sha256=manifest,
    )


def user_split(user_ids, protocol) -> UserSplit:
    """Partition ``user_ids`` into disjoint train/validation/test subsets.

    Sizes come from ``protocol.user_split`` and the shuffle is seeded by
    ``protocol.user_split_seed``, so the partition is reproducible. The three
    subsets do not overlap and their union is the whole input set; the input
    must therefore contain exactly ``train + validation + test`` distinct ids.
    """

    spec = protocol.user_split
    n_train = int(spec["train"])
    n_validation = int(spec["validation"])
    n_test = int(spec["test"])
    total = n_train + n_validation + n_test

    ordered = sorted(set(user_ids))
    if len(ordered) != total:
        raise ValueError(
            f"user_split expects exactly {total} distinct users "
            f"(train={n_train}, validation={n_validation}, test={n_test}); got {len(ordered)}."
        )

    shuffled = list(ordered)
    random.Random(protocol.user_split_seed).shuffle(shuffled)

    train = tuple(sorted(shuffled[:n_train]))
    validation = tuple(sorted(shuffled[n_train : n_train + n_validation]))
    test = tuple(sorted(shuffled[n_train + n_validation :]))
    return UserSplit(train=train, validation=validation, test=test)
