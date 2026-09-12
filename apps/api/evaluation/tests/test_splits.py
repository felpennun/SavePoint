"""Leave-one-out split + train/validation/test user partition (EVAL-01/02).

Plan 02-08 Task 3. Pins determinism per ``(seed, user_id)``, the candidate-set
rule (governed corpus minus remaining library plus held-out item), a stable
candidate-manifest hash, and a disjoint user partition whose sizes match the
frozen protocol.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from datetime import date

from catalogue.models import CorpusVersion, CuratedLabel, GameWork
from evaluation import protocol as protocol_module
from evaluation.splits import (
    LeaveFractionOut,
    LeaveOneOut,
    UserSplit,
    leave_fraction_out_dominant_tag,
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
                total_rating_count=10,
            )
        )
    works.append(
        GameWork.objects.create(
            canonical_slug="loo-work-unrated",
            original_title="LOO Work Unrated",
            is_dlc=False,
            in_corpus=True,
            corpus_version=CORPUS_VERSION,
            total_rating_count=10,
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
            total_rating_count=4,
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
    # works never are. A rating without the required total volume also fails
    # the frozen eligibility rule.
    unowned_governed = {w.id for w in governed_corpus[5:12]}
    assert unowned_governed <= result.candidate_ids
    assert governed_corpus[-1].id not in result.candidate_ids
    assert governed_corpus[12].id not in result.candidate_ids
    assert governed_corpus[13].id not in result.candidate_ids


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


# --------------------------------------------------------------------------- #
# held-out external-rating floor (protocol_version 14)                        #
# --------------------------------------------------------------------------- #
def test_heldout_selection_skips_a_positive_below_the_external_rating_floor(
    user, governed_corpus, frozen_protocol
) -> None:
    # governed_corpus[13] ("non-null-rating") has rating=101.0, only 4 total
    # ratings -- fails the *candidate* eligibility rule (needs >=5), so it is
    # never a valid heldout target regardless of the new floor. Use a
    # dedicated low-rated-but-eligible work instead.
    low_rated = GameWork.objects.create(
        canonical_slug="loo-work-low-rated",
        original_title="LOO Work Low Rated",
        is_dlc=False,
        in_corpus=True,
        corpus_version=CORPUS_VERSION,
        rating=40.0,
        total_rating_count=10,
    )
    assert frozen_protocol.heldout_min_external_rating == 70.0
    _own(user, low_rated, status="completed")

    assert leave_one_out(
        user, seed=frozen_protocol.loo_seed, protocol=frozen_protocol, corpus_version=CORPUS_VERSION
    ) is None


def test_heldout_selection_only_considers_positives_above_the_floor(
    user, governed_corpus, frozen_protocol
) -> None:
    low_rated = GameWork.objects.create(
        canonical_slug="loo-work-low-rated-2",
        original_title="LOO Work Low Rated 2",
        is_dlc=False,
        in_corpus=True,
        corpus_version=CORPUS_VERSION,
        rating=40.0,
        total_rating_count=10,
    )
    _own(user, low_rated, status="completed")
    _own(user, governed_corpus[0], status="completed")  # rating=80.0, clears the floor

    for _ in range(20):
        result = leave_one_out(
            user, seed=frozen_protocol.loo_seed, protocol=frozen_protocol, corpus_version=CORPUS_VERSION
        )
        assert result.heldout_work_id == governed_corpus[0].id


def test_older_protocol_without_the_floor_field_is_unaffected(
    user, governed_corpus, frozen_protocol
) -> None:
    raw = dict(frozen_protocol.raw)
    raw["relevance"] = {"completed": True, "rating_half_steps_gte": 7}
    legacy_protocol = protocol_module.from_mapping(raw)
    assert legacy_protocol.heldout_min_external_rating is None

    low_rated = GameWork.objects.create(
        canonical_slug="loo-work-low-rated-legacy",
        original_title="LOO Work Low Rated Legacy",
        is_dlc=False,
        in_corpus=True,
        corpus_version=CORPUS_VERSION,
        rating=40.0,
        total_rating_count=10,
    )
    _own(user, low_rated, status="completed")

    result = leave_one_out(
        user, seed=legacy_protocol.loo_seed, protocol=legacy_protocol, corpus_version=CORPUS_VERSION
    )
    assert result is not None
    assert result.heldout_work_id == low_rated.id


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


# --------------------------------------------------------------------------- #
# leave-fraction-out on the dominant content tag (protocol v15)               #
# --------------------------------------------------------------------------- #
DOMINANT_TAG_CORPUS = "dominant-tag-loo-test"


@pytest.fixture
def dominant_tag_corpus(db):  # noqa: ANN001
    CorpusVersion.objects.create(
        version=DOMINANT_TAG_CORPUS, ruleset_sha256="d" * 64, is_active=True, governed_count=10
    )


def _label(slug: str) -> CuratedLabel:
    return CuratedLabel.objects.create(
        name=slug, slug=slug, kind=CuratedLabel.Kind.GENRE, curation_version="test"
    )


def _tagged_work(slug: str, *labels: CuratedLabel, rating: float = 80.0) -> GameWork:
    work = GameWork.objects.create(
        canonical_slug=slug,
        original_title=slug,
        in_corpus=True,
        corpus_version=DOMINANT_TAG_CORPUS,
        rating=rating,
        total_rating_count=10,
        first_release_date=date(2020, 1, 1),
    )
    work.curated_labels.set(labels)
    return work


def _positive(user, work) -> None:
    LibraryEntry.objects.create(user=user, work=work, current_status="completed", rating_half_steps=10)


@pytest.fixture
def dominant_tag_user(db):  # noqa: ANN001
    return User.objects.create_user(username="dominant-tag-loo", password="Dominant-Tag-Loo-9!")


def test_leave_fraction_out_holds_out_a_fraction_of_the_dominant_tag(
    dominant_tag_corpus, dominant_tag_user
) -> None:
    rpg = _label("dominant-tag-rpg")
    puzzle = _label("dominant-tag-puzzle")
    # 6 RPG positives (a clear majority) + 1 puzzle positive.
    for index in range(6):
        _positive(dominant_tag_user, _tagged_work(f"dominant-tag-rpg-{index}", rpg))
    _positive(dominant_tag_user, _tagged_work("dominant-tag-puzzle-0", puzzle))

    frozen = protocol_module.load()
    result = leave_fraction_out_dominant_tag(
        dominant_tag_user, seed=frozen.loo_seed, protocol=frozen, corpus_version=DOMINANT_TAG_CORPUS,
        eligibility_cutoff_date=date(2026, 9, 12),
    )

    assert isinstance(result, LeaveFractionOut)
    assert result.dominant_tag == "tag:dominant-tag-rpg"
    # ceil(0.3 * 6) == 2, and removing 2 of 6 RPG positives (4 remain) should
    # not knock RPG out of first place against a single puzzle positive.
    assert len(result.heldout_work_ids) == 2
    assert result.achieved_rank == 1
    assert result.heldout_work_ids <= {
        w.id for w in GameWork.objects.filter(canonical_slug__startswith="dominant-tag-rpg-")
    }
    # The held-out items return to the shared candidate set.
    assert result.heldout_work_ids <= result.candidate_ids
    assert result.candidate_manifest_sha256


def test_leave_fraction_out_never_holds_out_fewer_than_one(
    dominant_tag_corpus, dominant_tag_user
) -> None:
    rpg = _label("dominant-tag-rpg-solo")
    # Only one eligible positive of the dominant tag: ceil(0.3 * 1) == 1, and
    # the floor of 1 is accepted unconditionally regardless of rank outcome.
    _positive(dominant_tag_user, _tagged_work("dominant-tag-rpg-solo-0", rpg))

    frozen = protocol_module.load()
    result = leave_fraction_out_dominant_tag(
        dominant_tag_user, seed=frozen.loo_seed, protocol=frozen, corpus_version=DOMINANT_TAG_CORPUS,
        eligibility_cutoff_date=date(2026, 9, 12),
    )

    assert isinstance(result, LeaveFractionOut)
    assert len(result.heldout_work_ids) == 1


def test_leave_fraction_out_is_deterministic_per_seed_and_user(
    dominant_tag_corpus, dominant_tag_user
) -> None:
    rpg = _label("dominant-tag-rpg-determinism")
    for index in range(6):
        _positive(dominant_tag_user, _tagged_work(f"dominant-tag-rpg-determinism-{index}", rpg))

    frozen = protocol_module.load()
    first = leave_fraction_out_dominant_tag(
        dominant_tag_user, seed=99, protocol=frozen, corpus_version=DOMINANT_TAG_CORPUS,
        eligibility_cutoff_date=date(2026, 9, 12),
    )
    second = leave_fraction_out_dominant_tag(
        dominant_tag_user, seed=99, protocol=frozen, corpus_version=DOMINANT_TAG_CORPUS,
        eligibility_cutoff_date=date(2026, 9, 12),
    )

    assert first.heldout_work_ids == second.heldout_work_ids
    assert first.candidate_manifest_sha256 == second.candidate_manifest_sha256


def test_leave_fraction_out_returns_none_without_any_positive(
    dominant_tag_corpus, dominant_tag_user
) -> None:
    frozen = protocol_module.load()
    assert leave_fraction_out_dominant_tag(
        dominant_tag_user, seed=frozen.loo_seed, protocol=frozen, corpus_version=DOMINANT_TAG_CORPUS,
        eligibility_cutoff_date=date(2026, 9, 12),
    ) is None


def test_leave_fraction_out_returns_none_below_the_external_rating_floor(
    dominant_tag_corpus, dominant_tag_user
) -> None:
    rpg = _label("dominant-tag-rpg-lowrated")
    # Below the frozen heldout_min_external_rating (70): never eligible for
    # this mechanism, exactly like leave_one_out's own floor.
    _positive(dominant_tag_user, _tagged_work("dominant-tag-rpg-lowrated-0", rpg, rating=40.0))

    frozen = protocol_module.load()
    assert leave_fraction_out_dominant_tag(
        dominant_tag_user, seed=frozen.loo_seed, protocol=frozen, corpus_version=DOMINANT_TAG_CORPUS,
        eligibility_cutoff_date=date(2026, 9, 12),
    ) is None
