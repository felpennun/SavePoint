"""Backend of the friends page: friend card, notifications, answering a
recommendation and withdrawing a sent request."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import AccountProfile, FavoriteSlot
from catalogue.models import GameWork
from library.models import LibraryEntry
from social import services
from social.models import SocialNotice

User = get_user_model()
PASSWORD = "Social-pass-9!"  # noqa: S105 - test fixture


@pytest.fixture
def me(db):  # noqa: ANN001
    return User.objects.create_user(username="page-me", password=PASSWORD)


@pytest.fixture
def pal(db):  # noqa: ANN001
    user = User.objects.create_user(username="page-pal", password=PASSWORD)
    AccountProfile.objects.create(user=user, display_name="Marta Gil", bio="Puzles y mapas.")
    return user


@pytest.fixture
def stranger(db):  # noqa: ANN001
    return User.objects.create_user(username="page-stranger", password=PASSWORD)


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="page-game", original_title="Page Game")


def _client(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user)
    return client


def _befriend(first, second) -> None:  # noqa: ANN001
    request = services.request_friendship(sender=first, alias=second.username)
    services.accept_friendship_request(receiver=second, request_id=str(request.id))


@pytest.mark.django_db
def test_friend_card_is_full_for_friends_and_basic_for_strangers(me, pal, stranger, work) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=pal, work=work, current_status="completed")
    FavoriteSlot.objects.create(user=pal, slot=1, work=work)
    _befriend(me, pal)

    card = _client(me).get(f"/api/social/friends/{pal.username}/").json()
    assert card["relationship"] == "friend"
    assert card["display_name"] == "Marta Gil"
    assert card["bio"] == "Puzles y mapas."
    assert card["favorites"][0]["title"] == "Page Game"
    assert card["favorites"][1] is None
    assert card["summary"]["completed"] == 1
    assert card["owned_work_ids"] == [str(work.id)]

    basic = _client(stranger).get(f"/api/social/friends/{pal.username}/").json()
    assert basic == {"alias": "page-pal", "relationship": "none"}


@pytest.mark.django_db
def test_friend_card_honours_the_owners_privacy_switches(me, pal, work) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=pal, work=work, current_status="completed")
    FavoriteSlot.objects.create(user=pal, slot=1, work=work)
    AccountProfile.objects.filter(user=pal).update(collection_visibility="private", favorites_visibility="private")
    _befriend(me, pal)

    card = _client(me).get(f"/api/social/friends/{pal.username}/").json()
    assert card["favorites_visible"] is False
    assert card["favorites"] == [None] * 5
    assert card["collection_visible"] is False
    assert card["summary"] is None
    assert card["owned_work_ids"] is None


@pytest.mark.django_db
def test_pending_requests_expose_their_ids_and_can_be_withdrawn(me, stranger) -> None:  # noqa: ANN001
    request = services.request_friendship(sender=me, alias=stranger.username)
    card = _client(me).get(f"/api/social/friends/{stranger.username}/").json()
    assert card["relationship"] == "pending_sent"
    assert card["request_id"] == str(request.id)

    other = _client(stranger).post(f"/api/social/requests/{request.id}/cancel/")
    assert other.status_code == 404  # only the sender may withdraw it

    cancelled = _client(me).post(f"/api/social/requests/{request.id}/cancel/")
    assert cancelled.status_code == 200
    assert _client(me).get("/api/social/requests/").json()["sent"] == []


@pytest.mark.django_db
def test_notifications_cover_requests_recommendations_and_notices(me, pal, stranger, work) -> None:  # noqa: ANN001
    services.request_friendship(sender=stranger, alias=me.username)
    _befriend(me, pal)  # pal accepts: I get an "accepted" notice
    services.send_recommendation(sender=pal, recipient_alias=me.username, work_id=work.id, text="Te va a gustar")

    body = _client(me).get("/api/social/notifications/").json()
    kinds = sorted(item["kind"] for item in body["notifications"])
    assert kinds == ["accepted", "rec", "request"]
    rec = next(item for item in body["notifications"] if item["kind"] == "rec")
    assert rec["actor"]["name"] == "Marta Gil"  # friends are shown by their full name
    assert rec["work"]["title"] == "Page Game"
    assert rec["note"] == "Te va a gustar"
    request = next(item for item in body["notifications"] if item["kind"] == "request")
    assert request["actor"]["name"] == "page-stranger"  # strangers only by alias
    assert body["unread"] == 3

    assert _client(me).post("/api/social/notifications/read-all/").json()["unread"] == 1  # the request still waits
    accept = _client(me).post(f"/api/social/requests/{request['request_id']}/accept/")
    assert accept.status_code == 200
    assert _client(me).get("/api/social/notifications/").json()["unread"] == 0


@pytest.mark.django_db
def test_adding_a_recommendation_puts_it_in_the_backlog_and_tells_the_sender(me, pal, work) -> None:  # noqa: ANN001
    _befriend(me, pal)
    message = services.send_recommendation(sender=pal, recipient_alias=me.username, work_id=work.id)

    response = _client(me).post(f"/api/social/messages/{message.id}/respond/", {"response": "added"}, format="json")
    assert response.status_code == 200
    assert LibraryEntry.objects.get(user=me, work=work).current_status == "pending"
    assert SocialNotice.objects.filter(recipient=pal, actor=me, kind="rec_added", work=work).exists()

    again = _client(me).post(f"/api/social/messages/{message.id}/respond/", {"response": "dismissed"}, format="json")
    assert again.status_code == 409  # one answer per recommendation

    state = next(
        item for item in _client(me).get("/api/social/notifications/").json()["notifications"] if item["kind"] == "rec"
    )
    assert state["state"] == "added" and state["read"] is True
    sender_view = _client(pal).get("/api/social/notifications/").json()["notifications"]
    assert any(item["kind"] == "rec_added" for item in sender_view)


@pytest.mark.django_db
def test_dismissing_leaves_the_collection_untouched(me, pal, work) -> None:  # noqa: ANN001
    _befriend(me, pal)
    message = services.send_recommendation(sender=pal, recipient_alias=me.username, work_id=work.id)
    response = _client(me).post(f"/api/social/messages/{message.id}/respond/", {"response": "dismissed"}, format="json")
    assert response.status_code == 200
    assert not LibraryEntry.objects.filter(user=me, work=work).exists()
    assert not SocialNotice.objects.filter(recipient=pal).filter(kind="rec_added").exists()


@pytest.mark.django_db
def test_only_the_recipient_can_answer_and_bad_values_are_rejected(me, pal, stranger, work) -> None:  # noqa: ANN001
    _befriend(me, pal)
    message = services.send_recommendation(sender=pal, recipient_alias=me.username, work_id=work.id)
    assert _client(stranger).post(f"/api/social/messages/{message.id}/respond/", {"response": "added"}, format="json").status_code == 404
    assert _client(me).post(f"/api/social/messages/{message.id}/respond/", {"response": "nope"}, format="json").status_code == 400


@pytest.mark.django_db
def test_friend_avatar_is_served_only_to_friends(me, pal, stranger) -> None:  # noqa: ANN001
    AccountProfile.objects.filter(user=pal).update(avatar_image=b"\x89PNG\r\n\x1a\nxx", avatar_image_type="image/png")
    _befriend(me, pal)
    assert _client(me).get(f"/api/accounts/profiles/{pal.username}/avatar/").status_code == 200
    assert _client(stranger).get(f"/api/accounts/profiles/{pal.username}/avatar/").status_code == 404
    assert APIClient().get(f"/api/accounts/profiles/{pal.username}/avatar/").status_code in (401, 403)


@pytest.mark.django_db
def test_detailed_profile_shows_shared_data_and_hides_private_data(me, pal, stranger, work) -> None:  # noqa: ANN001
    from library.models import CustomList, CustomListItem, GameComment

    LibraryEntry.objects.create(user=pal, work=work, current_status="completed", rating_half_steps=8)
    public_list = CustomList.objects.create(user=pal, name="Abierta", visibility="public")
    CustomListItem.objects.create(list=public_list, work=work, position=1)
    CustomList.objects.create(user=pal, name="Secreta", visibility="private")
    GameComment.objects.create(user=pal, work=work, text="Visible", visibility="public")
    GameComment.objects.create(user=pal, work=work, text="Oculto", visibility="private")
    _befriend(me, pal)

    body = _client(me).get(f"/api/social/friends/{pal.username}/profile/").json()
    assert body["relationship"] == "friend"
    assert body["display_name"] == "Marta Gil"
    assert [item["game"]["title"] for item in body["collection"]] == ["Page Game"]
    assert "display_rating" in body["collection"][0]  # the IGDB score shown on the card
    assert body["collection"][0]["is_platinum"] is False
    assert [item["name"] for item in body["lists"]] == ["Abierta"]
    assert body["lists"][0]["visibility"] is None  # visibility flags are for the owner only
    assert [item["text"] for item in body["comments"]] == ["Visible"]
    assert body["member_since"]

    own = _client(pal).get(f"/api/social/friends/{pal.username}/profile/").json()
    assert sorted(item["name"] for item in own["lists"]) == ["Abierta", "Secreta"]
    assert sorted(item["text"] for item in own["comments"]) == ["Oculto", "Visible"]

    basic = _client(stranger).get(f"/api/social/friends/{pal.username}/profile/").json()
    assert basic == {"alias": "page-pal", "relationship": "none"}


@pytest.mark.django_db
def test_detailed_profile_respects_a_private_collection(me, pal, work) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=pal, work=work, current_status="completed")
    AccountProfile.objects.filter(user=pal).update(collection_visibility="private")
    _befriend(me, pal)
    body = _client(me).get(f"/api/social/friends/{pal.username}/profile/").json()
    assert body["collection_visible"] is False
    assert body["collection"] == []
    assert body["summary"] is None


@pytest.mark.django_db
def test_friend_cover_is_served_only_to_friends(me, pal, stranger) -> None:  # noqa: ANN001
    AccountProfile.objects.filter(user=pal).update(cover_image=b"\x89PNG\r\n\x1a\nxx", cover_image_type="image/png")
    _befriend(me, pal)
    assert _client(me).get(f"/api/accounts/profiles/{pal.username}/cover/").status_code == 200
    assert _client(stranger).get(f"/api/accounts/profiles/{pal.username}/cover/").status_code == 404


@pytest.mark.django_db
def test_unread_notifications_come_first_even_when_older(me, pal, stranger) -> None:  # noqa: ANN001
    services.request_friendship(sender=stranger, alias=me.username)  # unread, older
    _befriend(me, pal)  # newer "accepted" notice
    _client(me).post("/api/social/notifications/read-all/")  # reads the notice, not the pending request

    kinds = [item["kind"] for item in _client(me).get("/api/social/notifications/").json()["notifications"]]
    assert kinds == ["request", "accepted"]
