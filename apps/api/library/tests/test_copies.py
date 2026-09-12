"""Tests for owned-copy creation (Plan 01-07 Task 1, D-15/D-16, INV-01/INV-02)
and purchase/conservation metadata (Plan 05-03, INV-03/INV-04/PRIV-01)."""

from __future__ import annotations

import threading
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connections, transaction
from rest_framework.test import APIClient

from catalogue.models import Edition, GameRelease, GameWork, Platform
from library import services
from library.models import LibraryEntry, OwnedCopy, StatusTransition

User = get_user_model()


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="copies-game", original_title="Copies Game")


@pytest.fixture
def other_work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="other-copies-game", original_title="Other Copies Game")


@pytest.fixture
def platform(db):  # noqa: ANN001
    return Platform.objects.create(name="PC", slug="pc")


@pytest.fixture
def release(db, work, platform):  # noqa: ANN001
    return GameRelease.objects.create(work=work, platform=platform, release_name="Copies Game (PC)")


@pytest.fixture
def other_work_release(db, other_work, platform):  # noqa: ANN001
    return GameRelease.objects.create(work=other_work, platform=platform, release_name="Other Copies Game (PC)")


@pytest.fixture
def edition(db, release):  # noqa: ANN001
    return Edition.objects.create(release=release, name="Standard")


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="copies-user-a", password="Copies-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="copies-user-b", password="Copies-User-B-Pass-9!")


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_two_different_copies_of_same_game_persist(work, release, user_a) -> None:  # noqa: ANN001
    copy1, created1 = services.create_owned_copy(
        user=user_a, work=work, release_id=str(release.id), edition_id=None, format="physical", idempotency_key="key-1"
    )
    copy2, created2 = services.create_owned_copy(
        user=user_a, work=work, release_id=str(release.id), edition_id=None, format="digital", idempotency_key="key-2"
    )
    assert created1 and created2
    assert copy1.id != copy2.id
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 2


@pytest.mark.django_db
def test_replaying_idempotency_key_returns_same_copy_not_a_duplicate(work, release, user_a) -> None:  # noqa: ANN001
    copy1, created1 = services.create_owned_copy(
        user=user_a, work=work, release_id=str(release.id), edition_id=None, format="physical", idempotency_key="replay-key"
    )
    copy2, created2 = services.create_owned_copy(
        user=user_a, work=work, release_id=str(release.id), edition_id=None, format="physical", idempotency_key="replay-key"
    )
    assert created1 is True
    assert created2 is False
    assert copy1.id == copy2.id
    assert OwnedCopy.objects.filter(user=user_a).count() == 1


@pytest.mark.django_db
def test_release_must_belong_to_the_selected_work(work, other_work_release, user_a) -> None:  # noqa: ANN001
    with pytest.raises(ValidationError):
        services.create_owned_copy(
            user=user_a,
            work=work,
            release_id=str(other_work_release.id),
            edition_id=None,
            format="physical",
            idempotency_key="mismatched-release",
        )
    assert OwnedCopy.objects.filter(user=user_a).count() == 0


@pytest.mark.django_db
def test_edition_must_belong_to_the_selected_release(work, release, other_work_release, user_a) -> None:  # noqa: ANN001
    foreign_edition = Edition.objects.create(release=other_work_release, name="Foreign Edition")
    with pytest.raises(ValidationError):
        services.create_owned_copy(
            user=user_a,
            work=work,
            release_id=str(release.id),
            edition_id=str(foreign_edition.id),
            format="physical",
            idempotency_key="mismatched-edition",
        )


