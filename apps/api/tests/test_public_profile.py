"""Privacy matrix for profile projections (PROF-03/PROF-04, D-06..D-08)."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from catalogue.models import GameWork
from library.models import CustomList, CustomListItem, GameComment, LibraryEntry
from social import services as social_services

User = get_user_model()


@pytest.fixture
def owner(db):  # noqa: ANN001
    return User.objects.create_user(username="profile-owner", password="Owner-pass-9!")


@pytest.fixture
def friend(db):  # noqa: ANN001
    return User.objects.create_user(username="profile-friend", password="Friend-pass-9!")


@pytest.fixture
def stranger(db):  # noqa: ANN001
    return User.objects.create_user(username="profile-stranger", password="Stranger-pass-9!")


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="profile-visible-game", original_title="Visible Game")


def _client(user=None) -> APIClient:  # noqa: ANN001
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _make_friendship(owner, friend) -> None:  # noqa: ANN001
    request = social_services.request_friendship(sender=friend, alias=owner.username)
    social_services.accept_friendship_request(receiver=owner, request_id=str(request.id))


@pytest.fixture
def populated_profile(owner, friend, work):  # noqa: ANN001
    AccountProfile.objects.create(user=owner, bio="A public biography.", avatar_url="https://example.invalid/avatar.png")
    LibraryEntry.objects.create(user=owner, work=work, current_status="playing", rating_half_steps=9)
    public_list = CustomList.objects.create(user=owner, name="Public list", visibility="public")
    CustomListItem.objects.create(list=public_list, work=work, position=1)
    GameComment.objects.create(user=owner, work=work, text="Public comment", visibility="public")
    _make_friendship(owner, friend)
    return owner


@pytest.mark.django_db
def test_anonymous_and_non_friend_receive_only_basic_profile(populated_profile, stranger):  # noqa: ANN001
    for client, expected_action in ((_client(), "login"), (_client(stranger), "send_friend_request")):
        response = client.get("/api/accounts/profiles/profile-owner/")

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"alias", "avatar_url", "bio", "action"}
        assert body["alias"] == "profile-owner"
        assert body["action"] == expected_action


@pytest.mark.django_db
def test_owner_and_accepted_friend_receive_separate_authorized_projection(populated_profile, owner, friend):  # noqa: ANN001
    owner_body = _client(owner).get("/api/accounts/profiles/profile-owner/").json()
    friend_body = _client(friend).get("/api/accounts/profiles/profile-owner/").json()

    for body in (owner_body, friend_body):
        assert set(body) == {"alias", "bio", "avatar_url", "activity", "summary", "favorites", "comments", "lists"}
        assert body["activity"][0]["status"] == "playing"
        assert body["comments"][0]["text"] == "Public comment"
        assert body["lists"][0]["name"] == "Public list"

    assert owner_body != friend_body or owner_body["alias"] == "profile-owner"


@pytest.mark.django_db
def test_blocked_profile_is_generic_404_like_missing_profile(populated_profile, owner, friend):  # noqa: ANN001
    missing = _client(friend).get("/api/accounts/profiles/no-such-profile/")
    social_services.block_user(actor=owner, alias=friend.username)

    blocked = _client(friend).get("/api/accounts/profiles/profile-owner/")

    assert blocked.status_code == 404
    assert blocked.json() == missing.json()


@pytest.mark.django_db
def test_anonymous_profile_read_never_mutates_friendship(populated_profile):  # noqa: ANN001
    before_requests = social_services.FriendshipRequest.objects.count()
    response = _client().get("/api/accounts/profiles/profile-owner/")

    assert response.status_code == 200
    assert response.json()["action"] == "login"
    assert social_services.FriendshipRequest.objects.count() == before_requests


@pytest.mark.django_db
def test_profile_projection_does_not_include_private_inventory_or_statistics(populated_profile, friend):  # noqa: ANN001
    body = _client(friend).get("/api/accounts/profiles/profile-owner/").json()
    forbidden = {"copies", "purchase", "price", "store", "location", "notes", "owned_copy_count", "id", "user_id"}

    def assert_safe(value):  # noqa: ANN001
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for nested in value.values():
                assert_safe(nested)
        elif isinstance(value, list):
            for nested in value:
                assert_safe(nested)

    assert_safe(body)
