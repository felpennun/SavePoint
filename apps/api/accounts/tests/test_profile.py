"""Tests for the owner-scoped, real-account profile endpoint
(Plan 05-01 Task 1, PROF-01/PRIV-01).

D-00/D-00b: a self-registered account is a real, persistent PostgreSQL user
-- not a `DemoAccountIdentity` fixture. D-01: the login alias
(`User.username`) is immutable; only biography and avatar are editable.
These tests reuse the CSRF-client/session pattern already established in
``test_auth.py``/``test_registration.py`` (whose files are not part of this
task's own pytest invocation) so every "session, hash, reload, IDOR,
duplicate, CSRF" case this task's <verify> checks for is actually covered
where that <verify> looks.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import AccountProfile, FavoriteSlot
from catalogue.models import GameWork
from library.models import LibraryEntry

User = get_user_model()

USERNAME_A = "profile-owner-a"
PASSWORD_A = "Zeph-Corridor-4471-Loft!"  # noqa: S105 - test fixture, not a real credential
USERNAME_B = "profile-owner-b"
PASSWORD_B = "Vantage-Kestrel-8823-Moor!"  # noqa: S105 - test fixture, not a real credential


@pytest.fixture(autouse=True)
def _isolate_throttle_state() -> None:
    """Registration/login carry scoped throttles backed by the process-wide
    LocMemCache -- clear it around every test (matches test_auth.py)."""
    cache.clear()
    yield
    cache.clear()


def _csrf_client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


def _register(client: APIClient, username: str, password: str) -> str:
    """Register a real account and return the (rotated) CSRF token for
    subsequent authenticated requests on this same client."""
    client.get("/api/accounts/csrf/")
    token = client.cookies["csrftoken"].value
    response = client.post(
        "/api/accounts/register/",
        {"username": username, "password": password},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 201
    return client.cookies["csrftoken"].value


def _login(client: APIClient, username: str, password: str) -> str:
    client.get("/api/accounts/csrf/")
    token = client.cookies["csrftoken"].value
    response = client.post(
        "/api/accounts/login/",
        {"username": username, "password": password},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 200
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
def test_registration_leaves_a_real_postgresql_session_and_irreversible_hash() -> None:
    """A real registered account persists a django_session row in
    PostgreSQL and a non-reversible password hash -- never the plaintext
    secret anywhere on the User row."""
    client = _csrf_client()
    _register(client, USERNAME_A, PASSWORD_A)

    user = User.objects.get(username=USERNAME_A)
    assert user.password != PASSWORD_A
    assert PASSWORD_A not in user.password
    # Django's default PBKDF2 hasher stores "algorithm$iterations$salt$hash".
    assert user.password.count("$") >= 2
    assert Session.objects.count() >= 1


@pytest.mark.django_db
def test_login_again_and_reload_preserves_identity_and_profile() -> None:
    """The account authenticates again from a brand-new client and the
    profile it wrote is still there -- proof of PostgreSQL persistence
    across the session cookie, not an in-memory fixture."""
    setup_client = _csrf_client()
    _register(setup_client, USERNAME_A, PASSWORD_A)
    token = setup_client.cookies["csrftoken"].value
    patch_response = setup_client.patch(
        "/api/accounts/me/profile/",
        {"bio": "Playing through my backlog."},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert patch_response.status_code == 200

    # Simulate a page reload: an entirely new client, fresh login.
    reload_client = _csrf_client()
    _login(reload_client, USERNAME_A, PASSWORD_A)
    profile_response = reload_client.get("/api/accounts/me/profile/")
    assert profile_response.status_code == 200
    assert profile_response.json()["bio"] == "Playing through my backlog."


@pytest.mark.django_db
def test_profile_update_payload_cannot_change_username() -> None:
    client = _csrf_client()
    token = _register(client, USERNAME_A, PASSWORD_A)

    response = client.patch(
        "/api/accounts/me/profile/",
        {"bio": "hello", "username": "renamed-account"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 200
    assert "username" not in response.json()
    assert User.objects.filter(username=USERNAME_A).exists()
    assert not User.objects.filter(username="renamed-account").exists()


@pytest.mark.django_db
def test_non_https_avatar_url_is_rejected_without_mutation() -> None:
    client = _csrf_client()
    token = _register(client, USERNAME_A, PASSWORD_A)

    response = client.patch(
        "/api/accounts/me/profile/",
        {"avatar_url": "http://example.invalid/avatar.png"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 400
    assert not AccountProfile.objects.filter(
        user__username=USERNAME_A, avatar_url="http://example.invalid/avatar.png"
    ).exists()


@pytest.mark.django_db
def test_oversized_avatar_url_is_rejected_without_mutation() -> None:
    client = _csrf_client()
    token = _register(client, USERNAME_A, PASSWORD_A)

    oversized = "https://example.invalid/" + ("a" * 600)
    response = client.patch(
        "/api/accounts/me/profile/",
        {"avatar_url": oversized},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 400
    assert not AccountProfile.objects.filter(user__username=USERNAME_A, avatar_url=oversized).exists()


@pytest.mark.django_db
def test_valid_https_avatar_url_is_persisted() -> None:
    client = _csrf_client()
    token = _register(client, USERNAME_A, PASSWORD_A)

    response = client.patch(
        "/api/accounts/me/profile/",
        {"avatar_url": "https://images.example.invalid/avatar.png"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 200
    assert response.json()["avatar_url"] == "https://images.example.invalid/avatar.png"


@pytest.mark.django_db
def test_anonymous_request_to_profile_endpoint_is_rejected() -> None:
    client = _csrf_client()
    get_response = client.get("/api/accounts/me/profile/")
    assert get_response.status_code in (401, 403)

    patch_response = client.patch("/api/accounts/me/profile/", {"bio": "x"}, format="json")
    assert patch_response.status_code in (401, 403)
    assert not AccountProfile.objects.exists()


@pytest.mark.django_db
def test_profile_update_without_csrf_token_is_rejected() -> None:
    """A mutation on the new endpoint is rejected without the CSRF header
    even though the caller already holds a valid, authenticated session."""
    client = _csrf_client()
    _register(client, USERNAME_A, PASSWORD_A)

    response = client.patch(
        "/api/accounts/me/profile/",
        {"bio": "no csrf header"},
        format="json",
    )
    assert response.status_code == 403
    assert not AccountProfile.objects.filter(user__username=USERNAME_A, bio="no csrf header").exists()


@pytest.mark.django_db
def test_payload_owner_override_is_ignored_and_never_touches_another_account() -> None:
    """IDOR guard: even if a payload smuggles another account's identity,
    the service only ever derives ownership from ``request.user`` -- a
    fabricated 'user_id'/'owner_id' has no effect and no unauthorized
    mutation is possible on user A's object."""
    client_a = _csrf_client()
    _register(client_a, USERNAME_A, PASSWORD_A)
    # Materialize A's own profile row first (a real GET, like a page load).
    assert client_a.get("/api/accounts/me/profile/").status_code == 200
    user_a = User.objects.get(username=USERNAME_A)

    client_b = _csrf_client()
    token_b = _register(client_b, USERNAME_B, PASSWORD_B)

    response = client_b.patch(
        "/api/accounts/me/profile/",
        {"bio": "b's own bio", "user_id": str(user_a.pk), "owner_id": str(user_a.pk)},
        format="json",
        HTTP_X_CSRFTOKEN=token_b,
    )
    assert response.status_code == 200

    profile_a = AccountProfile.objects.get(user=user_a)
    profile_b = AccountProfile.objects.get(user__username=USERNAME_B)
    assert profile_a.bio == ""
    assert profile_b.bio == "b's own bio"


