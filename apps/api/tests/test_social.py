from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

import pytest

from social.models import Friendship, FriendshipRequest


User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def users(db):
    return {
        "alice": User.objects.create_user(username="Alice", password="test-password-1"),
        "bob": User.objects.create_user(username="Bob", password="test-password-2"),
        "felipe": User.objects.create_user(username="Felipe", password="test-password-3"),
        "felipe_two": User.objects.create_user(username="FelipeTwo", password="test-password-4"),
    }


@pytest.mark.django_db
def test_exact_alias_search_does_not_return_partial_matches(api_client, users):
    api_client.force_authenticate(users["alice"])

    response = api_client.get(reverse("social:search"), {"alias": "Felipe"})
    partial_response = api_client.get(reverse("social:search"), {"alias": "fel"})

    assert response.status_code == 200
    assert [row["alias"] for row in response.json()["results"]] == ["Felipe"]
    assert partial_response.status_code == 200
    assert partial_response.json()["results"] == []


@pytest.mark.django_db
def test_request_and_accept_create_bidirectional_friendship(api_client, users):
    api_client.force_authenticate(users["alice"])
    request_response = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")

    assert request_response.status_code == 201
    request_id = request_response.json()["request"]["id"]
    assert request_response.json()["request"]["sender_alias"] == "Alice"
    assert request_response.json()["request"]["receiver_alias"] == "Bob"

    api_client.force_authenticate(users["bob"])
    accept_response = api_client.post(reverse("social:request-action", args=[request_id, "accept"]))

    assert accept_response.status_code == 200
    assert accept_response.json()["relationship"] == "friend"
    assert Friendship.objects.filter(pair__low_user__in=[users["alice"], users["bob"]]).exists()
    assert FriendshipRequest.objects.filter(id=request_id, status="accepted").exists()

    api_client.force_authenticate(users["alice"])
    alice_status = api_client.get(reverse("social:relationship", args=["Bob"]))
    api_client.force_authenticate(users["bob"])
    bob_status = api_client.get(reverse("social:relationship", args=["Alice"]))

    assert alice_status.json()["relationship"] == "friend"
    assert bob_status.json()["relationship"] == "friend"


@pytest.mark.django_db
def test_invalid_social_request_does_not_mutate_data(api_client, users):
    response = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")
    assert response.status_code == 401
    assert FriendshipRequest.objects.count() == 0

    users["bob"].is_active = False
    users["bob"].save(update_fields=["is_active"])
    api_client.force_authenticate(users["alice"])
    inactive_response = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")
    assert inactive_response.status_code == 404
    assert FriendshipRequest.objects.count() == 0

    self_response = api_client.post(reverse("social:requests"), {"alias": "Alice"}, format="json")
    assert self_response.status_code == 400
    assert FriendshipRequest.objects.count() == 0

