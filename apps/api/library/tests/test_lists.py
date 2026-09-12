"""Tests for custom lists with atomic optimistic-concurrency reorder
(Plan 05-02 Task 2, LIB-04/D-06/D-07)."""

from __future__ import annotations

import threading

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connections
from rest_framework.test import APIClient

from catalogue.models import GameWork
from library import services
from library.models import CustomList, CustomListItem, LibraryEntry

User = get_user_model()


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="list-user-a", password="List-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="list-user-b", password="List-User-B-Pass-9!")


@pytest.fixture
def work_1(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="list-game-1", original_title="List Game One")


@pytest.fixture
def work_2(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="list-game-2", original_title="List Game Two")


@pytest.fixture
def work_3(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="list-game-3", original_title="List Game Three")


@pytest.fixture
def uncollected_work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="uncollected-game", original_title="Uncollected Game")


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _collect(user, work) -> None:  # noqa: ANN001
    LibraryEntry.objects.get_or_create(user=user, work=work, defaults={"current_status": None})


# ---------------------------------------------------------------------------
# Test 1: owner CRUD; items require LibraryEntry membership.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_owner_can_create_edit_and_delete_a_list(user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)

    created = client.post("/api/library/lists/", {"name": "Favorites", "visibility": "public"}, format="json")
    assert created.status_code == 201
    list_id = created.json()["id"]

    edited = client.patch(f"/api/library/lists/{list_id}/", {"name": "My Favorites"}, format="json")
    assert edited.status_code == 200
    assert edited.json()["name"] == "My Favorites"

    deleted = client.delete(f"/api/library/lists/{list_id}/")
    assert deleted.status_code == 204
    assert not CustomList.objects.filter(id=list_id).exists()


@pytest.mark.django_db
def test_adding_an_uncollected_work_is_rejected_without_mutation(user_a, uncollected_work) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    created = client.post("/api/library/lists/", {"name": "List"}, format="json")
    list_id = created.json()["id"]

    response = client.post(
        f"/api/library/lists/{list_id}/items/", {"work_id": str(uncollected_work.id)}, format="json"
    )
    assert response.status_code == 400
    assert not CustomListItem.objects.filter(list_id=list_id).exists()


# ---------------------------------------------------------------------------
# Test 2: no duplicates; reorder requires expected_version + exact id set,
# assigns consecutive positions, stable after reload.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_adding_the_same_work_twice_is_rejected(user_a, work_1) -> None:  # noqa: ANN001
    _collect(user_a, work_1)
    client = _client_for(user_a)
    created = client.post("/api/library/lists/", {"name": "List"}, format="json")
    list_id = created.json()["id"]

    first = client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_1.id)}, format="json")
    assert first.status_code == 201
    second = client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_1.id)}, format="json")
    assert second.status_code == 400
    assert CustomListItem.objects.filter(list_id=list_id, work=work_1).count() == 1


@pytest.mark.django_db
def test_reorder_assigns_consecutive_positions_stable_after_reload(  # noqa: ANN201
    user_a, work_1, work_2, work_3
):
    for work in (work_1, work_2, work_3):
        _collect(user_a, work)
    client = _client_for(user_a)
    created = client.post("/api/library/lists/", {"name": "List"}, format="json").json()
    list_id = created["id"]
    for work in (work_1, work_2, work_3):
        client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work.id)}, format="json")

    current = client.get(f"/api/library/lists/{list_id}/").json()
    version = current["version"]
    item_ids = [item["id"] for item in current["items"]]
    reversed_ids = list(reversed(item_ids))

    reordered = client.post(
        f"/api/library/lists/{list_id}/reorder/",
        {"expected_version": version, "item_ids": reversed_ids},
        format="json",
    )
    assert reordered.status_code == 200
    positions = [item["position"] for item in reordered.json()["items"]]
    assert positions == [1, 2, 3]
    assert [item["id"] for item in reordered.json()["items"]] == reversed_ids
    assert reordered.json()["version"] == version + 1

    reload = client.get(f"/api/library/lists/{list_id}/").json()
    assert [item["id"] for item in reload["items"]] == reversed_ids
    assert [item["position"] for item in reload["items"]] == [1, 2, 3]


