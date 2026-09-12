"""Tests for the per-work comment tracer (Plan 05-02 Task 1, LIB-03/D-04/D-05).

One comment per user/work: the author has full CRUD over their own row,
visibility (public/private) is resolved server-side, and a work outside the
caller's own collection is rejected without any mutation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogue.models import GameWork
from library.models import GameComment, LibraryEntry

User = get_user_model()

HOSTILE_FIXTURES_PATH = Path(__file__).resolve().parents[4] / "e2e" / "fixtures" / "hostile.json"


@pytest.fixture
def work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="comment-game", original_title="Comment Game")


@pytest.fixture
def other_work(db):  # noqa: ANN001
    return GameWork.objects.create(canonical_slug="other-comment-game", original_title="Other Comment Game")


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="comment-user-a", password="Comment-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="comment-user-b", password="Comment-User-B-Pass-9!")


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _collect(user, work) -> None:  # noqa: ANN001
    LibraryEntry.objects.get_or_create(user=user, work=work, defaults={"current_status": None})


# ---------------------------------------------------------------------------
# Test 1: create/read/edit/delete flow; a second create returns conflict.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_owner_can_create_read_edit_and_delete_their_own_comment(work, user_a) -> None:  # noqa: ANN001
    _collect(user_a, work)
    client = _client_for(user_a)

    created = client.post(
        f"/api/library/entries/{work.id}/comments/",
        {"text": "Great game.", "visibility": "public"},
        format="json",
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]
    assert created.json()["text"] == "Great game."
    assert created.json()["is_own"] is True

    read = client.get(f"/api/library/comments/{comment_id}/")
    assert read.status_code == 200
    assert read.json()["text"] == "Great game."

    edited = client.patch(
        f"/api/library/comments/{comment_id}/", {"text": "Actually, even better."}, format="json"
    )
    assert edited.status_code == 200
    assert edited.json()["text"] == "Actually, even better."
    assert GameComment.objects.get(id=comment_id).text == "Actually, even better."

    deleted = client.delete(f"/api/library/comments/{comment_id}/")
    assert deleted.status_code == 204
    assert not GameComment.objects.filter(id=comment_id).exists()


@pytest.mark.django_db
def test_second_comment_for_the_same_work_returns_conflict_without_duplicating(work, user_a) -> None:  # noqa: ANN001
    _collect(user_a, work)
    client = _client_for(user_a)
    client.post(f"/api/library/entries/{work.id}/comments/", {"text": "First.", "visibility": "public"}, format="json")

    second = client.post(
        f"/api/library/entries/{work.id}/comments/", {"text": "Second.", "visibility": "public"}, format="json"
    )
    assert second.status_code == 409
    assert GameComment.objects.filter(user=user_a, work=work).count() == 1
    assert GameComment.objects.get(user=user_a, work=work).text == "First."


# ---------------------------------------------------------------------------
# Test 2: work outside LibraryEntry rejected without mutation; user B cannot
# read/edit/delete A's comment via the by-id endpoint.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_work_outside_collection_is_rejected_without_mutation(other_work, user_a) -> None:  # noqa: ANN001
    client = _client_for(user_a)
    response = client.post(
        f"/api/library/entries/{other_work.id}/comments/", {"text": "Not collected.", "visibility": "public"}, format="json"
    )
    assert response.status_code == 400
    assert not GameComment.objects.filter(user=user_a, work=other_work).exists()


@pytest.mark.django_db
def test_user_b_cannot_read_edit_or_delete_user_a_comment(work, user_a, user_b) -> None:  # noqa: ANN001
    _collect(user_a, work)
    comment = GameComment.objects.create(user=user_a, work=work, text="A's comment.", visibility="private")
    client_b = _client_for(user_b)

    read = client_b.get(f"/api/library/comments/{comment.id}/")
    assert read.status_code == 404

    edited = client_b.patch(f"/api/library/comments/{comment.id}/", {"text": "Hijacked."}, format="json")
    assert edited.status_code == 404

    deleted = client_b.delete(f"/api/library/comments/{comment.id}/")
    assert deleted.status_code == 404

    comment.refresh_from_db()
    assert comment.text == "A's comment."


@pytest.mark.django_db
def test_unauthenticated_create_is_rejected(work) -> None:  # noqa: ANN001
    response = APIClient().post(
        f"/api/library/entries/{work.id}/comments/", {"text": "Anon.", "visibility": "public"}, format="json"
    )
    assert response.status_code in (401, 403)
    assert not GameComment.objects.filter(work=work).exists()


# ---------------------------------------------------------------------------
# Test 3: author keeps access to their own private comment; third parties
# only receive public comments; hostile text is inert.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_author_sees_own_private_comment_via_the_by_work_listing(work, user_a) -> None:  # noqa: ANN001
    _collect(user_a, work)
    GameComment.objects.create(user=user_a, work=work, text="Private thoughts.", visibility="private")

    client = _client_for(user_a)
    response = client.get(f"/api/library/entries/{work.id}/comments/")
    assert response.status_code == 200
    comments = response.json()["comments"]
    assert len(comments) == 1
    assert comments[0]["text"] == "Private thoughts."
    assert comments[0]["is_own"] is True


@pytest.mark.django_db
def test_third_parties_only_receive_public_comments(work, user_a, user_b) -> None:  # noqa: ANN001
    _collect(user_a, work)
    _collect(user_b, work)
    GameComment.objects.create(user=user_a, work=work, text="Private A.", visibility="private")
    GameComment.objects.create(user=user_b, work=work, text="Public B.", visibility="public")

    anonymous_response = APIClient().get(f"/api/library/entries/{work.id}/comments/")
    anonymous_texts = {c["text"] for c in anonymous_response.json()["comments"]}
    assert anonymous_texts == {"Public B."}

    # B is a third party relative to A's private comment -- B's own comment
    # is already public, so B sees the same public-only set as anonymous.
    b_response = _client_for(user_b).get(f"/api/library/entries/{work.id}/comments/")
    b_texts = {c["text"] for c in b_response.json()["comments"]}
    assert b_texts == {"Public B."}

    # A, as the author, still sees their own private comment plus B's public one.
    a_response = _client_for(user_a).get(f"/api/library/entries/{work.id}/comments/")
    a_texts = {c["text"] for c in a_response.json()["comments"]}
    assert a_texts == {"Private A.", "Public B."}


@pytest.mark.django_db
def test_hostile_comment_text_is_returned_as_inert_text(work, user_a) -> None:  # noqa: ANN001
    payloads = json.loads(HOSTILE_FIXTURES_PATH.read_text(encoding="utf-8"))["untrustedText"]
    hostile_text = payloads[0]
    _collect(user_a, work)
    client = _client_for(user_a)

    created = client.post(
        f"/api/library/entries/{work.id}/comments/", {"text": hostile_text, "visibility": "public"}, format="json"
    )
    assert created.status_code == 201
    assert created.json()["text"] == hostile_text
    assert isinstance(created.json()["text"], str)

    listed = APIClient().get(f"/api/library/entries/{work.id}/comments/").json()["comments"]
    assert listed[0]["text"] == hostile_text
