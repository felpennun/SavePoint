"""Tests for the personal "platinum" mark on a LibraryEntry (owner-only,
never surfaced on the public profile or the shared catalogue)."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.serializers import build_public_profile
from catalogue.models import GameWork
from library.models import LibraryEntry

User = get_user_model()


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="platinum-game", original_title="Platinum Game")


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="platinum-user-a", password="Platinum-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="platinum-user-b", password="Platinum-User-B-Pass-9!")


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_configuration_defaults_to_not_platinum(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "playing", "rating_half_steps": None, "copies": []},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["is_platinum"] is False
    assert LibraryEntry.objects.get(user=user_a, work=work).is_platinum is False


@pytest.mark.django_db
def test_configuration_round_trips_platinum_true_through_get_and_reload(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    saved = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "completed", "rating_half_steps": 10, "is_platinum": True, "copies": []},
        format="json",
    )
    assert saved.status_code == 200
    assert saved.json()["is_platinum"] is True

    reloaded = client.get(f"/api/library/entries/{work.id}/configuration/")
    assert reloaded.status_code == 200
    assert reloaded.json()["is_platinum"] is True
    assert LibraryEntry.objects.get(user=user_a, work=work).is_platinum is True


@pytest.mark.django_db
def test_platinum_can_be_toggled_back_off(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "completed", "rating_half_steps": 10, "is_platinum": True, "copies": []},
        format="json",
    )
    cleared = client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "completed", "rating_half_steps": 10, "is_platinum": False, "copies": []},
        format="json",
    )
    assert cleared.status_code == 200
    assert cleared.json()["is_platinum"] is False
    assert LibraryEntry.objects.get(user=user_a, work=work).is_platinum is False


@pytest.mark.django_db
def test_platinum_is_isolated_per_user(work, user_a, user_b) -> None:  # noqa: ANN001
    client_a = _client_for(user_a)
    client_b = _client_for(user_b)
    client_a.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "completed", "rating_half_steps": 10, "is_platinum": True, "copies": []},
        format="json",
    )
    # User B has no entry for this work yet -- their own GET reads a
    # neutral, unset default rather than leaking A's value.
    b_view = client_b.get(f"/api/library/entries/{work.id}/configuration/")
    assert b_view.status_code == 200
    assert b_view.json()["is_platinum"] is False

    client_b.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "playing", "rating_half_steps": None, "is_platinum": False, "copies": []},
        format="json",
    )
    assert LibraryEntry.objects.get(user=user_a, work=work).is_platinum is True
    assert LibraryEntry.objects.get(user=user_b, work=work).is_platinum is False


@pytest.mark.django_db
def test_platinum_appears_in_my_library_listing(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "completed", "rating_half_steps": 10, "is_platinum": True, "copies": []},
        format="json",
    )
    listing = client.get("/api/library/entries/")
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert len(items) == 1
    assert items[0]["is_platinum"] is True


@pytest.mark.django_db
def test_platinum_never_appears_in_the_public_profile_projection(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    client.post(
        f"/api/library/entries/{work.id}/configuration/",
        {"status": "completed", "rating_half_steps": 10, "is_platinum": True, "copies": []},
        format="json",
    )
    profile = build_public_profile(user_a, viewer=user_a)
    assert "is_platinum" not in profile
    for activity_item in profile["activity"]:
        assert "is_platinum" not in activity_item
