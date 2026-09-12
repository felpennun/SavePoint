"""Shared-candidate evaluation harness tests (EVAL-01, DATA-07)."""

from __future__ import annotations

import copy
import uuid
from datetime import date, datetime, timezone

import pytest
from django.contrib.auth import get_user_model

from accounts.models import DemoAccountIdentity, demo_identity_anchor_id
from catalogue.corpus import evaluation_candidate_works
from catalogue.models import CorpusRatingSnapshot, CorpusVersion, CuratedLabel, GameWork
from evaluation import protocol as protocol_module
from evaluation.candidates import build
from evaluation.runner import (
    SnapshotCoverageError,
    build_evaluation_context,
    default_algorithms,
    precompute_shared_content_signals,
    run,
    validate_active_population,
    validate_snapshot_coverage,
)
from library.models import LibraryEntry
from recommendations.published import CONTENT_ALGORITHM_IDS

User = get_user_model()
CORPUS_VERSION = "runner-test"


@pytest.fixture
def frozen_protocol():
    mapping = copy.deepcopy(protocol_module.load().raw)
    mapping["corpus_version"] = CORPUS_VERSION
    mapping["snapshot_sha256"] = None
    mapping["popscore_snapshot_sha256"] = None
    mapping["user_split"] = {"train": 0, "validation": 0, "test": 1, "seed": 20260908}
    mapping["synthetic_population"]["phase_3_population"] = 1
    # This suite exercises run()/build() infrastructure (shared candidate
    # sets, drift detection, artifact shape), not which LOO mechanism is
    # live in the real frozen protocol -- pin the simple single-item
    # strategy so these fixtures (small, mostly untagged works) don't need
    # the content-profile machinery leave_fraction_out_dominant_tag
    # requires. That mechanism gets its own dedicated tests in
    # test_splits.py.
    mapping["split"]["strategy"] = "leave_one_out_per_user"
    return protocol_module.from_mapping(mapping)


