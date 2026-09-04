"""Tests for exact rating persistence (Plan 01-07 Task 1, D-13/LIB-02)."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from catalogue.models import GameWork
from library import services
from library.models import LibraryEntry

User = get_user_model()


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="rating-game", original_title="Rating Game")


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="rating-user-a", password="Rating-User-A-Pass-9!")


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.parametrize("value", [1, 2, 5, 9, 10])
@pytest.mark.django_db
def test_every_valid_half_step_is_accepted(value: int, work, user_a) -> None:  # noqa: ANN001
    entry = services.set_rating(user=user_a, work=work, rating_half_steps=value)
    assert entry.rating_half_steps == value


@pytest.mark.django_db
def test_null_clears_rating(work, user_a) -> None:  # noqa: ANN001
    services.set_rating(user=user_a, work=work, rating_half_steps=7)
    entry = services.set_rating(user=user_a, work=work, rating_half_steps=None)
    assert entry.rating_half_steps is None


@pytest.mark.parametrize("value", [0, 11, -1, 100])
@pytest.mark.django_db
def test_out_of_range_values_rejected_without_rounding(value: int, work, user_a) -> None:  # noqa: ANN001
    with pytest.raises(ValidationError):
        services.set_rating(user=user_a, work=work, rating_half_steps=value)
    assert not LibraryEntry.objects.filter(user=user_a, work=work, rating_half_steps=value).exists()


@pytest.mark.django_db
def test_float_value_rejected_not_rounded(work, user_a) -> None:  # noqa: ANN001
    with pytest.raises(ValidationError):
        services.set_rating(user=user_a, work=work, rating_half_steps=7.5)  # type: ignore[arg-type]


@pytest.mark.django_db
def test_database_check_constraint_rejects_out_of_range_bypassing_service(work, user_a) -> None:  # noqa: ANN001
    """Even a direct ORM write (bypassing the service layer) must fail --
    the constraint lives in PostgreSQL, not just in application code."""
    from django.db import IntegrityError, transaction

    entry = LibraryEntry.objects.create(user=user_a, work=work)
    entry.rating_half_steps = 0
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            entry.save(update_fields=["rating_half_steps"])


@pytest.mark.django_db
def test_rating_api_round_trip(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(f"/api/library/entries/{work.id}/rating/", {"rating_half_steps": 8}, format="json")
    assert response.status_code == 200
    assert response.json() == {"rating_half_steps": 8}

    reload = client.get(f"/api/library/entries/{work.id}/rating/")
    assert reload.json() == {"rating_half_steps": 8}


@pytest.mark.django_db
def test_rating_api_rejects_invalid_values(work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    for bad_value in (0, 11, "not-a-number"):
        response = client.post(f"/api/library/entries/{work.id}/rating/", {"rating_half_steps": bad_value}, format="json")
        assert response.status_code == 400
