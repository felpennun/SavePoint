"""Tests for GET /api/accounts/me/ -- the signed-in visitor's own identity.

The navbar account control and the home greeting read this endpoint to show
*which* account is active. It must answer only for an authenticated caller
and must never expose email or internal IDs.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

User = get_user_model()

USERNAME = "me-endpoint-user"
PASSWORD = "Me-Endpoint-Pass-71!"  # noqa: S105 - test fixture, not a real credential


@pytest.fixture(autouse=True)
def _isolate_throttle_state() -> None:
    cache.clear()
    yield
    cache.clear()


def _csrf_client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


def _sign_in(client: APIClient) -> None:
    User.objects.create_user(username=USERNAME, password=PASSWORD)
    client.get("/api/accounts/csrf/")
    token = client.cookies["csrftoken"].value
    client.post(
        "/api/accounts/login/",
        {"username": USERNAME, "password": PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )


@pytest.mark.django_db
def test_me_returns_the_signed_in_username() -> None:
    client = _csrf_client()
    _sign_in(client)

    response = client.get("/api/accounts/me/")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == USERNAME
    assert body["is_demo"] is False


@pytest.mark.django_db
def test_me_is_rejected_for_anonymous_callers() -> None:
    client = _csrf_client()
    response = client.get("/api/accounts/me/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_me_projection_is_a_minimal_allowlist() -> None:
    client = _csrf_client()
    _sign_in(client)

    body = client.get("/api/accounts/me/").json()

    assert set(body.keys()) == {"username", "is_demo", "capabilities"}
    assert body["capabilities"] == {
        "can_view_research": False,
        "can_manage_platform": False,
    }
