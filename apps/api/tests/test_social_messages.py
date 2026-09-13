"""Tests for private friendship recommendations and inbox isolation."""

from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from catalogue.models import GameWork
from social import services
from social.models import Block, Friendship, FriendshipRequest, SocialMessage


@pytest.fixture
def message_users(db):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    return {
        "alice": user_model.objects.create_user(username="message-alice", password="pass-a"),
        "bob": user_model.objects.create_user(username="message-bob", password="pass-b"),
        "carol": user_model.objects.create_user(username="message-carol", password="pass-c"),
    }


@pytest.fixture
def message_work(db):
    return GameWork.objects.create(
        canonical_slug="message-work",
        original_title="Message Work",
    )


def accept_friendship(sender, receiver):
    request = services.request_friendship(sender=sender, alias=receiver.username)
    services.accept_friendship_request(receiver=receiver, request_id=str(request.id))


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_only_accepted_friend_can_send_and_only_recipient_reads(message_users, message_work):
    alice = message_users["alice"]
    bob = message_users["bob"]
    carol = message_users["carol"]
    accept_friendship(alice, bob)

    sent = client_for(alice).post(
        "/api/social/recommendations/",
        {"recipient_alias": bob.username, "work_id": str(message_work.id), "text": "Play this."},
        format="json",
    )
    assert sent.status_code == 201
    assert sent.json()["message"]["recipient_alias"] == bob.username

    assert client_for(bob).get("/api/social/messages/").json()["messages"][0]["text"] == "Play this."
    assert client_for(alice).get("/api/social/messages/").json()["messages"] == []
    assert client_for(carol).get("/api/social/messages/").json()["messages"] == []
    denied = client_for(carol).post(
        "/api/social/recommendations/",
        {"recipient_alias": bob.username, "work_id": str(message_work.id)},
        format="json",
    )
    assert denied.status_code == 404


@pytest.mark.django_db
def test_mark_read_is_recipient_scoped_and_badge_counts_unread(message_users, message_work):
    alice = message_users["alice"]
    bob = message_users["bob"]
    accept_friendship(alice, bob)
    sent = client_for(alice).post(
        "/api/social/recommendations/",
        {"recipient_alias": bob.username, "work_id": str(message_work.id)},
        format="json",
    )
    message_id = sent.json()["message"]["id"]

    assert client_for(bob).get("/api/social/messages/unread-count/").json() == {"unread_count": 1}
    assert client_for(alice).post(f"/api/social/messages/{message_id}/read/", {}, format="json").status_code == 404
    marked = client_for(bob).post(f"/api/social/messages/{message_id}/read/", {}, format="json")
    assert marked.status_code == 200
    assert marked.json()["message"]["read"] is True
    assert client_for(bob).get("/api/social/messages/unread-count/").json() == {"unread_count": 0}
    assert client_for(bob).post(f"/api/social/messages/{message_id}/unread/", {}, format="json").status_code == 200
    assert client_for(bob).get("/api/social/messages/unread-count/").json() == {"unread_count": 1}


@pytest.mark.django_db
def test_directional_seven_day_cooldown_returns_retry_after(message_users, message_work):
    alice = message_users["alice"]
    bob = message_users["bob"]
    accept_friendship(alice, bob)
    payload = {"recipient_alias": bob.username, "work_id": str(message_work.id), "text": "First."}
    assert client_for(alice).post("/api/social/recommendations/", payload, format="json").status_code == 201

    blocked = client_for(alice).post(
        "/api/social/recommendations/",
        {**payload, "text": "Second."},
        format="json",
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "recommendation_cooldown"
    assert int(blocked["Retry-After"]) > 0
    assert blocked.json()["retry_after_seconds"] == int(blocked["Retry-After"])

    reverse = client_for(bob).post(
        "/api/social/recommendations/",
        {"recipient_alias": alice.username, "work_id": str(message_work.id)},
        format="json",
    )
    assert reverse.status_code == 201


@pytest.mark.django_db
def test_remove_and_block_hide_messages_but_keep_tombstone(message_users, message_work):
    alice = message_users["alice"]
    bob = message_users["bob"]
    accept_friendship(alice, bob)
    sent = client_for(alice).post(
        "/api/social/recommendations/",
        {"recipient_alias": bob.username, "work_id": str(message_work.id), "text": "Private."},
        format="json",
    )
    message_id = sent.json()["message"]["id"]
    assert client_for(alice).post(f"/api/social/friendships/{bob.username}/remove/").status_code == 200
    assert client_for(bob).get("/api/social/messages/").json()["messages"] == []

    accept_friendship(alice, bob)
    assert client_for(alice).post(
        "/api/social/recommendations/",
        {"recipient_alias": bob.username, "work_id": str(message_work.id)},
        format="json",
    ).status_code == 429
    assert client_for(alice).post(f"/api/social/friendships/{bob.username}/block/").status_code == 200
    assert client_for(bob).get("/api/social/messages/").json()["messages"] == []
    assert client_for(bob).post(
        "/api/social/recommendations/",
        {"recipient_alias": alice.username, "work_id": str(message_work.id)},
        format="json",
    ).status_code == 404


@pytest.mark.django_db
def test_message_payload_is_allowlisted_and_plain_text(message_users, message_work):
    alice = message_users["alice"]
    bob = message_users["bob"]
    accept_friendship(alice, bob)
    response = client_for(alice).post(
        "/api/social/recommendations/",
        {
            "recipient_alias": bob.username,
            "work_id": str(message_work.id),
            "text": "<script>alert(1)</script>",
            "sender_id": str(bob.pk),
            "recipient_id": str(alice.pk),
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_cooldown_window_is_exactly_seven_days_and_naive_clock_fails_closed(message_users, message_work):
    alice = message_users["alice"]
    bob = message_users["bob"]
    accept_friendship(alice, bob)
    fixed_now = datetime(2026, 9, 13, 12, 0, tzinfo=dt_timezone.utc)
    with patch("social.services.timezone.now", return_value=fixed_now):
        boundary_message = SocialMessage.objects.create(
            sender=alice,
            receiver=bob,
            work=message_work,
            message="Boundary",
        )
        SocialMessage.objects.filter(pk=boundary_message.pk).update(
            created_at=fixed_now - timedelta(days=7)
        )
        boundary = client_for(alice).post(
            "/api/social/recommendations/",
            {"recipient_alias": bob.username, "work_id": str(message_work.id)},
            format="json",
        )
    assert boundary.status_code == 201

    before = SocialMessage.objects.count()
    with patch("social.services.timezone.now", return_value=datetime(2026, 9, 13, 12, 0)):
        uncertain = client_for(alice).post(
            "/api/social/recommendations/",
            {"recipient_alias": bob.username, "work_id": str(message_work.id)},
            format="json",
        )
    assert uncertain.status_code == 429
    assert uncertain["Retry-After"] == str(services.CONSERVATIVE_RETRY_AFTER)
    assert SocialMessage.objects.count() == before
