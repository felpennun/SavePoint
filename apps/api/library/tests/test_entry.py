"""Tests for the library status endpoint (Plan 01-04 Task 1, LIB-01/D-09/D-14)."""

from __future__ import annotations

import threading

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from rest_framework.test import APIClient

from catalogue.models import AssetAttribution, GameRelease, GameWork, Platform
from library.models import LibraryEntry, StatusTransition

User = get_user_model()


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="tracer-game", original_title="Tracer Game")


@pytest.fixture
def dlc_work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="tracer-game-dlc", original_title="Tracer Game DLC", is_dlc=True)


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="entry-user-a", password="Entry-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="entry-user-b", password="Entry-User-B-Pass-9!")


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_my_library_lists_actioned_entries_and_excludes_untouched_ones(work, user_a) -> None:  # noqa: ANN001
    other_work = GameWork.objects.create(canonical_slug="untouched-game", original_title="Untouched Game")
    unrated_work = GameWork.objects.create(canonical_slug="no-status-game", original_title="No Status Game")
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    LibraryEntry.objects.create(user=user_a, work=other_work, current_status=None)  # never actioned
    LibraryEntry.objects.create(user=user_a, work=unrated_work, current_status=None, rating_half_steps=8)

    client = _client_for(user_a)
    response = client.get("/api/library/entries/")
    assert response.status_code == 200
    body = response.json()
    assert {item["work_slug"] for item in body["items"]} == {"tracer-game", "no-status-game"}
    assert body["summary"]["playing"] == 1
    assert body["summary"]["pending"] == 0


@pytest.mark.django_db
def test_my_library_lists_a_rating_without_a_status_after_reload(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/rating/",
        {"rating_half_steps": 10},
        format="json",
    )

    assert response.status_code == 200
    items = client.get("/api/library/entries/").json()["items"]
    assert len(items) == 1
    assert items[0]["work_slug"] == "tracer-game"
    assert items[0]["status"] is None
    assert items[0]["rating_half_steps"] == 10


@pytest.mark.django_db
def test_my_library_returns_cover_and_platform_metadata(work, user_a) -> None:  # noqa: ANN001
    platform = Platform.objects.create(name="PC", slug="pc")
    GameRelease.objects.create(work=work, platform=platform, release_name="Tracer Game (PC)")
    AssetAttribution.objects.create(
        work=work,
        file_url="https://cdn.example.test/tracer-game.jpg",
        creator="Catalogue source",
        licence="Catalogue terms",
        licence_url="https://example.test/licence",
        source_url="https://example.test/tracer-game",
        display_allowed=True,
    )
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")

    item = _client_for(user_a).get("/api/library/entries/").json()["items"][0]

    assert item["cover"]["is_placeholder"] is False
    assert item["cover"]["url"] == "https://cdn.example.test/tracer-game.jpg"
    assert item["platform_summary"] == "PC"


@pytest.mark.django_db
def test_my_library_counts_a_work_once_when_user_owns_multiple_copies(work, user_a) -> None:  # noqa: ANN001
    platform = Platform.objects.create(name="PC", slug="pc")
    release = GameRelease.objects.create(work=work, platform=platform, release_name="Tracer Game (PC)")
    LibraryEntry.objects.create(user=user_a, work=work, current_status="completed")
    work.owned_copies.create(user=user_a, release=release, format="physical", idempotency_key="copy-1")
    work.owned_copies.create(user=user_a, release=release, format="digital", idempotency_key="copy-2")

    body = _client_for(user_a).get("/api/library/entries/").json()

    assert len(body["items"]) == 1
    assert body["items"][0]["owned_copy_count"] == 2
    assert body["summary"] == {"pending": 0, "playing": 0, "completed": 1, "abandoned": 0}


@pytest.mark.django_db
def test_my_library_is_owner_scoped(work, user_a, user_b) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="completed")

    response_b = _client_for(user_b).get("/api/library/entries/")
    assert response_b.json()["items"] == []


@pytest.mark.django_db
def test_my_library_requires_authentication(work) -> None:  # noqa: ANN001
    response = APIClient().get("/api/library/entries/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_set_status_persists_and_reloads(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")

    assert response.status_code == 200
    assert response.json() == {"status": "playing", "changed": True}

    entry = LibraryEntry.objects.get(user=user_a, work=work)
    assert entry.current_status == "playing"


