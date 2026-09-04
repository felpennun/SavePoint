"""Tests for the demo interaction seed (Plan 01-16).

Task 1's `<verify>` runs only `-k manifest` (structural checks against the
committed data/demo/seed-v1.json, no database needed) before any schema
exists to load into; Task 2's `<verify>` runs the full file plus
popularity tests once the command exists.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.db import connections

from accounts.management.commands.seed_demo import _check_no_sensitive_keys, FORBIDDEN_KEY_SUBSTRINGS
from accounts.models import DEMO_ACCOUNT_ANCHOR_ID, DemoAccountAnchor
from catalogue.models import GameWork
from library.models import LibraryEntry

User = get_user_model()

SEED_PATH = Path(__file__).resolve().parents[4] / "data" / "demo" / "seed-v1.json"


def _load_manifest() -> dict:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Task 1: manifest-only structural tests (no database mutation)
# ---------------------------------------------------------------------------


def test_manifest_exists_and_is_valid_json() -> None:
    manifest = _load_manifest()
    assert manifest["schema_version"] == 1
    assert manifest["seed_version"] == "seed-v1"


def test_manifest_contains_no_sensitive_keys() -> None:
    manifest = _load_manifest()
    # Should not raise.
    _check_no_sensitive_keys(manifest)

    # And the check itself actually catches a planted violation.
    with pytest.raises(CommandError):
        _check_no_sensitive_keys({"nested": {"api_token": "should-be-rejected"}})


def test_forbidden_key_substrings_cover_common_credential_shapes() -> None:
    assert "password" in FORBIDDEN_KEY_SUBSTRINGS
    assert "token" in FORBIDDEN_KEY_SUBSTRINGS
    assert "secret" in FORBIDDEN_KEY_SUBSTRINGS


def test_manifest_interactions_hash_is_reproducible() -> None:
    manifest = _load_manifest()

    def canonical_bytes(value):
        return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

    actual = hashlib.sha256(canonical_bytes(manifest["interactions"])).hexdigest()
    assert actual == manifest["interactions_sha256"]


def test_manifest_references_only_null_or_1_to_10_ratings() -> None:
    manifest = _load_manifest()
    for interaction in manifest["interactions"]:
        rating = interaction["rating_half_steps"]
        assert rating is None or 1 <= rating <= 10


def test_manifest_declares_exactly_six_expected_popularity_results() -> None:
    manifest = _load_manifest()
    assert len(manifest["expected_popularity_v1"]["results"]) == 6
    assert len(manifest["interactions"]) == 6


def test_manifest_expected_results_are_score_ordered() -> None:
    manifest = _load_manifest()
    scores = [row["score"] for row in manifest["expected_popularity_v1"]["results"]]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Task 2: full load tests (require schema + account + catalogue)
# ---------------------------------------------------------------------------


@pytest.fixture
def demo_account(db):  # noqa: ANN001
    user = User.objects.create_user(username="seed-demo-account", password="Seed-Demo-Account-Pass-9!")
    return DemoAccountAnchor.objects.create(id=DEMO_ACCOUNT_ANCHOR_ID, user=user)


@pytest.fixture
def seeded_works(db):  # noqa: ANN001
    """Create GameWork rows matching the manifest's referenced UUIDs."""
    manifest = _load_manifest()
    works = []
    for interaction in manifest["interactions"]:
        work = GameWork.objects.create(
            id=interaction["work_id"],
            canonical_slug=interaction["work_slug"],
            original_title=interaction["work_slug"],
        )
        works.append(work)
    return works


@pytest.mark.django_db
def test_seed_fails_closed_without_bootstrap_account(seeded_works) -> None:  # noqa: ANN001
    with pytest.raises(CommandError, match="Demo account not found"):
        call_command("seed_demo")
    assert LibraryEntry.objects.count() == 0


@pytest.mark.django_db
def test_seed_fails_closed_when_a_referenced_work_is_missing(demo_account) -> None:  # noqa: ANN001
    # No seeded_works fixture -- none of the manifest's works exist.
    with pytest.raises(CommandError, match="unknown work"):
        call_command("seed_demo")
    assert LibraryEntry.objects.count() == 0


@pytest.mark.django_db
def test_seed_loads_and_matches_expected_popularity_exactly(demo_account, seeded_works) -> None:  # noqa: ANN001
    from io import StringIO

    out = StringIO()
    call_command("seed_demo", stdout=out)

    manifest = _load_manifest()
    assert LibraryEntry.objects.count() == 6

    from library.popularity import rank_popularity_v1

    actual = rank_popularity_v1()
    expected_ids = [row["work_id"] for row in manifest["expected_popularity_v1"]["results"]]
    actual_ids_in_order = [r["work_id"] for r in actual["results"] if r["work_id"] in set(expected_ids)]
    assert actual_ids_in_order == expected_ids

    expected_scores = {row["work_id"]: row["score"] for row in manifest["expected_popularity_v1"]["results"]}
    for row in actual["results"]:
        if row["work_id"] in expected_scores:
            assert row["score"] == expected_scores[row["work_id"]]


@pytest.mark.django_db
def test_seed_never_touches_password_or_reads_credential_env(demo_account, seeded_works, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.delenv("DEMO_USERNAME", raising=False)
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    original_hash = demo_account.user.password

    call_command("seed_demo")

    demo_account.user.refresh_from_db()
    assert demo_account.user.password == original_hash


@pytest.mark.django_db
def test_seed_is_idempotent(demo_account, seeded_works) -> None:  # noqa: ANN001
    call_command("seed_demo")
    first_count = LibraryEntry.objects.count()
    first_ratings = list(LibraryEntry.objects.values_list("work_id", "current_status", "rating_half_steps").order_by("work_id"))

    call_command("seed_demo")
    second_count = LibraryEntry.objects.count()
    second_ratings = list(LibraryEntry.objects.values_list("work_id", "current_status", "rating_half_steps").order_by("work_id"))

    assert first_count == second_count == 6
    assert first_ratings == second_ratings


@pytest.mark.django_db(transaction=True)
def test_concurrent_seed_invocations_leave_no_partial_state(demo_account, seeded_works) -> None:  # noqa: ANN001
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            call_command("seed_demo")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent seed raised: {errors}"
    assert LibraryEntry.objects.count() == 6
