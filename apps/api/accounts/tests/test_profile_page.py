"""Tests for the profile page backend: display name, built-in avatar, uploaded
photo and cover, default list visibility, password change and self-service
account deletion."""

from __future__ import annotations

import struct
import zlib

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import AccountProfile
from catalogue.models import GameWork
from library.models import CustomList, GameComment, LibraryEntry

User = get_user_model()

PASSWORD = "Zeph-Corridor-4471-Loft!"  # noqa: S105 - test fixture, not a real credential
NEW_PASSWORD = "Vantage-Kestrel-8823-Moor!"  # noqa: S105 - test fixture, not a real credential


@pytest.fixture(autouse=True)
def _isolate_throttle_state() -> None:
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def owner(db):  # noqa: ANN001
    return User.objects.create_user(username="page-owner", password=PASSWORD)


@pytest.fixture
def client(owner) -> APIClient:  # noqa: ANN001
    api = APIClient()
    api.force_authenticate(owner)
    return api


def _png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + chunk(b"IEND", b"")
    )


@pytest.mark.django_db
def test_profile_read_includes_page_fields_and_summary(client, owner) -> None:  # noqa: ANN001
    work = GameWork.objects.create(canonical_slug="g1", original_title="G1")
    LibraryEntry.objects.create(user=owner, work=work, current_status="completed")
    body = client.get("/api/accounts/me/profile/").json()
    assert body["alias"] == "page-owner"
    assert body["display_name"] == ""
    assert body["avatar_preset"] is None
    assert body["avatar_image_url"] == ""
    assert body["cover_image_url"] == ""
    assert body["summary"] == {"games": 1, "completed": 1, "playing": 0, "lists": 0, "friends": 0}
    assert body["member_since"]


