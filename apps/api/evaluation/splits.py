"""Leave-one-out-per-user split and the disjoint train/validation/test user
partition (EVAL-01, EVAL-02; D-17, D-18, D-21).

The candidate set built here is identical for every algorithm given the same
user and seed (EVAL-01): ``governed_works(corpus_version)`` minus the user's
*remaining* library, plus the single held-out item (D-18, RESEARCH Pitfall 6).
Its ``sha256`` is returned so a run can freeze the per-user candidate manifest.

Leakage note (EVAL-02): the genre rating profile (D-13) is a *corpus* statistic
derived from the immutable ``CorpusRatingSnapshot`` of the active
``corpus_version`` -- not from user data -- so it is leakage-safe across the
train/validation/test partition. Any statistic that *were* derived from users
would have to be computed on the ``train`` partition only.
"""

from __future__ import annotations

import hashlib
import json
import random
import uuid
from typing import NamedTuple

from catalogue.corpus import governed_works
from library.models import LibraryEntry


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


class UserSplit(NamedTuple):
    """Disjoint train/validation/test partition of the synthetic user ids."""

    train: tuple[int, ...]
    validation: tuple[int, ...]
    test: tuple[int, ...]


def relevant_positive_ids(user, protocol) -> set[int]:
    """Work ids the user counts as a positive under the frozen relevance rule.

    D-17: ``current_status == "completed"`` **or** ``rating_half_steps`` at or
    above ``protocol.relevance.rating_half_steps_gte``.
    """

    rule = protocol.relevance
    want_completed = bool(rule.get("completed"))
    floor = int(rule["rating_half_steps_gte"])

    positives: set[int] = set()
    for work_id, status, rating in LibraryEntry.objects.filter(user=user).values_list(
        "work_id", "current_status", "rating_half_steps"
    ):
        if (want_completed and status == "completed") or (rating is not None and rating >= floor):
            positives.add(work_id)
    return positives


def leave_one_out(user, seed, protocol, corpus_version: str | None = None) -> LeaveOneOut | None:
    """Hold one relevant-positive item out for ``user`` and build its candidate set.

    Returns ``None`` when the user has no relevant-positive item — the caller
    excludes them from the evaluation rather than crashing.

    The held-out item is chosen deterministically by
    ``random.Random(f"{seed}:{user.pk}")``, so two runs with the same seed
    produce the same held-out item and the same candidate manifest hash.
    """

    positives = relevant_positive_ids(user, protocol)
    if not positives:
        return None

    rng = random.Random(f"{seed}:{user.pk}")
    heldout = rng.choice(sorted(positives))

    library_ids = set(
        LibraryEntry.objects.filter(user=user).values_list("work_id", flat=True)
    )
    remaining_library_ids = library_ids - {heldout}

    governed_ids = set(governed_works(corpus_version).values_list("id", flat=True))
    candidate_ids = (governed_ids - remaining_library_ids) | {heldout}

    manifest = hashlib.sha256(
        json.dumps(sorted(str(cid) for cid in candidate_ids), separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return LeaveOneOut(
        heldout_work_id=heldout,
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
