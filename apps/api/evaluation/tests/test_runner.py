"""Shared-candidate evaluation harness tests (EVAL-01, DATA-07)."""

from __future__ import annotations

import copy
import uuid
from datetime import date, datetime, timezone

import pytest
from django.contrib.auth import get_user_model

from accounts.models import DemoAccountIdentity, demo_identity_anchor_id
from catalogue.models import CorpusRatingSnapshot, CorpusVersion, GameWork
from evaluation import protocol as protocol_module
from evaluation.candidates import build
from evaluation.runner import SnapshotCoverageError, run, validate_active_population, validate_snapshot_coverage
from library.models import LibraryEntry

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
    return protocol_module.from_mapping(mapping)


@pytest.fixture
def runner_fixture(db):
    works = [
        GameWork.objects.create(
            canonical_slug=f"runner-work-{index}",
            original_title=f"Runner Work {index}",
            rating=80.0 if index == 0 else None,
            rating_count=None if index == 0 else (1 if index == 1 else None),
            total_rating_count=1 if index == 1 else None,
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

    candidate_ids, heldout_id, candidate_sha256 = build(
        user, frozen_protocol, CORPUS_VERSION
    )

    assert heldout_id == works[0].id
    assert set(candidate_ids) == {works[0].id, works[1].id}
    assert works[2].id not in candidate_ids
    assert works[3].id not in candidate_ids
    assert candidate_sha256


def test_runner_population_contract_matches_active_split(runner_fixture, frozen_protocol):
    user, _works, _identity = runner_fixture
    report = validate_active_population([user], frozen_protocol, CORPUS_VERSION)
    assert report == {"active_user_count": 1, "expected_user_count": 1, "split_total": 1}


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
    works[1].save(update_fields=["rating"])

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
    works[1].save(update_fields=["rating"])

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
        "protocol_version",
        "split",
        "simulation",
        "limitation",
    } <= set(artifact)
    metrics = artifact["algorithms"]["only"]["aggregates"]
    assert set(metrics) == {"5", "10", "20"}
    assert set(metrics["10"]) == {"precision", "recall", "ndcg", "map"}
