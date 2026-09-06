"""Tests for login/logout endpoints (Plan 01-04 Task 2, AUTH-01)."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

User = get_user_model()

USERNAME = "demo-tracer-user"
PASSWORD = "Tracer-Demo-Password-9!"  # noqa: S105 - test fixture


@pytest.fixture(autouse=True)
def _isolate_throttle_state() -> None:
    """LoginView now carries a scoped anonymous rate throttle (H-01/M-01);
    DRF keeps its per-IP history in the default cache, which LocMemCache
    holds for the whole process. Clear it around every test so one test's
    login burst never throttles the next."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def demo_user(db):  # noqa: ANN001 - pytest-django db fixture
    return User.objects.create_user(username=USERNAME, password=PASSWORD)


def _csrf_client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


@pytest.mark.django_db
def test_valid_login_redirects_to_catalogue(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        "/api/accounts/login/",
        {"username": USERNAME, "password": PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    assert response.json()["next"] == "/catalogue"


@pytest.mark.django_db
def test_invalid_credentials_return_uniform_message(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    wrong_password = client.post(
        "/api/accounts/login/",
        {"username": USERNAME, "password": "wrong"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    unknown_user = client.post(
        "/api/accounts/login/",
        {"username": "nobody-registered", "password": "whatever"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


@pytest.mark.django_db
def test_login_username_is_case_insensitive(demo_user) -> None:  # noqa: ANN001
    """Registration blocks case-variant duplicates (``username__iexact``),
    so a login that only differs in case must resolve to the stored account
    instead of locking the visitor out."""
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        "/api/accounts/login/",
        {"username": USERNAME.upper(), "password": PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    assert response.json()["next"] == "/catalogue"


@pytest.mark.django_db
def test_case_insensitive_login_still_needs_the_right_password(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        "/api/accounts/login/",
        {"username": USERNAME.upper(), "password": "wrong"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_without_csrf_token_is_rejected(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    # Deliberately omit the X-CSRFToken header despite holding the cookie.
    response = client.post(
        "/api/accounts/login/", {"username": USERNAME, "password": PASSWORD}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_logout_invalidates_the_session(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value
    client.post(
        "/api/accounts/login/",
        {"username": USERNAME, "password": PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    # django.contrib.auth.login() rotates the CSRF token to prevent session
    # fixation -- re-read the (now-updated) cookie rather than reuse the
    # pre-login value, matching what a real client reads fresh each request.
    csrf_token = client.cookies["csrftoken"].value

    logout_response = client.post("/api/accounts/logout/", format="json", HTTP_X_CSRFTOKEN=csrf_token)
    assert logout_response.status_code == 200

    # A subsequent authenticated-only request must be rejected post-logout.
    protected_response = client.post(
        "/api/library/entries/00000000-0000-0000-0000-000000000000/status/",
        {"status": "playing"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert protected_response.status_code in (401, 403)


@pytest.mark.django_db
def test_external_redirect_target_is_discarded(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        "/api/accounts/login/",
        {"username": USERNAME, "password": PASSWORD, "next": "https://evil.example/phish"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    assert response.json()["next"] == "/catalogue"


@pytest.mark.django_db
def test_protocol_relative_redirect_target_is_discarded(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        "/api/accounts/login/",
        {"username": USERNAME, "password": PASSWORD, "next": "//evil.example/phish"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    assert response.json()["next"] == "/catalogue"


@pytest.mark.django_db
def test_safe_relative_redirect_target_is_honored(demo_user) -> None:  # noqa: ANN001
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        "/api/accounts/login/",
        {"username": USERNAME, "password": PASSWORD, "next": "/collection"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    assert response.json()["next"] == "/collection"


@pytest.mark.django_db
def test_repeated_failed_logins_are_throttled(demo_user) -> None:  # noqa: ANN001
    """M-01: LoginView caps anonymous attempts (scope "login", 10/min) so a
    uniform error message is not an invitation to brute-force at full speed."""
    client = _csrf_client()
    client.get("/api/accounts/csrf/")
    csrf_token = client.cookies["csrftoken"].value

    statuses = []
    for _ in range(15):
        response = client.post(
            "/api/accounts/login/",
            {"username": USERNAME, "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        statuses.append(response.status_code)

    assert 429 in statuses, f"expected a throttled (429) response in the burst, got {statuses}"
    # Everything before the limit is a normal 401, never a 5xx.
    assert set(statuses) <= {401, 429}
