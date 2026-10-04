"""Protected collection/list projections and canonical shareable locators."""

from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from catalogue.models import GameWork
from library import services as library_services
from library.models import CustomList, CustomListItem, GameComment, LibraryEntry
from social import services as social_services

User = get_user_model()

PROJECTION_KEYS = {"game", "cover", "year", "platform", "backlog_status", "personal_rating"}
PRIVATE_KEYS = {
    "id",
    "user_id",
    "owner_id",
    "work_id",
    "copy_id",
    "copies",
    "purchase",
    "purchase_date",
    "price",
    "currency",
    "store",
    "location",
    "storage_location",
    "notes",
    "edition_id",
    "release_id",
    "idempotency_key",
}


@pytest.fixture
def owner(db):  # noqa: ANN001
    return User.objects.create_user(username="visibility-owner", password="Owner-pass-9!")


@pytest.fixture
def friend(db):  # noqa: ANN001
    return User.objects.create_user(username="visibility-friend", password="Friend-pass-9!")


@pytest.fixture
def stranger(db):  # noqa: ANN001
    return User.objects.create_user(username="visibility-stranger", password="Stranger-pass-9!")


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(
        canonical_slug="visibility-game",
        original_title="Visibility Game",
        first_release_date=date(2024, 5, 10),
    )


def _client(user=None) -> APIClient:  # noqa: ANN001
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _make_friendship(owner, friend) -> None:  # noqa: ANN001
    request = social_services.request_friendship(sender=friend, alias=owner.username)
    social_services.accept_friendship_request(receiver=owner, request_id=str(request.id))


def _create_public_list(owner, work, *, name="Shared list"):  # noqa: ANN001
    library_entry = LibraryEntry.objects.create(
        user=owner, work=work, current_status="completed", rating_half_steps=8
    )
    custom_list = CustomList.objects.create(user=owner, name=name, visibility="public")
    CustomListItem.objects.create(list=custom_list, work=work, position=1)
    return library_entry, custom_list


def _assert_no_private_fields(value):  # noqa: ANN001
    if isinstance(value, dict):
        assert not PRIVATE_KEYS.intersection(value)
        for nested in value.values():
            _assert_no_private_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_private_fields(nested)


@pytest.mark.django_db
def test_public_slug_is_stable_and_unique_per_owner(owner, stranger, work):  # noqa: ANN001
    first = library_services.create_list(user=owner, name="My Favourites")
    second = library_services.create_list(user=owner, name="My Favourites")
    other_owner = library_services.create_list(user=stranger, name="My Favourites")

    assert first.public_slug == "my-favourites"
    assert second.public_slug == "my-favourites-2"
    assert other_owner.public_slug == first.public_slug

    first_slug = first.public_slug
    library_services.update_list(custom_list=first, name="Renamed list")
    assert first.public_slug == first_slug
    assert CustomList.objects.get(pk=first.pk).public_slug == first_slug


@pytest.mark.django_db
def test_owner_and_friend_list_routes_expose_only_manual_allowlist(owner, friend, work):  # noqa: ANN001
    _entry, custom_list = _create_public_list(owner, work)
    _make_friendship(owner, friend)

    response = _client(friend).get(
        f"/api/library/profiles/{owner.username}/lists/{custom_list.public_slug}/"
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"name", "items"}
    assert body["name"] == "Shared list"
    assert len(body["items"]) == 1
    assert set(body["items"][0]) == PROJECTION_KEYS
    assert body["items"][0]["game"] == {"slug": "visibility-game", "title": "Visibility Game"}
    assert body["items"][0]["year"] == 2024
    assert body["items"][0]["backlog_status"] == "completed"
    assert body["items"][0]["personal_rating"] == 8
    _assert_no_private_fields(body)

    owner_response = _client(owner).get(
        f"/api/library/profiles/{owner.username}/lists/{custom_list.public_slug}/"
    )
    assert owner_response.status_code == 200
    assert owner_response.json() == body


@pytest.mark.django_db
def test_friend_collection_projection_is_allowlisted_and_excludes_inventory(owner, friend, work):  # noqa: ANN001
    _entry, _custom_list = _create_public_list(owner, work)
    _make_friendship(owner, friend)

    response = _client(friend).get(f"/api/library/profiles/{owner.username}/collection/")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items"}
    assert len(body["items"]) == 1
    assert set(body["items"][0]) == PROJECTION_KEYS
    assert body["items"][0]["personal_rating"] == 8
    _assert_no_private_fields(body)


@pytest.mark.django_db
def test_anonymous_and_non_friend_get_same_404_for_direct_collection_and_list(owner, stranger, work):  # noqa: ANN001
    _entry, custom_list = _create_public_list(owner, work)
    list_url = f"/api/library/profiles/{owner.username}/lists/{custom_list.public_slug}/"
    collection_url = f"/api/library/profiles/{owner.username}/collection/"

    for client in (_client(), _client(stranger)):
        list_response = client.get(list_url)
        collection_response = client.get(collection_url)
        missing_response = client.get("/api/library/profiles/missing-owner/collection/")

        assert list_response.status_code == 404
        assert collection_response.status_code == 404
        assert list_response.json() == missing_response.json()
        assert collection_response.json() == missing_response.json()


@pytest.mark.django_db
def test_block_revokes_direct_collection_and_list_access_with_generic_404(owner, friend, work):  # noqa: ANN001
    _entry, custom_list = _create_public_list(owner, work)
    _make_friendship(owner, friend)
    list_url = f"/api/library/profiles/{owner.username}/lists/{custom_list.public_slug}/"
    collection_url = f"/api/library/profiles/{owner.username}/collection/"
    before = _client(friend).get(list_url)
    assert before.status_code == 200

    social_services.block_user(actor=owner, alias=friend.username)
    missing = _client(friend).get("/api/library/profiles/no-owner/collection/")

    for url in (list_url, collection_url):
        response = _client(friend).get(url)
        assert response.status_code == 404
        assert response.json() == missing.json()