@pytest.mark.django_db
def test_empty_copy_list_is_valid(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.get(f"/api/library/entries/{work.id}/copies/")
    assert response.status_code == 200
    assert response.json() == {"copies": []}


@pytest.mark.django_db
def test_created_copy_makes_work_visible_in_my_library(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/copies/",
        {
            "release_id": str(release.id),
            "edition_id": None,
            "format": "physical",
            "idempotency_key": "collection-visibility",
        },
        format="json",
    )

    assert response.status_code == 201
    items = client.get("/api/library/entries/").json()["items"]
    assert len(items) == 1
    assert items[0]["work_id"] == str(work.id)
    assert items[0]["work_slug"] == "copies-game"
    assert items[0]["status"] is None
    assert items[0]["rating_half_steps"] is None
    assert items[0]["owned_copy_count"] == 1


@pytest.mark.django_db
def test_copy_list_ordered_stably_newest_first(work, release, user_a) -> None:  # noqa: ANN001
    first_copy, _ = services.create_owned_copy(
        user=user_a, work=work, release_id=str(release.id), edition_id=None, format="physical", idempotency_key="a"
    )
    second_copy, _ = services.create_owned_copy(
        user=user_a, work=work, release_id=str(release.id), edition_id=None, format="digital", idempotency_key="b"
    )
    client = _client_for(user_a)
    response = client.get(f"/api/library/entries/{work.id}/copies/")
    copies = response.json()["copies"]
    assert len(copies) == 2
    assert copies[0]["id"] == str(second_copy.id)
    assert copies[1]["id"] == str(first_copy.id)

    # Stability: repeating the same request produces the same order.
    repeat = client.get(f"/api/library/entries/{work.id}/copies/").json()["copies"]
    assert [c["id"] for c in repeat] == [c["id"] for c in copies]


@pytest.mark.django_db(transaction=True)
def test_concurrent_idempotency_key_replay_creates_exactly_one_copy(work, release, user_a) -> None:  # noqa: ANN001
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            services.create_owned_copy(
                user=user_a,
                work=work,
                release_id=str(release.id),
                edition_id=None,
                format="physical",
                idempotency_key="concurrent-key",
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent copy creation raised: {errors}"
    assert OwnedCopy.objects.filter(user=user_a, idempotency_key="concurrent-key").count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_intentionally_distinct_keys_produce_distinct_copies(work, release, user_a) -> None:  # noqa: ANN001
    errors: list[BaseException] = []

    def _worker(key: str) -> None:
        try:
            services.create_owned_copy(
                user=user_a, work=work, release_id=str(release.id), edition_id=None, format="physical", idempotency_key=key
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_worker, args=(f"distinct-{i}",)) for i in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent copy creation raised: {errors}"
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 3


@pytest.mark.django_db
def test_configuration_saves_updates_and_removes_the_complete_work_state(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    initial = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {
            "status": "playing",
            "rating_half_steps": 8,
            "copies": [
                {"release_id": str(release.id), "format": "physical", "edition_id": None},
                {"release_id": str(release.id), "format": "digital", "edition_id": None},
            ],
        },
        format="json",
    )
    assert initial.status_code == 200
    assert len(initial.json()["copies"]) == 2
    first_id = initial.json()["copies"][0]["id"]

    updated = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {
            "status": "completed",
            "rating_half_steps": 10,
            "copies": [{"id": first_id, "release_id": str(release.id), "format": "digital", "edition_id": None}],
        },
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"
    assert updated.json()["rating_half_steps"] == 10
    assert len(updated.json()["copies"]) == 1
    assert updated.json()["copies"][0]["id"] == first_id
    assert updated.json()["copies"][0]["format"] == "digital"
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 1
    assert StatusTransition.objects.filter(entry__user=user_a, entry__work=work).count() == 2


@pytest.mark.django_db
def test_owner_can_delete_one_copy_and_then_clear_the_whole_configuration(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    saved = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {
            "status": "pending",
            "rating_half_steps": None,
            "copies": [{"release_id": str(release.id), "format": "physical", "edition_id": None}],
        },
        format="json",
    )
    copy_id = saved.json()["copies"][0]["id"]
    deleted_copy = client.delete(f"/api/library/entries/{work.id}/copies/{copy_id}/")
    assert deleted_copy.status_code == 204
    assert not OwnedCopy.objects.filter(user=user_a, work=work).exists()
    assert LibraryEntry.objects.filter(user=user_a, work=work).exists()

    deleted_entry = client.delete(f"/api/library/entries/{work.id}/")
    assert deleted_entry.status_code == 204
    assert not LibraryEntry.objects.filter(user=user_a, work=work).exists()
    assert not StatusTransition.objects.filter(entry__user=user_a, entry__work=work).exists()


# ---------------------------------------------------------------------------
# Plan 05-03 Task 1 (tracer): purchase/conservation metadata round-trip and
# idempotency (INV-03/INV-04).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_physical_copy_metadata_persists_and_survives_reload(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    payload = {
        "status": "playing",
        "rating_half_steps": None,
        "copies": [
            {
                "release_id": str(release.id),
                "edition_id": None,
                "format": "physical",
                "purchase_date": "2026-01-15",
                "price": "49.99",
                "currency": "eur",
                "store": "GameStop",
                "conservation_state": "good",
                "storage_location": "Shelf A3",
            }
        ],
    }
    saved = client.post(f"/api/library/entries/{work.id}/configuration/", payload, format="json")
    assert saved.status_code == 200
    copy = saved.json()["copies"][0]
    assert copy["purchase_date"] == "2026-01-15"
    assert copy["price"] == "49.99"
    # Lowercase input is normalized to uppercase (INV-03).
    assert copy["currency"] == "EUR"
    assert copy["store"] == "GameStop"
    assert copy["conservation_state"] == "good"
    assert copy["storage_location"] == "Shelf A3"

    reloaded = client.get(f"/api/library/entries/{work.id}/copies/").json()["copies"]
    assert len(reloaded) == 1
    assert reloaded[0]["purchase_date"] == "2026-01-15"
    assert reloaded[0]["price"] == "49.99"
    assert reloaded[0]["currency"] == "EUR"
    assert reloaded[0]["store"] == "GameStop"
    assert reloaded[0]["conservation_state"] == "good"
    assert reloaded[0]["storage_location"] == "Shelf A3"


@pytest.mark.django_db
def test_replaying_idempotency_key_preserves_first_metadata(work, release, user_a) -> None:  # noqa: ANN001
    copy1, created1 = services.create_owned_copy(
        user=user_a,
        work=work,
        release_id=str(release.id),
        edition_id=None,
        format="physical",
        idempotency_key="meta-replay-key",
        purchase_date="2026-02-01",
        price=Decimal("19.99"),
        currency="USD",
        store="Steam",
        conservation_state="new",
        storage_location="Drawer 1",
    )
    copy2, created2 = services.create_owned_copy(
        user=user_a,
        work=work,
        release_id=str(release.id),
        edition_id=None,
        format="physical",
        idempotency_key="meta-replay-key",
        purchase_date="1999-01-01",
        price=Decimal("0.01"),
        currency="GBP",
        store="Different",
        conservation_state="poor",
        storage_location="Attic",
    )
    assert created1 is True
    assert created2 is False
    assert copy1.id == copy2.id
    copy1.refresh_from_db()
    assert str(copy1.price) == "19.99"
    assert copy1.currency == "USD"
    assert copy1.store == "Steam"
    assert copy1.conservation_state == "new"
    assert copy1.storage_location == "Drawer 1"


@pytest.mark.django_db
def test_full_configuration_conserves_copy_metadata_when_editing_and_removing_other_copies(
    work, release, user_a
) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    saved = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {
            "status": "playing",
            "rating_half_steps": None,
            "copies": [
                {
                    "release_id": str(release.id),
                    "edition_id": None,
                    "format": "physical",
                    "purchase_date": "2026-02-01",
                    "price": "19.99",
                    "currency": "USD",
                    "store": "Steam",
                    "conservation_state": "new",
                    "storage_location": "Drawer 1",
                },
                {"release_id": str(release.id), "edition_id": None, "format": "digital"},
            ],
        },
        format="json",
    )
    assert saved.status_code == 200
    copies = saved.json()["copies"]
    physical_copy = next(c for c in copies if c["format"] == "physical")
    digital_copy = next(c for c in copies if c["format"] == "digital")

    # Edit only the store field of the physical copy, and drop the digital
    # one entirely; the physical copy's other metadata must survive intact.
    updated = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {
            "status": "playing",
            "rating_half_steps": None,
            "copies": [
                {
                    "id": physical_copy["id"],
                    "release_id": str(release.id),
                    "edition_id": None,
                    "format": "physical",
                    "purchase_date": "2026-02-01",
                    "price": "19.99",
                    "currency": "USD",
                    "store": "Different Store",
                    "conservation_state": "new",
                    "storage_location": "Drawer 1",
                },
            ],
        },
        format="json",
    )
    assert updated.status_code == 200
    remaining = updated.json()["copies"]
    assert len(remaining) == 1
    assert remaining[0]["store"] == "Different Store"
    assert remaining[0]["price"] == "19.99"
    assert remaining[0]["currency"] == "USD"
    assert remaining[0]["conservation_state"] == "new"
    assert remaining[0]["storage_location"] == "Drawer 1"
    assert not OwnedCopy.objects.filter(id=digital_copy["id"]).exists()


