"""Tests for the public profile projection (Plan 01-07 Task 2, PROF-02/INV-05)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import AccountProfile, FavoriteSlot, ProfileVisibility
from catalogue.models import GameWork
from library import services
from library.models import CustomList, CustomListItem, GameComment, LibraryEntry
from social.models import Friendship, RelationshipPair

User = get_user_model()

HOSTILE_FIXTURES_PATH = Path(__file__).resolve().parents[4] / "e2e" / "fixtures" / "hostile.json"

# Every field a public profile response must NEVER contain, regardless of
# nesting depth (INV-05).
FORBIDDEN_KEYS = {
    "email",
    "password",
    "id",
    "user_id",
    "pk",
    "session_key",
    "sessionid",
    "is_staff",
    "is_superuser",
    "copies",
    "owned_copies",
    "release_id",
    "edition_id",
    "idempotency_key",
    "format",
    "notes",
    "purchase",
    "location",
    "rating_half_steps",
    "visibility",
    "version",
}


def _assert_no_forbidden_keys(value) -> None:  # noqa: ANN001
    if isinstance(value, dict):
        for key, nested in value.items():
            assert key not in FORBIDDEN_KEYS, f"forbidden key '{key}' leaked into public profile response"
            _assert_no_forbidden_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_keys(item)


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="profile-game", original_title="Profile Game")


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="profile-user-a", password="Profile-User-A-Pass-9!", email="a@example.invalid")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="profile-user-b", password="Profile-User-B-Pass-9!", email="b@example.invalid")


def _make_friends(user_a, user_b) -> None:  # noqa: ANN001
    low_user, high_user = sorted((user_a, user_b), key=lambda user: user.pk)
    pair = RelationshipPair.objects.create(low_user=low_user, high_user=high_user)
    Friendship.objects.create(pair=pair)


@pytest.mark.django_db
def test_authorized_profile_returns_alias_activity_and_summary(work, user_a) -> None:  # noqa: ANN001
    entry = LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    services.set_rating(user=user_a, work=work, rating_half_steps=9)  # rating must never leak (INV-05)
    entry.refresh_from_db()

    client = _client_for(user_a)
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    assert response.status_code == 200
    body = response.json()

    assert body["alias"] == user_a.username
    assert body["activity"] == [
        {"work_slug": "profile-game", "work_title": "Profile Game", "status": "playing"}
    ]
    assert body["summary"]["playing"] == 1
    assert body["summary"]["pending"] == 0


@pytest.mark.django_db
def test_nonexistent_and_inactive_aliases_return_identical_404(user_a) -> None:  # noqa: ANN001
    inactive_user = User.objects.create_user(username="profile-inactive", password="Profile-Inactive-Pass-9!")
    inactive_user.is_active = False
    inactive_user.save(update_fields=["is_active"])

    client = _client_for(user_a)
    missing_response = client.get("/api/accounts/profiles/does-not-exist/")
    inactive_response = client.get(f"/api/accounts/profiles/{inactive_user.username}/")

    assert missing_response.status_code == 404
    assert inactive_response.status_code == 404
    assert missing_response.json() == inactive_response.json()


@pytest.mark.django_db
def test_response_never_contains_private_fields_recursively(work, user_a) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="completed")
    services.set_rating(user=user_a, work=work, rating_half_steps=10)

    client = APIClient()
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    _assert_no_forbidden_keys(response.json())


@pytest.mark.django_db
def test_user_a_public_profile_never_reveals_user_b_data(work, user_a, user_b) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    LibraryEntry.objects.create(user=user_b, work=work, current_status="abandoned")

    client = _client_for(user_a)
    profile_a = client.get(f"/api/accounts/profiles/{user_a.username}/").json()
    profile_b = client.get(f"/api/accounts/profiles/{user_b.username}/").json()

    assert profile_a["activity"][0]["status"] == "playing"
    assert "activity" not in profile_b
    assert profile_a["alias"] != profile_b["alias"]


@pytest.mark.django_db
def test_hostile_alias_returned_as_inert_text_never_executed_or_stripped() -> None:
    payloads = json.loads(HOSTILE_FIXTURES_PATH.read_text(encoding="utf-8"))["untrustedText"]
    # Django's User.objects.create_user does not run form-level username
    # validators -- simulating a value that somehow bypassed a signup form,
    # to prove the *serializer* is the actual safety boundary, not reliance
    # on upstream validation alone. Pick the payload with no literal "/" --
    # the alias becomes a URL path segment here, and a slash is a path
    # separator to Django's router regardless of XSS safety; that's a
    # routing property, not a text-escaping one, so it's exercised
    # separately by the request-body-based hostile-title test below.
    hostile_username = next(p for p in payloads if "/" not in p)[:150]
    user = User.objects.create_user(username=hostile_username, password="Hostile-Alias-Pass-9!")

    client = APIClient()
    response = client.get(f"/api/accounts/profiles/{hostile_username}/")
    assert response.status_code == 200
    # Returned verbatim as a plain JSON string value -- JSON has no markup
    # to inject into; the frontend is responsible for text-only rendering.
    assert response.json()["alias"] == hostile_username
    assert isinstance(response.json()["alias"], str)


@pytest.mark.django_db
def test_hostile_game_title_returned_as_inert_text(user_a) -> None:  # noqa: ANN001
    payloads = json.loads(HOSTILE_FIXTURES_PATH.read_text(encoding="utf-8"))["untrustedText"]
    hostile_title = payloads[1]
    hostile_work = GameWork.objects.create(
        canonical_slug="hostile-title-game", original_title=hostile_title, title_en=hostile_title
    )
    LibraryEntry.objects.create(user=user_a, work=hostile_work, current_status="pending")

    client = _client_for(user_a)
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    activity = response.json()["activity"]
    assert activity[0]["work_title"] == hostile_title


# --------------------------------------------------------------------------
# Task 2: independent collection_visibility/favorites_visibility (D-02/D-03).
# --------------------------------------------------------------------------


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


_PRIVACY_COMBINATIONS = [
    (ProfileVisibility.PUBLIC, ProfileVisibility.PUBLIC),
    (ProfileVisibility.PUBLIC, ProfileVisibility.PRIVATE),
    (ProfileVisibility.PRIVATE, ProfileVisibility.PUBLIC),
    (ProfileVisibility.PRIVATE, ProfileVisibility.PRIVATE),
]


@pytest.mark.django_db
@pytest.mark.parametrize("collection_visibility,favorites_visibility", _PRIVACY_COMBINATIONS)
def test_privacy_combination_is_enforced_for_anonymous_and_user_b(  # noqa: ANN201
    work, user_a, user_b, collection_visibility, favorites_visibility
):
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    AccountProfile.objects.create(
        user=user_a,
        collection_visibility=collection_visibility,
        favorites_visibility=favorites_visibility,
    )
    FavoriteSlot.objects.create(user=user_a, slot=1, work=work)
    _make_friends(user_a, user_b)

    anonymous_response = APIClient().get(f"/api/accounts/profiles/{user_a.username}/")
    assert anonymous_response.status_code == 200
    assert "activity" not in anonymous_response.json()
    assert "favorites" not in anonymous_response.json()

    for viewer_client in (_client_for(user_b),):
        response = viewer_client.get(f"/api/accounts/profiles/{user_a.username}/")
        assert response.status_code == 200
        body = response.json()

        if collection_visibility == ProfileVisibility.PUBLIC:
            assert body["activity"] != []
        else:
            assert body["activity"] == []

        if favorites_visibility == ProfileVisibility.PUBLIC:
            assert body["favorites"][0] is not None
        else:
            assert all(item is None for item in body["favorites"])

        _assert_no_forbidden_keys(body)


@pytest.mark.django_db
@pytest.mark.parametrize("collection_visibility,favorites_visibility", _PRIVACY_COMBINATIONS)
def test_owner_always_sees_their_own_data_regardless_of_visibility(  # noqa: ANN201
    work, user_a, collection_visibility, favorites_visibility
):
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    AccountProfile.objects.create(
        user=user_a,
        collection_visibility=collection_visibility,
        favorites_visibility=favorites_visibility,
    )
    FavoriteSlot.objects.create(user=user_a, slot=1, work=work)

    client = _client_for(user_a)
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    assert response.status_code == 200
    body = response.json()
    assert body["activity"] != []
    assert body["favorites"][0] is not None


@pytest.mark.django_db
def test_default_profile_without_explicit_settings_is_public(work, user_a) -> None:  # noqa: ANN001
    """No AccountProfile row at all (never edited) behaves like the
    Phase 1 default: public, matching pre-existing accounts that predate
    this phase's privacy toggle."""
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    FavoriteSlot.objects.create(user=user_a, slot=1, work=work)

    client = _client_for(user_a)
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    body = response.json()
    assert body["activity"] != []
    assert body["favorites"][0] is not None


