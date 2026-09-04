"""Tests for the popularity-v1 baseline (Plan 01-07 Task 3, REC-02)."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from rest_framework.test import APIClient

from catalogue.models import GameWork
from library import services
from library.models import LibraryEntry
from library.popularity import rank_popularity_v1

User = get_user_model()


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="pop-user-a", password="Pop-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="pop-user-b", password="Pop-User-B-Pass-9!")


@pytest.mark.django_db
def test_zero_activity_returns_explicit_empty_list() -> None:
    result = rank_popularity_v1()
    assert result["results"] == []
    assert result["algorithm_id"] == "popularity-v1"


@pytest.mark.django_db
def test_dto_always_declares_algorithm_id_and_limitation() -> None:
    result = rank_popularity_v1()
    assert result["algorithm_id"] == "popularity-v1"
    assert "generated_at" in result
    assert "input_snapshot_sha256" in result
    assert "not personalized" in result["limitation"].lower()


@pytest.mark.django_db
def test_completed_outranks_playing_outranks_pending(user_a) -> None:  # noqa: ANN001
    completed = GameWork.objects.create(canonical_slug="pop-completed", original_title="Completed Game")
    playing = GameWork.objects.create(canonical_slug="pop-playing", original_title="Playing Game")
    pending = GameWork.objects.create(canonical_slug="pop-pending", original_title="Pending Game")
    LibraryEntry.objects.create(user=user_a, work=completed, current_status="completed")
    LibraryEntry.objects.create(user=user_a, work=playing, current_status="playing")
    LibraryEntry.objects.create(user=user_a, work=pending, current_status="pending")

    result = rank_popularity_v1()
    slugs = [r["slug"] for r in result["results"]]
    assert slugs == ["pop-completed", "pop-playing", "pop-pending"]


@pytest.mark.django_db
def test_rating_contributes_to_score(user_a, user_b) -> None:  # noqa: ANN001
    work = GameWork.objects.create(canonical_slug="pop-rated", original_title="Rated Game")
    LibraryEntry.objects.create(user=user_a, work=work, current_status="pending")
    services.set_rating(user=user_a, work=work, rating_half_steps=10)

    unrated = GameWork.objects.create(canonical_slug="pop-unrated", original_title="Unrated Game")
    LibraryEntry.objects.create(user=user_b, work=unrated, current_status="pending")

    result = rank_popularity_v1()
    scores = {r["slug"]: r["score"] for r in result["results"]}
    assert scores["pop-rated"] > scores["pop-unrated"]


@pytest.mark.django_db
def test_ties_broken_by_work_uuid_ascending(user_a) -> None:  # noqa: ANN001
    work_1 = GameWork.objects.create(canonical_slug="pop-tie-1", original_title="Tie Game 1")
    work_2 = GameWork.objects.create(canonical_slug="pop-tie-2", original_title="Tie Game 2")
    LibraryEntry.objects.create(user=user_a, work=work_1, current_status="playing")
    LibraryEntry.objects.create(user=user_a, work=work_2, current_status="playing")

    result = rank_popularity_v1()
    tied = [r for r in result["results"] if r["slug"] in ("pop-tie-1", "pop-tie-2")]
    assert len(tied) == 2
    assert tied[0]["score"] == tied[1]["score"]
    expected_first = str(min(work_1.id, work_2.id))
    assert tied[0]["work_id"] == expected_first


@pytest.mark.django_db
def test_same_input_produces_same_hash_and_order(user_a) -> None:  # noqa: ANN001
    work = GameWork.objects.create(canonical_slug="pop-stable", original_title="Stable Game")
    LibraryEntry.objects.create(user=user_a, work=work, current_status="completed")

    cutoff = datetime.now(timezone.utc)
    first = rank_popularity_v1(cutoff=cutoff)
    second = rank_popularity_v1(cutoff=cutoff)
    assert first["input_snapshot_sha256"] == second["input_snapshot_sha256"]
    assert first["results"] == second["results"]


@pytest.mark.django_db
def test_hash_changes_when_underlying_data_changes(user_a) -> None:  # noqa: ANN001
    work = GameWork.objects.create(canonical_slug="pop-changing", original_title="Changing Game")
    LibraryEntry.objects.create(user=user_a, work=work, current_status="pending")

    before = rank_popularity_v1()
    services.set_rating(user=user_a, work=work, rating_half_steps=5)
    after = rank_popularity_v1()

    assert before["input_snapshot_sha256"] != after["input_snapshot_sha256"]


@pytest.mark.django_db
def test_popularity_endpoint_is_public() -> None:
    client = APIClient()
    response = client.get("/api/library/popularity/")
    assert response.status_code == 200
    body = response.json()
    assert body["algorithm_id"] == "popularity-v1"


@pytest.mark.django_db(transaction=True)
def test_concurrent_status_writes_never_produce_partial_mixed_result(user_a) -> None:  # noqa: ANN001
    work = GameWork.objects.create(canonical_slug="pop-concurrent", original_title="Concurrent Game")
    errors: list[BaseException] = []
    results: list[dict] = []

    def _writer() -> None:
        try:
            client = APIClient()
            client.force_authenticate(user=user_a)
            client.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connections.close_all()

    def _reader() -> None:
        try:
            results.append(rank_popularity_v1())
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_writer), threading.Thread(target=_reader)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent read/write raised: {errors}"
    # Every concurrent read still returns a well-formed, self-consistent
    # DTO -- never a partial/corrupt result from racing the writer.
    for result in results:
        assert isinstance(result["input_snapshot_sha256"], str) and len(result["input_snapshot_sha256"]) == 64
        assert isinstance(result["results"], list)