@pytest.mark.django_db
def test_known_internal_list_id_cannot_bypass_owner_slug_locator(owner, stranger, work):  # noqa: ANN001
    _entry, custom_list = _create_public_list(owner, work)
    _make_friendship(owner, stranger)

    by_id = _client(stranger).get(f"/api/library/profiles/{owner.username}/lists/{custom_list.id}/")
    wrong_slug = _client(stranger).get(f"/api/library/profiles/{owner.username}/lists/not-the-slug/")

    assert by_id.status_code == 404
    assert wrong_slug.status_code == 404


@pytest.mark.django_db
def test_private_list_is_not_shared_even_with_accepted_friend(owner, friend, work):  # noqa: ANN001
    LibraryEntry.objects.create(user=owner, work=work, current_status="playing", rating_half_steps=7)
    private_list = CustomList.objects.create(user=owner, name="Private list", visibility="private")
    CustomListItem.objects.create(list=private_list, work=work, position=1)
    _make_friendship(owner, friend)

    response = _client(friend).get(
        f"/api/library/profiles/{owner.username}/lists/{private_list.public_slug}/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_friend_cannot_receive_profile_content_when_collection_is_private(owner, friend, work):  # noqa: ANN001
    AccountProfile.objects.create(user=owner, collection_visibility="private")
    LibraryEntry.objects.create(user=owner, work=work, current_status="playing", rating_half_steps=7)
    _make_friendship(owner, friend)

    response = _client(friend).get(f"/api/accounts/profiles/{owner.username}/")

    assert response.status_code == 200
    assert response.json()["activity"] == []


@pytest.mark.django_db
def test_collection_and_list_order_is_not_inferred_from_creation_time(owner, friend, work):  # noqa: ANN001
    second_work = GameWork.objects.create(canonical_slug="second-game", original_title="Second Game")
    LibraryEntry.objects.create(user=owner, work=work, current_status="pending", rating_half_steps=5)
    LibraryEntry.objects.create(user=owner, work=second_work, current_status="completed", rating_half_steps=9)
    custom_list = CustomList.objects.create(user=owner, name="Ordered", visibility="public")
    CustomListItem.objects.create(list=custom_list, work=second_work, position=1)
    CustomListItem.objects.create(list=custom_list, work=work, position=2)
    _make_friendship(owner, friend)

    response = _client(friend).get(
        f"/api/library/profiles/{owner.username}/lists/{custom_list.public_slug}/"
    )

    assert response.status_code == 200
    assert [item["game"]["slug"] for item in response.json()["items"]] == ["second-game", "visibility-game"]
    assert [item["backlog_status"] for item in response.json()["items"]] == ["completed", "pending"]


@pytest.mark.django_db
def test_game_comments_are_visible_only_to_owner_or_accepted_friend(owner, friend, stranger, work):  # noqa: ANN001
    LibraryEntry.objects.create(user=owner, work=work, current_status="completed")
    GameComment.objects.create(user=owner, work=work, text="Owner comment", visibility="public")
    GameComment.objects.create(user=friend, work=work, text="Friend comment", visibility="public")
    _make_friendship(owner, friend)

    anonymous = _client().get(f"/api/library/entries/{work.id}/comments/")
    stranger_response = _client(stranger).get(f"/api/library/entries/{work.id}/comments/")
    friend_response = _client(friend).get(f"/api/library/entries/{work.id}/comments/")

    assert anonymous.json()["comments"] == []
    assert stranger_response.json()["comments"] == []
    assert {item["text"] for item in friend_response.json()["comments"]} == {"Owner comment", "Friend comment"}
    assert set(friend_response.json()["comments"][0]) == {"author_alias", "text", "date"}


@pytest.mark.django_db
def test_private_third_party_comments_and_blocked_relationships_stay_hidden(owner, friend, stranger, work):  # noqa: ANN001
    LibraryEntry.objects.create(user=owner, work=work, current_status="completed")
    GameComment.objects.create(user=owner, work=work, text="Owner public", visibility="public")
    GameComment.objects.create(user=stranger, work=work, text="Stranger private", visibility="private")
    _make_friendship(owner, friend)

    friend_response = _client(friend).get(f"/api/library/entries/{work.id}/comments/")
    assert {item["text"] for item in friend_response.json()["comments"]} == {"Owner public"}

    social_services.block_user(actor=owner, alias=friend.username)
    blocked_response = _client(friend).get(f"/api/library/entries/{work.id}/comments/")
    assert blocked_response.json() == {"comments": []}


@pytest.mark.django_db
def test_comment_projection_ignores_identity_fields_and_keeps_hostile_text_plain(owner, work):  # noqa: ANN001
    LibraryEntry.objects.create(user=owner, work=work, current_status="completed")
    payload = {
        "text": "<img src=x onerror=alert(1)>",
        "visibility": "public",
        "owner_id": "someone-else",
        "author_id": "someone-else",
    }
    created = _client(owner).post(f"/api/library/entries/{work.id}/comments/", payload, format="json")
    assert created.status_code == 201
    assert created.json()["text"] == payload["text"]
    assert not {"owner_id", "author_id", "sender_id", "recipient_id"}.intersection(created.json())
    listed = _client(owner).get(f"/api/library/entries/{work.id}/comments/").json()
    assert listed["comments"][0]["text"] == payload["text"]
    assert listed["comments"][0]["is_own"] is True
    assert not {"owner_id", "author_id", "sender_id", "recipient_id"}.intersection(listed["comments"][0])
