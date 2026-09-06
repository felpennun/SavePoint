"""Controlled functional registration (Plan 01.1-08, AUTH-02 / D-08).

D-08's middle path: a genuinely functional self-registration flow that still
lives inside the controlled academic demo boundary. It is NOT AUTH-03
(unrestricted public production registration stays out of scope): no email
verification, no social auth. A new account is real, active, and *not*
simulated -- the `DemoAccountIdentity` marker is seed-only.

Weak, duplicate, malformed, CSRF-less, and throttled attempts must create no
user at all.
"""

from __future__ import annotations

import inspect

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts import views as accounts_views
from accounts.models import DemoAccountIdentity

User = get_user_model()

STRONG_PASSWORD = "Zeph-Qadim-7412-Loft!"  # noqa: S105 - test fixture, not a real credential
WEAK_PASSWORD = "1234"  # noqa: S105 - deliberately weak fixture


@pytest.fixture(autouse=True)
def _isolate_throttle_state() -> None:
    """DRF's rate throttle persists its per-IP history in the default cache,
    which LocMemCache keeps for the whole process -- clear it around every
    test so the throttle case does not bleed into the others."""
    cache.clear()
    yield
    cache.clear()


def _csrf_client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


def _bootstrap_csrf(client: APIClient) -> str:
    client.get("/api/accounts/csrf/")
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_valid_registration_creates_active_non_simulated_account_and_session() -> None:
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    response = client.post(
        "/api/accounts/register/",
        {"username": "fresh-account", "password": STRONG_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 201
    user = User.objects.get(username="fresh-account")
    assert user.is_active is True
    # Non-simulated: the seed-only DemoAccountIdentity marker is never stamped
    # on a self-registered account.
    assert not DemoAccountIdentity.objects.filter(user=user).exists()
    assert not hasattr(user, "demo_identity")
    # Password is properly hashed and usable.
    assert user.has_usable_password()
    assert authenticate(username="fresh-account", password=STRONG_PASSWORD) is not None
    # The new session is logged in.
    assert client.session.get("_auth_user_id") == str(user.pk)


@pytest.mark.django_db
def test_successful_registration_redirects_to_the_catalogue() -> None:
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    response = client.post(
        "/api/accounts/register/",
        {"username": "redirect-account", "password": STRONG_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 201
    assert response.json()["next"] == "/catalogue"


@pytest.mark.django_db
def test_weak_password_is_rejected_and_creates_no_user() -> None:
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    response = client.post(
        "/api/accounts/register/",
        {"username": "weak-account", "password": WEAK_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 400
    assert not User.objects.filter(username="weak-account").exists()


@pytest.mark.django_db
def test_weak_password_response_lists_concrete_reasons() -> None:
    """The 400 body carries the specific validator failures so the client
    can tell the visitor exactly what to fix, not just "too weak"."""
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    response = client.post(
        "/api/accounts/register/",
        {"username": "reasons-account", "password": WEAK_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 400
    reasons = response.json()["password_errors"]
    assert isinstance(reasons, list)
    # "1234" trips several validators at once (too short, too common,
    # entirely numeric); at least two concrete messages come back.
    assert len(reasons) >= 2
    assert all(isinstance(message, str) and message for message in reasons)
    assert not User.objects.filter(username="reasons-account").exists()


@pytest.mark.django_db
def test_password_too_similar_to_username_is_rejected() -> None:
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    response = client.post(
        "/api/accounts/register/",
        {"username": "supercalifragilistic", "password": "supercalifragilistic1"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 400
    assert not User.objects.filter(username="supercalifragilistic").exists()


@pytest.mark.django_db
def test_duplicate_username_is_rejected_and_creates_no_second_user() -> None:
    User.objects.create_user(username="already-here", password=STRONG_PASSWORD)

    client = _csrf_client()
    token = _bootstrap_csrf(client)
    response = client.post(
        "/api/accounts/register/",
        {"username": "already-here", "password": STRONG_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 409
    assert User.objects.filter(username="already-here").count() == 1


@pytest.mark.django_db
def test_duplicate_username_check_is_case_insensitive() -> None:
    User.objects.create_user(username="CaseOwner", password=STRONG_PASSWORD)

    client = _csrf_client()
    token = _bootstrap_csrf(client)
    response = client.post(
        "/api/accounts/register/",
        {"username": "caseowner", "password": STRONG_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 409
    assert User.objects.filter(username__iexact="caseowner").count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        {"username": "missing-password"},
        {"password": STRONG_PASSWORD},
        {"username": "", "password": STRONG_PASSWORD},
        {"username": "   ", "password": STRONG_PASSWORD},
        {"username": {"nested": "object"}, "password": STRONG_PASSWORD},
        {"username": "list-password", "password": ["not", "a", "string"]},
    ],
)
def test_malformed_payload_is_rejected_and_creates_no_user(payload: dict) -> None:
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    before = User.objects.count()
    response = client.post(
        "/api/accounts/register/",
        payload,
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 400
    assert User.objects.count() == before


@pytest.mark.django_db
def test_registration_without_csrf_token_is_rejected() -> None:
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    # Hold the cookie but deliberately omit the X-CSRFToken header.
    response = client.post(
        "/api/accounts/register/",
        {"username": "no-csrf-account", "password": STRONG_PASSWORD},
        format="json",
    )

    assert response.status_code == 403
    assert not User.objects.filter(username="no-csrf-account").exists()


@pytest.mark.django_db
def test_repeated_attempts_are_throttled_and_create_no_user() -> None:
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    statuses = []
    for index in range(7):
        response = client.post(
            "/api/accounts/register/",
            {"username": f"burst-account-{index}", "password": WEAK_PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        statuses.append(response.status_code)

    # The scoped anonymous throttle trips before the burst finishes.
    assert 429 in statuses
    assert statuses[-1] == 429
    # A throttled attempt never reaches account creation.
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_throttle_blocks_an_otherwise_valid_registration() -> None:
    client = _csrf_client()
    token = _bootstrap_csrf(client)

    # Exhaust the scope with rejected attempts (no users created).
    for index in range(7):
        client.post(
            "/api/accounts/register/",
            {"username": f"filler-account-{index}", "password": WEAK_PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

    response = client.post(
        "/api/accounts/register/",
        {"username": "would-be-valid", "password": STRONG_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 429
    assert not User.objects.filter(username="would-be-valid").exists()


def test_registration_view_carries_no_unrestricted_production_language() -> None:
    """AUTH-03 (unrestricted public production registration) stays out of
    scope -- the controlled-demo implementation must not describe itself in
    those terms anywhere."""
    source = inspect.getsource(accounts_views).lower()
    for forbidden in ("unrestricted", "auth-03", "auth_03", "production account", "production registration"):
        assert forbidden not in source, f"AUTH-03 language leaked into accounts/views.py: {forbidden!r}"