@pytest.fixture
def runner_fixture(db):
    works = [
        GameWork.objects.create(
            canonical_slug=f"runner-work-{index}",
            original_title=f"Runner Work {index}",
            rating=80.0 if index == 0 else None,
            rating_count=None if index == 0 else (1 if index == 1 else None),
            total_rating_count=10 if index == 0 else (1 if index == 1 else None),
            in_corpus=True,
            corpus_version=CORPUS_VERSION,
            first_release_date=date(2020, 1, 1),
        )
        for index in range(4)
    ]
    CorpusVersion.objects.create(
        version=CORPUS_VERSION,
        ruleset_sha256="a" * 64,
        is_active=True,
        governed_count=len(works),
    )
    CorpusRatingSnapshot.objects.create(
        work=works[0],
        corpus_version=CORPUS_VERSION,
        source="igdb",
        rating=80.0,
        rating_count=10,
        retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    user = User.objects.create_user(username="runner-synthetic")
    identity = DemoAccountIdentity.objects.create(
        id=demo_identity_anchor_id("runner-synthetic"),
        seed_key="runner-synthetic",
        user=user,
        marker="synthetic-eval-user",
        display_label="Synthetic runner fixture",
    )
    LibraryEntry.objects.create(user=user, work=works[0], current_status="completed")
    return user, works, identity


def test_build_returns_one_shared_candidate_set(runner_fixture, frozen_protocol):
    user, works, _identity = runner_fixture

    candidate_ids, heldout_ids, candidate_sha256 = build(
        user, frozen_protocol, CORPUS_VERSION
    )

    assert heldout_ids == frozenset({works[0].id})
    assert set(candidate_ids) == {works[0].id}
    assert works[1].id not in candidate_ids
    assert works[2].id not in candidate_ids
    assert works[3].id not in candidate_ids
    assert candidate_sha256


@pytest.mark.django_db
def test_evaluation_candidate_works_is_not_duplicated_by_multi_label_works(runner_fixture) -> None:
    # Regression (2026-09-11): .filter(curated_labels__isnull=False) JOINs the
    # M2M and returns one row per label, so a work with N curated labels used
    # to be scored and ranked N times by run() -- inflating precision/recall/
    # nDCG/MAP past their [0,1] bounds whenever it ranked highly. The fix
    # (evaluation/runner.py) reads that same list via Exists(), matching the
    # product-facing query in recommendations/content/rank.py.
    _user, works, _identity = runner_fixture
    work = works[0]
    for index, kind in enumerate((CuratedLabel.Kind.GENRE, CuratedLabel.Kind.THEME, CuratedLabel.Kind.MODE)):
        label = CuratedLabel.objects.create(
            name=f"Runner Label {index}", slug=f"runner-label-{index}", kind=kind,
            curation_version="test",
        )
        work.curated_labels.add(label)

    naive_row_count = (
        evaluation_candidate_works(CORPUS_VERSION).filter(curated_labels__isnull=False).count()
    )
    assert naive_row_count > 1, "fixture must exercise the multi-label duplication path"

    from django.db.models import Exists, OuterRef

    deduped_ids = list(
        evaluation_candidate_works(CORPUS_VERSION)
        .filter(Exists(GameWork.objects.filter(pk=OuterRef("pk"), curated_labels__isnull=False)))
        .values_list("id", flat=True)
    )
    assert deduped_ids.count(work.id) == 1
    assert len(deduped_ids) == len(set(deduped_ids))


def test_runner_population_contract_matches_active_split(runner_fixture, frozen_protocol):
    user, _works, _identity = runner_fixture
    report = validate_active_population([user], frozen_protocol, CORPUS_VERSION)
    assert report == {"active_user_count": 1, "expected_user_count": 1, "split_total": 1}


def test_offline_runner_uses_the_product_content_algorithm_catalog() -> None:
    assert set(default_algorithms()) == {
        "random-v1",
        "popularity-v1",
        *CONTENT_ALGORITHM_IDS,
    }


def test_offline_runner_order_matches_the_frozen_protocol() -> None:
    # run_evaluation_parallel compares these position by position, so a set
    # match is not enough: the order must equal protocol.tuning.evaluation_algorithms.
    declared = protocol_module.load().raw["tuning"]["evaluation_algorithms"]
    assert list(default_algorithms()) == declared


def test_build_skips_user_without_eligible_positive(runner_fixture, frozen_protocol):
    _user, works, _identity = runner_fixture
    user = User.objects.create_user(username="runner-unrated-only")
    DemoAccountIdentity.objects.create(
        id=demo_identity_anchor_id("runner-unrated-only"),
        seed_key="runner-unrated-only",
        user=user,
        marker="synthetic-eval-user",
        display_label="Synthetic unrated-only fixture",
    )
    LibraryEntry.objects.create(user=user, work=works[2], current_status="completed")

    assert build(user, frozen_protocol, CORPUS_VERSION) is None


def test_runner_asserts_algorithms_receive_same_candidate_set(runner_fixture, frozen_protocol):
    seen: dict[str, set[uuid.UUID]] = {}

    def ranker(*, algorithm_id, candidate_ids, **_kwargs):
        seen[algorithm_id] = set(candidate_ids)
        return list(candidate_ids)

    artifact = run(
        frozen_protocol,
        CORPUS_VERSION,
        {"first": ranker, "second": ranker},
        split="test",
    )

    assert seen["first"] == seen["second"]
    assert artifact["split_manifest_sha256"]


def test_runner_rejects_candidate_set_drift(runner_fixture, frozen_protocol):
    def first(*, candidate_ids, **_kwargs):
        return list(candidate_ids)

    def second(*, candidate_ids, **_kwargs):
        return {
            "candidate_ids": list(candidate_ids)[:-1],
            "ranked_ids": list(candidate_ids),
        }

    with pytest.raises(AssertionError, match="candidate set"):
        run(
            frozen_protocol,
            CORPUS_VERSION,
            {"first": first, "second": second},
            split="test",
        )


def test_snapshot_coverage_ignores_governed_unrated_work(runner_fixture):
    _user, _works, _identity = runner_fixture

    validate_snapshot_coverage(CORPUS_VERSION)


def test_snapshot_coverage_rejects_missing_live_rating_snapshot(runner_fixture):
    _user, works, _identity = runner_fixture
    works[1].rating = 75.0
    works[1].total_rating_count = 10
    works[1].save(update_fields=["rating", "total_rating_count"])

    with pytest.raises(SnapshotCoverageError, match="missing"):
        validate_snapshot_coverage(CORPUS_VERSION)


def test_snapshot_coverage_rejects_version_mismatch(runner_fixture):
    _user, works, _identity = runner_fixture
    CorpusRatingSnapshot.objects.create(
        work=works[1],
        corpus_version="wrong-version",
        source="igdb",
        rating=75.0,
        rating_count=5,
        retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    works[1].rating = 75.0
    works[1].total_rating_count = 10
    works[1].save(update_fields=["rating", "total_rating_count"])

    with pytest.raises(SnapshotCoverageError, match="mismatch"):
        validate_snapshot_coverage(CORPUS_VERSION)


def test_artifact_contains_frozen_fields_and_metrics(runner_fixture, frozen_protocol):
    def ranker(*, candidate_ids, **_kwargs):
        return list(candidate_ids)

    artifact = run(
        frozen_protocol,
        CORPUS_VERSION,
        {"only": ranker},
        split="test",
    )

    assert {
        "code_commit",
        "protocol_sha256",
        "corpus_version",
        "snapshot_sha256",
        "popscore_snapshot_sha256",
        "feature_set_version",
        "seeds",
        "split_manifest_sha256",
        "algorithms",
        "statistical_comparisons",
        "protocol_version",
        "split",
        "simulation",
        "limitation",
    } <= set(artifact)
    metrics = artifact["algorithms"]["only"]["aggregates"]
    assert set(metrics) == {"5", "10", "20"}
    assert set(metrics["10"]) == {"precision", "recall", "ndcg", "map"}
    headline = artifact["statistical_comparisons"][frozen_protocol.headline]
    assert headline["family"] == frozen_protocol.headline
    assert headline["configuration"]["seed"] == frozen_protocol.loo_seed


@pytest.mark.django_db
def test_run_with_a_precomputed_context_matches_run_with_none(runner_fixture, frozen_protocol) -> None:
    # 2026-09-11: run_evaluation_parallel builds one context in its parent
    # process and forks workers that reuse it (see precompute_shared_content_
    # signals below); this is the guard that the plumbing itself -- passing
    # `context=` instead of letting run() build its own -- never changes a
    # scored value.
    def ranker(*, candidate_ids, **_kwargs):
        return list(candidate_ids)

    fresh = run(frozen_protocol, CORPUS_VERSION, {"only": ranker}, split="test")

    context = build_evaluation_context(frozen_protocol, CORPUS_VERSION, split="test")
    reused = run(frozen_protocol, CORPUS_VERSION, {"only": ranker}, split="test", context=context)

    def strip_timing(artifact: dict) -> dict:
        artifact = copy.deepcopy(artifact)
        for algorithm in artifact["algorithms"].values():
            algorithm.pop("duration_seconds", None)
        return artifact

    assert strip_timing(fresh) == strip_timing(reused)


@pytest.mark.django_db
def test_run_rejects_a_context_built_for_a_different_split(runner_fixture, frozen_protocol) -> None:
    def ranker(*, candidate_ids, **_kwargs):
        return list(candidate_ids)

    context = build_evaluation_context(frozen_protocol, CORPUS_VERSION, split="test")
    with pytest.raises(ValueError, match="context was built for split"):
        run(frozen_protocol, CORPUS_VERSION, {"only": ranker}, split="train", context=context)


@pytest.mark.django_db
def test_precompute_shared_content_signals_matches_uncached_rank_content_v1() -> None:
    # Standalone from the LOO/protocol machinery above -- this is purely
    # about whether precompute_shared_content_signals populates the same
    # cache keys rank_content_v1 reads, with the same values an uncached
    # call would compute for itself.
    from recommendations.content.features import (
        all_family_idf_profiles,
        corpus_rating_prior,
        tag_rating_profile,
    )
    from recommendations.content.rank import _load_candidate_vectors, rank_content_v1
    from recommendations.content.variants import ALGORITHM_REGISTRY

    corpus_version = "runner-precompute-test"
    CorpusVersion.objects.create(
        version=corpus_version, ruleset_sha256="c" * 64, is_active=True, governed_count=4
    )
    label = CuratedLabel.objects.create(
        name="Precompute RPG", slug="precompute-rpg", kind=CuratedLabel.Kind.GENRE,
        curation_version="test",
    )

    def make_work(slug: str) -> GameWork:
        work = GameWork.objects.create(
            canonical_slug=slug,
            original_title=slug,
            in_corpus=True,
            corpus_version=corpus_version,
            rating=80.0,
            total_rating_count=10,
            first_release_date=date(2020, 1, 1),
        )
        work.curated_labels.add(label)
        CorpusRatingSnapshot.objects.create(
            work=work, corpus_version=corpus_version, source="igdb", rating=80.0,
            rating_count=10, total_rating_count=10,
            retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
        )
        return work

    candidate = make_work("precompute-candidate")
    user = User.objects.create_user(username="precompute-user")
    for index in range(3):
        seed = make_work(f"precompute-seed-{index}")
        LibraryEntry.objects.create(
            user=user, work=seed, current_status="completed", rating_half_steps=10
        )

    works = [candidate]
    family_idf = all_family_idf_profiles(corpus_version)
    tag_profile = tag_rating_profile(corpus_version)
    vectors = _load_candidate_vectors(
        works, ALGORITHM_REGISTRY["content-cbf-weighted-v1"], corpus_version, family_idf=family_idf
    )
    context = {
        "corpus_version": corpus_version,
        "candidates_by_user": [(user, [candidate.id], candidate.id, "hash")],
        "evaluation_prepared": {
            "works": works,
            "vectors": vectors,
            "tag_profile": tag_profile,
            "family_idf": family_idf,
            "snapshot_stats": {candidate.id: (80.0, 10, 10)},
            "rating_prior": corpus_rating_prior(corpus_version, eligibility_cutoff_date=date.today()),
        },
    }

    precompute_shared_content_signals(context)
    prepared = context["evaluation_prepared"]
    assert candidate.id in prepared["_rating_term_cache"]
    assert (user.pk, candidate.id) in prepared["_similarity_cache"]
    assert user.pk in prepared["_profile_cache"]

    cached = rank_content_v1(
        user, "content-cbf-weighted-v1", corpus_version=corpus_version,
        candidate_ids={candidate.id}, prepared=prepared,
    )
    uncached = rank_content_v1(
        user, "content-cbf-weighted-v1", corpus_version=corpus_version,
        candidate_ids={candidate.id},
    )
    assert cached["insufficient_history"] is False
    assert cached["results"] == uncached["results"]