@pytest.mark.django_db
def test_get_status_returns_none_before_any_status_is_set(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.get(f"/api/library/entries/{work.id}/status/")
    assert response.status_code == 200
    assert response.json() == {"status": None}


@pytest.mark.django_db
def test_get_status_reflects_the_last_saved_value_after_reload(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    client.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")

    # A fresh GET (simulating a page reload) must read the persisted
    # PostgreSQL value, not any client-side optimistic guess.
    reload_response = client.get(f"/api/library/entries/{work.id}/status/")
    assert reload_response.status_code == 200
    assert reload_response.json() == {"status": "playing"}


@pytest.mark.django_db
def test_get_status_is_scoped_to_the_requesting_user(work, user_a, user_b) -> None:  # noqa: ANN001
    client_a = _client_for(user_a)
    client_b = _client_for(user_b)
    client_a.post(f"/api/library/entries/{work.id}/status/", {"status": "completed"}, format="json")

    response_b = client_b.get(f"/api/library/entries/{work.id}/status/")
    assert response_b.json() == {"status": None}


@pytest.mark.django_db
def test_identical_retry_does_not_duplicate_history(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    client.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")
    second = client.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")

    assert second.json()["changed"] is False
    entry = LibraryEntry.objects.get(user=user_a, work=work)
    assert StatusTransition.objects.filter(entry=entry).count() == 1


@pytest.mark.django_db
def test_status_change_appends_transaction_history(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    client.post(f"/api/library/entries/{work.id}/status/", {"status": "pending"}, format="json")
    client.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")
    client.post(f"/api/library/entries/{work.id}/status/", {"status": "completed"}, format="json")

    entry = LibraryEntry.objects.get(user=user_a, work=work)
    history = list(StatusTransition.objects.filter(entry=entry).order_by("id").values_list("from_status", "to_status"))
    assert history == [(None, "pending"), ("pending", "playing"), ("playing", "completed")]


@pytest.mark.django_db
def test_user_a_cannot_affect_user_b_entry(work, user_a, user_b) -> None:  # noqa: ANN001
    client_a = _client_for(user_a)
    client_b = _client_for(user_b)

    client_a.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")
    client_b.post(f"/api/library/entries/{work.id}/status/", {"status": "abandoned"}, format="json")

    entry_a = LibraryEntry.objects.get(user=user_a, work=work)
    entry_b = LibraryEntry.objects.get(user=user_b, work=work)
    assert entry_a.current_status == "playing"
    assert entry_b.current_status == "abandoned"
    assert entry_a.pk != entry_b.pk


@pytest.mark.django_db
def test_unauthenticated_request_rejected(work) -> None:  # noqa: ANN001
    client = APIClient()
    response = client.post(f"/api/library/entries/{work.id}/status/", {"status": "playing"}, format="json")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_invalid_status_rejected(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(f"/api/library/entries/{work.id}/status/", {"status": "not-a-real-status"}, format="json")
    assert response.status_code == 400
    assert LibraryEntry.objects.filter(user=user_a, work=work).exists() is False


@pytest.mark.django_db
def test_dlc_work_is_not_independently_actionable(dlc_work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(f"/api/library/entries/{dlc_work.id}/status/", {"status": "playing"}, format="json")
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_concurrent_status_changes_leave_coherent_history(work, user_a) -> None:  # noqa: ANN001
    import os

    os.environ["_TEST_WORK_ID"] = str(work.id)
    os.environ["_TEST_USER_ID"] = str(user_a.pk)
    errors: list[BaseException] = []

    def _worker(status: str) -> None:
        try:
            client = _client_for(user_a)
            client.post(f"/api/library/entries/{work.id}/status/", {"status": status}, format="json")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_worker, args=(s,)) for s in ("pending", "playing", "completed")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent status change raised: {errors}"
    # Exactly one LibraryEntry, and a coherent (non-corrupted) transition
    # chain -- select_for_update serializes the three concurrent writers so
    # each transition's from_status equals the entry's state at that point,
    # even though the exact interleaving order isn't deterministic.
    assert LibraryEntry.objects.filter(user=user_a, work=work).count() == 1
    entry = LibraryEntry.objects.get(user=user_a, work=work)
    history = list(StatusTransition.objects.filter(entry=entry).order_by("id"))
    running_status = None
    for transition in history:
        assert transition.from_status == running_status
        running_status = transition.to_status
    assert entry.current_status == running_status