# ---------------------------------------------------------------------------
# Test 3: missing expected_version -> 400 no mutation; stale -> 409 no
# changes; matching version -> select_for_update + commit + new version.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reorder_without_expected_version_is_rejected_without_mutation(user_a, work_1) -> None:  # noqa: ANN001
    _collect(user_a, work_1)
    client = _client_for(user_a)
    created = client.post("/api/library/lists/", {"name": "List"}, format="json").json()
    list_id = created["id"]
    item = client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_1.id)}, format="json").json()
    item_id = item["items"][0]["id"]

    response = client.post(f"/api/library/lists/{list_id}/reorder/", {"item_ids": [item_id]}, format="json")
    assert response.status_code == 400
    assert CustomList.objects.get(id=list_id).version == 1


@pytest.mark.django_db
def test_stale_expected_version_returns_conflict_without_changes(user_a, work_1, work_2) -> None:  # noqa: ANN001
    _collect(user_a, work_1)
    _collect(user_a, work_2)
    client = _client_for(user_a)
    created = client.post("/api/library/lists/", {"name": "List"}, format="json").json()
    list_id = created["id"]
    client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_1.id)}, format="json")
    client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_2.id)}, format="json")

    before = client.get(f"/api/library/lists/{list_id}/").json()
    item_ids = [item["id"] for item in before["items"]]

    stale = client.post(
        f"/api/library/lists/{list_id}/reorder/",
        {"expected_version": before["version"] + 99, "item_ids": list(reversed(item_ids))},
        format="json",
    )
    assert stale.status_code == 409

    after = client.get(f"/api/library/lists/{list_id}/").json()
    assert after["version"] == before["version"]
    assert [item["id"] for item in after["items"]] == item_ids
    assert [item["position"] for item in after["items"]] == [item["position"] for item in before["items"]]