# --------------------------------------------------------------------------
# Plan 05-02 Task 3: public comments/lists aggregate (LIB-03/LIB-04),
# independently gated by each item's own ``visibility`` field.
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_public_profile_includes_only_public_comments_for_third_parties(work, user_a, user_b) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    GameComment.objects.create(user=user_a, work=work, text="Public thoughts.", visibility="public")
    private_work = GameWork.objects.create(canonical_slug="private-comment-game", original_title="Private Comment Game")
    LibraryEntry.objects.create(user=user_a, work=private_work, current_status="playing")
    GameComment.objects.create(user=user_a, work=private_work, text="Private thoughts.", visibility="private")

    _make_friends(user_a, user_b)
    response = _client_for(user_b).get(f"/api/accounts/profiles/{user_a.username}/")
    texts = {c["text"] for c in response.json()["comments"]}
    assert texts == {"Public thoughts."}
    assert "comments" not in APIClient().get(f"/api/accounts/profiles/{user_a.username}/").json()


@pytest.mark.django_db
def test_owner_sees_all_own_comments_regardless_of_visibility(work, user_a) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    GameComment.objects.create(user=user_a, work=work, text="Private thoughts.", visibility="private")

    client = _client_for(user_a)
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    texts = {c["text"] for c in response.json()["comments"]}
    assert texts == {"Private thoughts."}