@pytest.mark.django_db
def test_duplicate_registration_case_insensitive_returns_uniform_error() -> None:
    """Reused analog of test_registration.py's duplicate-username case
    (that file is not part of this task's own pytest invocation), so the
    <fails_when> "duplicado" case stays covered where this plan's <verify>
    actually looks."""
    client = _csrf_client()
    _register(client, "Case-Owner-Profile", PASSWORD_A)

    other_client = _csrf_client()
    other_client.get("/api/accounts/csrf/")
    token = other_client.cookies["csrftoken"].value
    response = other_client.post(
        "/api/accounts/register/",
        {"username": "case-owner-profile", "password": PASSWORD_A},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 409
    assert User.objects.filter(username__iexact="case-owner-profile").count() == 1


# --------------------------------------------------------------------------
# Task 2: five favorite slots (D-02) -- full-replace, owner-scoped.
# --------------------------------------------------------------------------


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def favorite_owner(db):  # noqa: ANN001
    return User.objects.create_user(username="favorite-owner", password="Corridor-Halcyon-7734-Reef!")


@pytest.fixture
def favorite_works(db):  # noqa: ANN001
    return [
        GameWork.objects.create(canonical_slug=f"favorite-work-{i}", original_title=f"Favorite Work {i}")
        for i in range(1, 7)
    ]


@pytest.mark.django_db
def test_replacing_five_favorite_slots_from_owned_collection(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    for work in favorite_works[:5]:
        LibraryEntry.objects.create(user=favorite_owner, work=work, current_status="completed")

    client = _client_for(favorite_owner)
    payload = {
        "slots": [{"slot": i + 1, "work_id": str(work.id)} for i, work in enumerate(favorite_works[:5])]
    }
    response = client.put("/api/accounts/me/favorites/", payload, format="json")
    assert response.status_code == 200
    body = response.json()["slots"]
    assert len(body) == 5
    assert all(item["work_id"] is not None for item in body)


@pytest.mark.django_db
def test_favorite_slots_allow_null_gaps(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=favorite_owner, work=favorite_works[0], current_status="completed")

    client = _client_for(favorite_owner)
    response = client.put(
        "/api/accounts/me/favorites/",
        {"slots": [{"slot": 3, "work_id": str(favorite_works[0].id)}]},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()["slots"]
    assert body[2]["work_id"] == str(favorite_works[0].id)
    assert body[0]["work_id"] is None
    assert body[1]["work_id"] is None


@pytest.mark.django_db
def test_slot_number_six_is_rejected_without_mutation(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=favorite_owner, work=favorite_works[0], current_status="completed")

    client = _client_for(favorite_owner)
    response = client.put(
        "/api/accounts/me/favorites/",
        {"slots": [{"slot": 6, "work_id": str(favorite_works[0].id)}]},
        format="json",
    )
    assert response.status_code == 400
    assert not FavoriteSlot.objects.filter(user=favorite_owner).exists()


@pytest.mark.django_db
def test_duplicate_slot_number_in_payload_is_rejected(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    for work in favorite_works[:2]:
        LibraryEntry.objects.create(user=favorite_owner, work=work, current_status="completed")

    client = _client_for(favorite_owner)
    response = client.put(
        "/api/accounts/me/favorites/",
        {
            "slots": [
                {"slot": 1, "work_id": str(favorite_works[0].id)},
                {"slot": 1, "work_id": str(favorite_works[1].id)},
            ]
        },
        format="json",
    )
    assert response.status_code == 400
    assert not FavoriteSlot.objects.filter(user=favorite_owner).exists()


@pytest.mark.django_db
def test_duplicate_work_in_payload_is_rejected(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=favorite_owner, work=favorite_works[0], current_status="completed")

    client = _client_for(favorite_owner)
    response = client.put(
        "/api/accounts/me/favorites/",
        {
            "slots": [
                {"slot": 1, "work_id": str(favorite_works[0].id)},
                {"slot": 2, "work_id": str(favorite_works[0].id)},
            ]
        },
        format="json",
    )
    assert response.status_code == 400
    assert not FavoriteSlot.objects.filter(user=favorite_owner).exists()


@pytest.mark.django_db
def test_work_outside_collection_is_rejected_without_mutation(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    client = _client_for(favorite_owner)
    response = client.put(
        "/api/accounts/me/favorites/",
        {"slots": [{"slot": 1, "work_id": str(favorite_works[0].id)}]},
        format="json",
    )
    assert response.status_code == 400
    assert not FavoriteSlot.objects.filter(user=favorite_owner).exists()


@pytest.mark.django_db
def test_replace_is_a_full_overwrite_not_a_merge(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    for work in favorite_works[:3]:
        LibraryEntry.objects.create(user=favorite_owner, work=work, current_status="completed")

    client = _client_for(favorite_owner)
    first = client.put(
        "/api/accounts/me/favorites/",
        {
            "slots": [
                {"slot": 1, "work_id": str(favorite_works[0].id)},
                {"slot": 2, "work_id": str(favorite_works[1].id)},
            ]
        },
        format="json",
    )
    assert first.status_code == 200

    second = client.put(
        "/api/accounts/me/favorites/",
        {"slots": [{"slot": 5, "work_id": str(favorite_works[2].id)}]},
        format="json",
    )
    assert second.status_code == 200
    slots = second.json()["slots"]
    assert slots[0]["work_id"] is None
    assert slots[1]["work_id"] is None
    assert slots[4]["work_id"] == str(favorite_works[2].id)
    assert FavoriteSlot.objects.filter(user=favorite_owner).count() == 1


@pytest.mark.django_db
def test_anonymous_cannot_read_or_write_favorites(favorite_owner, favorite_works) -> None:  # noqa: ANN001
    client = APIClient()
    get_response = client.get("/api/accounts/me/favorites/")
    assert get_response.status_code in (401, 403)

    put_response = client.put("/api/accounts/me/favorites/", {"slots": []}, format="json")
    assert put_response.status_code in (401, 403)
    assert not FavoriteSlot.objects.filter(user=favorite_owner).exists()


@pytest.mark.django_db
def test_favorite_payload_cannot_reference_another_users_work_ownership(  # noqa: ANN201
    favorite_owner, favorite_works
):
    """IDOR guard: user B cannot add a favorite tied to user A's own
    LibraryEntry -- ownership must be re-checked for the requesting user,
    not merely "does any LibraryEntry for this work exist"."""
    other_owner = User.objects.create_user(
        username="favorite-other-owner", password="Ashgrove-Talon-2209-Bluff!"
    )
    LibraryEntry.objects.create(user=other_owner, work=favorite_works[0], current_status="completed")

    client = _client_for(favorite_owner)
    response = client.put(
        "/api/accounts/me/favorites/",
        {"slots": [{"slot": 1, "work_id": str(favorite_works[0].id)}]},
        format="json",
    )
    assert response.status_code == 400
    assert not FavoriteSlot.objects.filter(user=favorite_owner).exists()