@pytest.mark.django_db
def test_matching_version_reorders_and_returns_new_version(user_a, work_1, work_2) -> None:  # noqa: ANN001
    _collect(user_a, work_1)
    _collect(user_a, work_2)
    client = _client_for(user_a)
    created = client.post("/api/library/lists/", {"name": "List"}, format="json").json()
    list_id = created["id"]
    client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_1.id)}, format="json")
    client.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_2.id)}, format="json")

    current = client.get(f"/api/library/lists/{list_id}/").json()
    item_ids = [item["id"] for item in current["items"]]

    response = client.post(
        f"/api/library/lists/{list_id}/reorder/",
        {"expected_version": current["version"], "item_ids": list(reversed(item_ids))},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["version"] == current["version"] + 1
    assert CustomList.objects.get(id=list_id).version == current["version"] + 1


# ---------------------------------------------------------------------------
# Test 4: two concurrent reorders serialize via select_for_update(); the
# conflict outcome leaves no duplicated or gapped positions.
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_concurrent_reorders_serialize_without_duplicate_or_gapped_positions(  # noqa: ANN201
    user_a, work_1, work_2, work_3
):
    for work in (work_1, work_2, work_3):
        _collect(user_a, work)
    custom_list = CustomList.objects.create(user=user_a, name="Concurrent List")
    items = [
        CustomListItem.objects.create(list=custom_list, work=work, position=index)
        for index, work in enumerate((work_1, work_2, work_3), start=1)
    ]
    item_ids = [str(item.id) for item in items]

    results: list[object] = []
    errors: list[BaseException] = []

    def _worker(ordering: list[str]) -> None:
        try:
            result = services.reorder_list_items(
                user=user_a, list_id=str(custom_list.id), expected_version=1, item_ids=ordering
            )
            results.append(result)
        except services.StaleListVersion as exc:
            results.append(exc)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connections.close_all()

    orderings = [item_ids, list(reversed(item_ids))]
    threads = [threading.Thread(target=_worker, args=(ordering,)) for ordering in orderings]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent reorder raised: {errors}"
    successes = [r for r in results if isinstance(r, CustomList)]
    conflicts = [r for r in results if isinstance(r, services.StaleListVersion)]
    # select_for_update serializes the two writers: exactly one succeeds
    # against version 1, the other loses the race and sees a stale version.
    assert len(successes) == 1
    assert len(conflicts) == 1

    final_positions = list(
        CustomListItem.objects.filter(list=custom_list).order_by("position").values_list("position", flat=True)
    )
    assert final_positions == [1, 2, 3]
    assert CustomListItem.objects.filter(list=custom_list).count() == 3


# ---------------------------------------------------------------------------
# Test 5: an exception during reorder leaves the previous order intact;
# user B cannot access A's private list; a public list only exposes
# allowlisted name/works/positions.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_exception_during_reorder_leaves_previous_order_intact(user_a, work_1, work_2) -> None:  # noqa: ANN001
    _collect(user_a, work_1)
    _collect(user_a, work_2)
    custom_list = CustomList.objects.create(user=user_a, name="List")
    item_1 = CustomListItem.objects.create(list=custom_list, work=work_1, position=1)
    item_2 = CustomListItem.objects.create(list=custom_list, work=work_2, position=2)

    # An incomplete/mismatched id set raises ValidationError mid-service,
    # inside the same transaction.atomic() block as any position writes.
    with pytest.raises(ValidationError):
        services.reorder_list_items(
            user=user_a, list_id=str(custom_list.id), expected_version=1, item_ids=[str(item_1.id)]
        )

    custom_list.refresh_from_db()
    item_1.refresh_from_db()
    item_2.refresh_from_db()
    assert custom_list.version == 1
    assert item_1.position == 1
    assert item_2.position == 2


@pytest.mark.django_db
def test_user_b_cannot_access_user_a_private_list_resources(user_a, user_b, work_1) -> None:  # noqa: ANN001
    _collect(user_a, work_1)
    client_a = _client_for(user_a)
    created = client_a.post("/api/library/lists/", {"name": "Private List", "visibility": "private"}, format="json").json()
    list_id = created["id"]
    client_a.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_1.id)}, format="json")

    client_b = _client_for(user_b)
    assert client_b.get(f"/api/library/lists/{list_id}/").status_code == 404
    assert client_b.patch(f"/api/library/lists/{list_id}/", {"name": "Hijacked"}, format="json").status_code == 404
    assert client_b.delete(f"/api/library/lists/{list_id}/").status_code == 404
    assert (
        client_b.post(f"/api/library/lists/{list_id}/items/", {"work_id": str(work_1.id)}, format="json").status_code
        == 404
    )
    reorder_response = client_b.post(
        f"/api/library/lists/{list_id}/reorder/", {"expected_version": 1, "item_ids": []}, format="json"
    )
    assert reorder_response.status_code == 404
    assert CustomList.objects.get(id=list_id).name == "Private List"


@pytest.mark.django_db
def test_public_list_projection_only_exposes_allowlisted_fields(user_a, work_1) -> None:  # noqa: ANN001
    _collect(user_a, work_1)
    custom_list = CustomList.objects.create(user=user_a, name="Public List", visibility="public")
    CustomListItem.objects.create(list=custom_list, work=work_1, position=1)

    from library.serializers import serialize_profile_list

    projection = serialize_profile_list(custom_list)
    assert set(projection.keys()) == {"name", "items"}
    assert set(projection["items"][0].keys()) == {"work_slug", "work_title", "position"}
    assert projection["name"] == "Public List"
    assert projection["items"][0]["work_slug"] == "list-game-1"