@pytest.mark.django_db
def test_patch_updates_display_name_preset_and_default_list_visibility(client, owner) -> None:  # noqa: ANN001
    response = client.patch(
        "/api/accounts/me/profile/",
        {"display_name": "  Alex  ", "avatar_preset": 3, "default_list_visibility": "private"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Alex"
    assert response.json()["avatar_preset"] == 3
    assert AccountProfile.objects.get(user=owner).default_list_visibility == "private"

    cleared = client.patch("/api/accounts/me/profile/", {"avatar_preset": None}, format="json")
    assert cleared.json()["avatar_preset"] is None


@pytest.mark.django_db
def test_invalid_preset_and_long_display_name_are_rejected(client) -> None:  # noqa: ANN001
    assert client.patch("/api/accounts/me/profile/", {"avatar_preset": 9}, format="json").status_code == 400
    assert client.patch("/api/accounts/me/profile/", {"display_name": "x" * 41}, format="json").status_code == 400


@pytest.mark.django_db
def test_new_lists_use_the_default_list_visibility(client, owner) -> None:  # noqa: ANN001
    client.patch("/api/accounts/me/profile/", {"default_list_visibility": "private"}, format="json")
    response = client.post("/api/library/lists/", {"name": "Backlog"}, format="json")
    assert response.status_code == 201
    assert CustomList.objects.get(user=owner, name="Backlog").visibility == "private"


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["avatar", "cover"])
def test_image_upload_roundtrip_is_owner_only(client, owner, kind) -> None:  # noqa: ANN001
    upload = SimpleUploadedFile("pic.png", _png(), content_type="image/png")
    response = client.put(f"/api/accounts/me/{kind}/", {"file": upload}, format="multipart")
    assert response.status_code == 200
    assert response.json()[f"{kind}_image_url"].startswith(f"/api/accounts/me/{kind}/?v=")

    fetched = client.get(f"/api/accounts/me/{kind}/")
    assert fetched.status_code == 200
    assert fetched["Content-Type"] == "image/png"
    assert fetched.content == _png()

    anonymous = APIClient().get(f"/api/accounts/me/{kind}/")
    assert anonymous.status_code in (401, 403)

    cleared = client.delete(f"/api/accounts/me/{kind}/")
    assert cleared.json()[f"{kind}_image_url"] == ""
    assert client.get(f"/api/accounts/me/{kind}/").status_code == 404


@pytest.mark.django_db
def test_upload_rejects_non_images_and_oversized_files(client) -> None:  # noqa: ANN001
    html = SimpleUploadedFile("pic.png", b"<script>alert(1)</script>", content_type="image/png")
    assert client.put("/api/accounts/me/avatar/", {"file": html}, format="multipart").status_code == 400
    big = SimpleUploadedFile("pic.png", _png() + b"0" * (512 * 1024), content_type="image/png")
    assert client.put("/api/accounts/me/avatar/", {"file": big}, format="multipart").status_code == 400
    assert client.put("/api/accounts/me/avatar/", {}, format="multipart").status_code == 400


@pytest.mark.django_db
def test_password_change_requires_the_current_password(client, owner) -> None:  # noqa: ANN001
    wrong = client.post(
        "/api/accounts/me/password/", {"current_password": "nope", "new_password": NEW_PASSWORD}, format="json"
    )
    assert wrong.status_code == 400

    weak = client.post(
        "/api/accounts/me/password/", {"current_password": PASSWORD, "new_password": "12345678"}, format="json"
    )
    assert weak.status_code == 400

    ok = client.post(
        "/api/accounts/me/password/", {"current_password": PASSWORD, "new_password": NEW_PASSWORD}, format="json"
    )
    assert ok.status_code == 200
    owner.refresh_from_db()
    assert owner.check_password(NEW_PASSWORD)


@pytest.mark.django_db
def test_account_deletion_removes_the_account_and_its_data(client, owner) -> None:  # noqa: ANN001
    work = GameWork.objects.create(canonical_slug="g2", original_title="G2")
    LibraryEntry.objects.create(user=owner, work=work, current_status="playing")
    GameComment.objects.create(user=owner, work=work, text="hi", visibility="public")
    CustomList.objects.create(user=owner, name="L")
    client.patch("/api/accounts/me/profile/", {"display_name": "Alex"}, format="json")

    wrong = client.post("/api/accounts/me/delete/", {"password": "nope"}, format="json")
    assert wrong.status_code == 400
    assert User.objects.filter(pk=owner.pk).exists()

    response = client.post("/api/accounts/me/delete/", {"password": PASSWORD}, format="json")
    assert response.status_code == 204
    assert not User.objects.filter(username="page-owner").exists()
    assert not LibraryEntry.objects.filter(work=work).exists()
    assert not GameComment.objects.filter(work=work).exists()


@pytest.mark.django_db
def test_bulk_queryset_deletion_does_not_leave_dangling_recommendation_state(owner) -> None:  # noqa: ANN001
    from recommendations.models import RecommendationState

    work = GameWork.objects.create(canonical_slug="g3", original_title="G3")
    LibraryEntry.objects.create(user=owner, work=work, current_status="playing")
    User.objects.filter(pk=owner.pk).delete()
    assert not RecommendationState.objects.filter(user_id=owner.pk).exists()


@pytest.mark.django_db
def test_username_availability_reports_each_case(client, owner) -> None:  # noqa: ANN001
    User.objects.create_user(username="Taken-Name", password=PASSWORD)

    def status(name: str) -> str:
        return client.get("/api/accounts/me/username/availability/", {"username": name}).json()["status"]

    assert status("brand-new") == "ok"
    assert status("page-owner") == "same"
    assert status("taken-name") == "taken"  # compared case-insensitively
    assert status("ab") == "invalid"
    assert status("has space") == "invalid"
    assert status("anonymous-abc") == "invalid"


@pytest.mark.django_db
def test_username_can_be_changed_only_once(client, owner) -> None:  # noqa: ANN001
    first = client.post("/api/accounts/me/username/", {"username": "fresh-alias"}, format="json")
    assert first.status_code == 200
    assert first.json()["alias"] == "fresh-alias"
    assert first.json()["username_changed"] is True
    owner.refresh_from_db()
    assert owner.username == "fresh-alias"

    second = client.post("/api/accounts/me/username/", {"username": "another-alias"}, format="json")
    assert second.status_code == 409
    assert second.json()["code"] == "already_changed"
    owner.refresh_from_db()
    assert owner.username == "fresh-alias"


@pytest.mark.django_db
def test_username_change_rejects_taken_and_invalid_names_without_using_the_one_change(client, owner) -> None:  # noqa: ANN001
    User.objects.create_user(username="someone-else", password=PASSWORD)
    taken = client.post("/api/accounts/me/username/", {"username": "SOMEONE-ELSE"}, format="json")
    assert taken.status_code == 409
    assert taken.json()["code"] == "taken"
    invalid = client.post("/api/accounts/me/username/", {"username": "no spaces!"}, format="json")
    assert invalid.status_code == 400

    # The failed attempts did not consume the single allowed change.
    ok = client.post("/api/accounts/me/username/", {"username": "good-name"}, format="json")
    assert ok.status_code == 200