@pytest.mark.django_db
def test_public_profile_includes_only_public_lists_for_third_parties(work, user_a, user_b) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    public_list = CustomList.objects.create(user=user_a, name="Public List", visibility="public")
    CustomListItem.objects.create(list=public_list, work=work, position=1)
    private_list = CustomList.objects.create(user=user_a, name="Private List", visibility="private")
    CustomListItem.objects.create(list=private_list, work=work, position=1)

    _make_friends(user_a, user_b)
    response = _client_for(user_b).get(f"/api/accounts/profiles/{user_a.username}/")
    names = {lst["name"] for lst in response.json()["lists"]}
    assert names == {"Public List"}
    assert "lists" not in APIClient().get(f"/api/accounts/profiles/{user_a.username}/").json()


@pytest.mark.django_db
def test_owner_sees_all_own_lists_regardless_of_visibility(work, user_a) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    private_list = CustomList.objects.create(user=user_a, name="Private List", visibility="private")
    CustomListItem.objects.create(list=private_list, work=work, position=1)

    client = _client_for(user_a)
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    names = {lst["name"] for lst in response.json()["lists"]}
    assert names == {"Private List"}


@pytest.mark.django_db
def test_public_list_projection_has_no_forbidden_keys(work, user_a) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=user_a, work=work, current_status="playing")
    custom_list = CustomList.objects.create(user=user_a, name="Public List", visibility="public")
    CustomListItem.objects.create(list=custom_list, work=work, position=1)
    GameComment.objects.create(user=user_a, work=work, text="Some text.", visibility="public")

    client = _client_for(user_a)
    response = client.get(f"/api/accounts/profiles/{user_a.username}/")
    _assert_no_forbidden_keys(response.json())
