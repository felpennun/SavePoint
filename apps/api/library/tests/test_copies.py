"""Tests for owned-copy creation (Plan 01-07 Task 1, D-15/D-16, INV-01/INV-02)."""

from __future__ import annotations

import threading

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connections
from rest_framework.test import APIClient

from catalogue.models import Edition, GameRelease, GameWork, Platform
from library import services
from library.models import OwnedCopy

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
