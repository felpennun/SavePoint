from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.urls import reverse
from rest_framework.test import APIClient

import pytest

from social import services
from social.models import Block, Friendship, FriendshipRequest, RelationshipPair


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


def establish_friendship(api_client, users):
    api_client.force_authenticate(users["alice"])
    request_response = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")
    request_id = request_response.json()["request"]["id"]
    api_client.force_authenticate(users["bob"])
    assert api_client.post(reverse("social:request-accept", args=[request_id])).status_code == 200


@pytest.mark.django_db
def test_exact_alias_search_does_not_return_partial_matches(api_client, users):
    api_client.force_authenticate(users["alice"])

    response = api_client.get(reverse("social:search"), {"alias": "Felipe"})
    partial_response = api_client.get(reverse("social:search"), {"alias": "fel"})

    assert response.status_code == 200
    assert [row["alias"] for row in response.json()["results"]] == ["Felipe"]
    assert partial_response.status_code == 200
    assert partial_response.json()["results"] == []

    repeated = api_client.get(
        reverse("social:search"), [("alias", "Felipe"), ("alias", "FelipeTwo")]
    )
    extra = api_client.get(reverse("social:search"), {"alias": "Felipe", "owner_id": "2"})
    assert repeated.status_code == 400
    assert extra.status_code == 400


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
    assert response.status_code in {401, 403}
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


@pytest.mark.django_db
def test_reject_and_remove_are_distinct_and_allow_a_future_request(api_client, users):
    api_client.force_authenticate(users["alice"])
    first = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")
    first_id = first.json()["request"]["id"]
    api_client.force_authenticate(users["bob"])
    assert api_client.post(reverse("social:request-reject", args=[first_id])).status_code == 200

    api_client.force_authenticate(users["alice"])
    second = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")
    assert second.status_code == 201
    api_client.force_authenticate(users["bob"])
    assert api_client.post(reverse("social:request-accept", args=[second.json()["request"]["id"]])).status_code == 200
    api_client.force_authenticate(users["alice"])
    assert api_client.post(reverse("social:friendship-remove", args=["Bob"])).status_code == 200
    assert api_client.get(reverse("social:relationship", args=["Bob"])).json()["relationship"] == "none"
    assert api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json").status_code == 201


@pytest.mark.django_db
def test_block_cancels_requests_removes_friendship_and_hides_both_directions(api_client, users):
    establish_friendship(api_client, users)
    api_client.force_authenticate(users["alice"])
    response = api_client.post(reverse("social:friendship-block", args=["Bob"]))

    assert response.status_code == 200
    assert Block.objects.filter(blocker=users["alice"], blocked=users["bob"], is_active=True).exists()
    assert not Friendship.objects.filter(pair__low_user__in=[users["alice"], users["bob"]]).exists()
    assert api_client.get(reverse("social:relationship", args=["Bob"])).status_code == 404
    assert api_client.get(reverse("social:search"), {"alias": "Bob"}).json()["results"] == []

    api_client.force_authenticate(users["bob"])
    assert api_client.get(reverse("social:relationship", args=["Alice"])).status_code == 404
    assert api_client.post(reverse("social:requests"), {"alias": "Alice"}, format="json").status_code == 404


@pytest.mark.django_db
def test_unblock_revokes_only_block_and_allows_a_new_request_without_restoring_friendship(api_client, users):
    api_client.force_authenticate(users["alice"])
    assert api_client.post(reverse("social:friendship-block", args=["Bob"])).status_code == 200
    assert api_client.post(reverse("social:unblock", args=["Bob"])).status_code == 200
    assert not Block.objects.filter(blocker=users["alice"], blocked=users["bob"], is_active=True).exists()
    assert api_client.get(reverse("social:relationship", args=["Bob"])).json()["relationship"] == "none"
    request_response = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")
    assert request_response.status_code == 201
    assert not Friendship.objects.exists()


@pytest.mark.django_db
def test_duplicate_and_reverse_pending_requests_are_deterministic(api_client, users):
    api_client.force_authenticate(users["alice"])
    assert api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json").status_code == 201
    assert api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json").status_code == 409
    api_client.force_authenticate(users["bob"])
    assert api_client.post(reverse("social:requests"), {"alias": "Alice"}, format="json").status_code == 409
    assert FriendshipRequest.objects.filter(status="pending").count() == 1
    assert RelationshipPair.objects.count() == 1


@pytest.mark.django_db
def test_social_mutations_reject_client_identity_fields(api_client, users):
    api_client.force_authenticate(users["alice"])
    response = api_client.post(
        reverse("social:requests"),
        {"alias": "Bob", "sender_id": str(users["bob"].pk), "receiver_id": str(users["alice"].pk)},
        format="json",
    )

    assert response.status_code == 400
    assert FriendshipRequest.objects.count() == 0


@pytest.mark.django_db
def test_block_cancels_pending_request_and_unblock_reopens_request_path(api_client, users):
    api_client.force_authenticate(users["alice"])
    request_response = api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json")
    request_id = request_response.json()["request"]["id"]
    api_client.force_authenticate(users["bob"])
    assert api_client.post(reverse("social:friendship-block", args=["Alice"])).status_code == 200
    assert FriendshipRequest.objects.get(pk=request_id).status == "blocked"
    assert api_client.post(reverse("social:unblock", args=["Alice"])).status_code == 200
    api_client.force_authenticate(users["alice"])
    assert api_client.post(reverse("social:requests"), {"alias": "Bob"}, format="json").status_code == 201


@pytest.mark.django_db(transaction=True)
def test_concurrent_requests_create_one_pending_row(users):
    def send_request():
        close_old_connections()
        try:
            services.request_friendship(sender=users["alice"], alias="Bob")
            return "created"
        except services.SocialConflict:
            return "conflict"
        finally:
            connections.close_all()

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _item: send_request(), range(2)))
    close_old_connections()

    assert sorted(results) == ["conflict", "created"]
    assert FriendshipRequest.objects.filter(status="pending").count() == 1