# ---------------------------------------------------------------------------
# Plan 05-03 Task 2: physical/digital rules, constraints, validation, and
# ownership/privacy protection (INV-03/INV-04/PRIV-01).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_digital_copy_with_conservation_state_is_rejected_via_api_without_mutation(
    work, release, user_a
) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/copies/",
        {
            "release_id": str(release.id),
            "edition_id": None,
            "format": "digital",
            "idempotency_key": "digital-conservation",
            "conservation_state": "good",
        },
        format="json",
    )
    assert response.status_code == 400
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_digital_copy_with_storage_location_is_rejected_via_service_without_mutation(
    work, release, user_a
) -> None:  # noqa: ANN001
    with pytest.raises(ValidationError):
        services.create_owned_copy(
            user=user_a,
            work=work,
            release_id=str(release.id),
            edition_id=None,
            format="digital",
            idempotency_key="digital-location",
            storage_location="Shelf",
        )
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_digital_copy_with_conservation_state_fails_check_constraint_at_orm_level(
    work, release, user_a
) -> None:  # noqa: ANN001
    """A direct ORM write that bypasses serializer/service validation must
    still be rejected by PostgreSQL's CheckConstraint (last line of
    defense, INV-04)."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            OwnedCopy.objects.create(
                user=user_a,
                work=work,
                release=release,
                edition=None,
                format="digital",
                idempotency_key="orm-bypass-digital",
                conservation_state="good",
            )
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_negative_price_fails_check_constraint_at_orm_level(work, release, user_a) -> None:  # noqa: ANN001
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            OwnedCopy.objects.create(
                user=user_a,
                work=work,
                release=release,
                edition=None,
                format="physical",
                idempotency_key="orm-bypass-price",
                price=Decimal("-1.00"),
            )
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_invalid_currency_fails_check_constraint_at_orm_level(work, release, user_a) -> None:  # noqa: ANN001
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            OwnedCopy.objects.create(
                user=user_a,
                work=work,
                release=release,
                edition=None,
                format="physical",
                idempotency_key="orm-bypass-currency",
                currency="eu",
            )
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_negative_price_is_rejected_via_api_without_mutation(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/copies/",
        {
            "release_id": str(release.id),
            "edition_id": None,
            "format": "physical",
            "idempotency_key": "negative-price",
            "price": "-5.00",
        },
        format="json",
    )
    assert response.status_code == 400
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_invalid_currency_is_rejected_via_api_without_mutation(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/copies/",
        {
            "release_id": str(release.id),
            "edition_id": None,
            "format": "physical",
            "idempotency_key": "invalid-currency",
            "currency": "12",
        },
        format="json",
    )
    assert response.status_code == 400
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_unknown_conservation_state_is_rejected_via_api_without_mutation(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/copies/",
        {
            "release_id": str(release.id),
            "edition_id": None,
            "format": "physical",
            "idempotency_key": "unknown-conservation",
            "conservation_state": "pristine",
        },
        format="json",
    )
    assert response.status_code == 400
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_oversized_store_payload_is_rejected_without_mutation(work, release, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/copies/",
        {
            "release_id": str(release.id),
            "edition_id": None,
            "format": "physical",
            "idempotency_key": "oversized-store",
            "store": "x" * 200,
        },
        format="json",
    )
    assert response.status_code == 400
    assert OwnedCopy.objects.filter(user=user_a, work=work).count() == 0


@pytest.mark.django_db
def test_user_b_cannot_read_or_mutate_user_a_copy_metadata(work, release, user_a, user_b) -> None:  # noqa: ANN001
    copy_a, _ = services.create_owned_copy(
        user=user_a,
        work=work,
        release_id=str(release.id),
        edition_id=None,
        format="physical",
        idempotency_key="isolation-key",
        price=Decimal("30.00"),
        currency="EUR",
        store="A's store",
        conservation_state="good",
        storage_location="A's shelf",
    )

    client_b = _client_for(user_b)
    # B's own copies listing for this work never includes A's copy.
    response = client_b.get(f"/api/library/entries/{work.id}/copies/")
    assert response.json() == {"copies": []}

    # B cannot delete A's copy.
    deleted = client_b.delete(f"/api/library/entries/{work.id}/copies/{copy_a.id}/")
    assert deleted.status_code == 404
    assert OwnedCopy.objects.filter(id=copy_a.id, user=user_a).exists()

    # B cannot overwrite A's copy metadata through the configuration
    # endpoint by guessing A's copy id -- it is simply not among B's own
    # existing copies, so the id is ignored/rejected without mutation.
    overwrite_attempt = client_b.post(
        f"/api/library/entries/{work.id}/configuration/",
        {
            "status": "playing",
            "rating_half_steps": None,
            "copies": [
                {
                    "id": str(copy_a.id),
                    "release_id": str(release.id),
                    "edition_id": None,
                    "format": "physical",
                    "store": "B tried to overwrite",
                }
            ],
        },
        format="json",
    )
    assert overwrite_attempt.status_code == 400
    copy_a.refresh_from_db()
    assert copy_a.store == "A's store"


@pytest.mark.django_db
def test_public_profile_never_leaks_copy_purchase_or_conservation_metadata(
    work, release, user_a
) -> None:  # noqa: ANN001
    services.create_owned_copy(
        user=user_a,
        work=work,
        release_id=str(release.id),
        edition_id=None,
        format="physical",
        idempotency_key="privacy-key",
        purchase_date="2026-03-01",
        price=Decimal("59.99"),
        currency="EUR",
        store="Secret Store",
        conservation_state="good",
        storage_location="Secret Shelf",
    )

    client = APIClient()
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    assert response.status_code == 200
    body_text = response.content.decode("utf-8")
    for forbidden in ("Secret Store", "Secret Shelf", "59.99", "purchase_date", "conservation_state", "storage_location"):
        assert forbidden not in body_text
