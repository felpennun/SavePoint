"""Leave-one-out split + train/validation/test user partition (EVAL-01/02).

Plan 02-08 Task 3. Pins determinism per ``(seed, user_id)``, the candidate-set
rule (governed corpus minus remaining library plus held-out item), a stable
candidate-manifest hash, and a disjoint user partition whose sizes match the
frozen protocol.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from catalogue.models import GameWork
from evaluation import protocol as protocol_module
from evaluation.splits import (
    LeaveOneOut,
    UserSplit,
    leave_one_out,
    relevant_positive_ids,
    user_split,
)
from library.models import LibraryEntry

User = get_user_model()
CORPUS_VERSION = "loo-test"


@pytest.fixture
def frozen_protocol():
    return protocol_module.load()


@pytest.fixture
def governed_corpus(db):
    works = []
    for i in range(12):
        works.append(
            GameWork.objects.create(
                canonical_slug=f"loo-work-{i:02d}",
                original_title=f"LOO Work {i:02d}",
                is_dlc=False,
                in_corpus=True,
                corpus_version=CORPUS_VERSION,
                rating=80.0,
                rating_count=1,
            )
        )
    works.append(
        GameWork.objects.create(
            canonical_slug="loo-work-unrated",
            original_title="LOO Work Unrated",
            is_dlc=False,
            in_corpus=True,
            corpus_version=CORPUS_VERSION,
        )
    )
    works.append(
        GameWork.objects.create(
            canonical_slug="loo-work-non-null-rating",
            original_title="LOO Work Non-null Rating",
            is_dlc=False,
            in_corpus=True,
            corpus_version=CORPUS_VERSION,
            rating=101.0,
        )
    )
    # an ungoverned work, to prove it never leaks into the candidate set
    works.append(
        GameWork.objects.create(
            canonical_slug="loo-work-ungoverned",
            original_title="LOO Work Ungoverned",
            is_dlc=False,
            in_corpus=False,
        )
    )
    return works


@pytest.fixture
def user(db):
    return User.objects.create_user(username="synthetic-loo", password="Synthetic-LOO-9!")


def _own(user, work, *, status=None, rating=None):
    return LibraryEntry.objects.create(
        user=user, work=work, current_status=status, rating_half_steps=rating
    )


# --------------------------------------------------------------------------- #
# relevance rule (D-17)                                                        #
# --------------------------------------------------------------------------- #
def test_relevant_positive_rule(user, governed_corpus, frozen_protocol) -> None:
    _own(user, governed_corpus[0], status="completed")            # positive: completed
    _own(user, governed_corpus[1], status="playing", rating=8)    # positive: rating >= 7
    _own(user, governed_corpus[2], status="pending", rating=6)    # not a positive
    _own(user, governed_corpus[3], status="abandoned")            # not a positive

    positives = relevant_positive_ids(user, frozen_protocol)

    assert positives == {governed_corpus[0].id, governed_corpus[1].id}


def test_user_without_positives_is_skipped(user, governed_corpus, frozen_protocol) -> None:
    _own(user, governed_corpus[0], status="pending")
    _own(user, governed_corpus[1], status="abandoned", rating=3)

    assert relevant_positive_ids(user, frozen_protocol) == set()
    assert leave_one_out(user, seed=frozen_protocol.loo_seed, protocol=frozen_protocol,
                         corpus_version=CORPUS_VERSION) is None


# --------------------------------------------------------------------------- #
# leave-one-out                                                                #
# --------------------------------------------------------------------------- #
def test_leave_one_out_is_deterministic_per_seed_and_user(user, governed_corpus, frozen_protocol) -> None:
    for work in governed_corpus[:5]:
        _own(user, work, status="completed")

    first = leave_one_out(user, seed=99, protocol=frozen_protocol, corpus_version=CORPUS_VERSION)
    second = leave_one_out(user, seed=99, protocol=frozen_protocol, corpus_version=CORPUS_VERSION)

    assert isinstance(first, LeaveOneOut)
    assert first.heldout_work_id == second.heldout_work_id
    assert first.candidate_manifest_sha256 == second.candidate_manifest_sha256
    assert first.candidate_ids == second.candidate_ids


def test_candidate_set_excludes_remaining_library_but_includes_heldout(
    user, governed_corpus, frozen_protocol
) -> None:
    owned = governed_corpus[:5]
    for work in owned:
        _own(user, work, status="completed")

    result = leave_one_out(user, seed=7, protocol=frozen_protocol, corpus_version=CORPUS_VERSION)
    assert result is not None

    heldout = result.heldout_work_id
    remaining_owned = {w.id for w in owned} - {heldout}

    # held-out item is back in the candidate set
    assert heldout in result.candidate_ids
    # the user's other library works are excluded
    assert result.candidate_ids.isdisjoint(remaining_owned)
    assert result.remaining_library_ids == frozenset(remaining_owned)
    # unowned eligible governed works are candidates; unrated and ungoverned
    # works never are. A non-null IGDB rating satisfies the frozen rule even
    # when this fixture deliberately uses an out-of-range value.
    unowned_governed = {w.id for w in governed_corpus[5:12]}
    assert unowned_governed <= result.candidate_ids
    assert governed_corpus[-1].id not in result.candidate_ids
    assert governed_corpus[12].id not in result.candidate_ids
    assert governed_corpus[13].id in result.candidate_ids


def test_completed_unrated_work_is_not_an_evaluation_positive(
    user, governed_corpus, frozen_protocol
) -> None:
    _own(user, governed_corpus[12], status="completed")

    assert leave_one_out(
        user,
        seed=frozen_protocol.loo_seed,
        protocol=frozen_protocol,
        corpus_version=CORPUS_VERSION,
    ) is None


def test_candidate_manifest_sha256_is_stable_across_runs(user, governed_corpus, frozen_protocol) -> None:
    for work in governed_corpus[:4]:
        _own(user, work, status="completed")

    hashes = {
        leave_one_out(user, seed=3, protocol=frozen_protocol,
                      corpus_version=CORPUS_VERSION).candidate_manifest_sha256
        for _ in range(3)
    }
    assert len(hashes) == 1


# --------------------------------------------------------------------------- #
# user split (D-21)                                                            #
# --------------------------------------------------------------------------- #
@pytest.fixture
def two_hundred_user_ids(db, frozen_protocol):
    spec = frozen_protocol.user_split
    total = spec["train"] + spec["validation"] + spec["test"]
    User.objects.bulk_create(User(username=f"synthetic-user-{i:03d}") for i in range(total))
    return list(User.objects.filter(username__startswith="synthetic-user-").values_list("id", flat=True))


def test_user_split_is_disjoint_and_covers_all(two_hundred_user_ids, frozen_protocol) -> None:
    spec = frozen_protocol.user_split
    split = user_split(two_hundred_user_ids, frozen_protocol)

    assert isinstance(split, UserSplit)
    assert (len(split.train), len(split.validation), len(split.test)) == (
        spec["train"],
        spec["validation"],
        spec["test"],
    )
    train, validation, test = set(split.train), set(split.validation), set(split.test)
    assert train.isdisjoint(validation)
    assert train.isdisjoint(test)
    assert validation.isdisjoint(test)
    assert train | validation | test == set(two_hundred_user_ids)


def test_user_split_is_deterministic(two_hundred_user_ids, frozen_protocol) -> None:
    a = user_split(two_hundred_user_ids, frozen_protocol)
    b = user_split(list(reversed(two_hundred_user_ids)), frozen_protocol)
    assert a == b


def test_user_split_rejects_wrong_user_count(two_hundred_user_ids, frozen_protocol) -> None:
    with pytest.raises(ValueError, match="expects exactly"):
        user_split(two_hundred_user_ids[:10], frozen_protocol)
