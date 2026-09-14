"""CSV import preview/apply contract (PORT-02/PORT-03)."""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from catalogue.models import GameRelease, GameWork, Platform
from library.models import OwnedCopy

User = get_user_model()
IMPORT_URL = "/api/library/import/preview/"
APPLY_URL = "/api/library/import/apply/"


def _csv(*, slug: str, record_type: str = "copy", store: str = "Local shop") -> bytes:
    from library.export import CSV_FIELDNAMES, CSV_SCHEMA_VERSION

    row = dict.fromkeys(CSV_FIELDNAMES, "")
    row.update(
        {
            "schema_version": str(CSV_SCHEMA_VERSION),
            "record_type": record_type,
            "work_slug": slug,
            "work_title": "ignored export title",
            "copy_format": "physical" if record_type == "copy" else "",
            "purchase_date": "2026-09-14" if record_type == "copy" else "",
            "price": "19.99" if record_type == "copy" else "",
            "currency": "EUR" if record_type == "copy" else "",
            "store": store if record_type == "copy" else "",
            "conservation_state": "good" if record_type == "copy" else "",
            "storage_location": "Shelf A" if record_type == "copy" else "",
            "status": "completed" if record_type == "collection" else "",
            "rating_half_steps": "9" if record_type == "collection" else "",
        }
    )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDNAMES)
    writer.writeheader()
    writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _upload(raw: bytes) -> SimpleUploadedFile:
    return SimpleUploadedFile("collection.csv", raw, content_type="text/csv")


@pytest.fixture
def game_data():
    user = User.objects.create_user(username="import-owner", password="Import-password-123!")
    other = User.objects.create_user(username="other-owner", password="Other-password-123!")
    work = GameWork.objects.create(canonical_slug="importable-game", original_title="Importable Game")
    release = GameRelease.objects.create(work=work, release_name="Importable Game", release_date=date(2020, 1, 1))
    Platform.objects.create(name="PC", slug="import-pc")
    return user, other, work, release


@pytest.mark.django_db
def test_preview_is_digest_bound_and_does_not_mutate(game_data):
    user, _, work, _ = game_data
    raw = _csv(slug=work.canonical_slug)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(IMPORT_URL, {"file": _upload(raw)}, format="multipart")
    assert response.status_code == 200
    body = response.json()
    assert body["can_apply"] is True
    assert body["preview_sha256"] == hashlib.sha256(raw).hexdigest()
    assert body["will_create"] == 1
    assert not OwnedCopy.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_apply_creates_only_for_authenticated_owner_and_replay_is_idempotent(game_data):
    user, other, work, _ = game_data
    raw = _csv(slug=work.canonical_slug)
    digest = hashlib.sha256(raw).hexdigest()
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(APPLY_URL, {"file": _upload(raw), "preview_sha256": digest}, format="multipart")
    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert OwnedCopy.objects.filter(user=user).count() == 1
    assert OwnedCopy.objects.filter(user=other).count() == 0

    replay = client.post(APPLY_URL, {"file": _upload(raw), "preview_sha256": digest}, format="multipart")
    assert replay.status_code == 200
    assert replay.json()["created"] == 0
    assert replay.json()["unchanged"] == 1
    assert OwnedCopy.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_conflicting_replay_is_rejected_without_partial_write(game_data):
    user, _, work, _ = game_data
    original = _csv(slug=work.canonical_slug, store="Original")
    client = APIClient()
    client.force_authenticate(user=user)
    preview = client.post(IMPORT_URL, {"file": _upload(original)}, format="multipart").json()
    assert client.post(
        APPLY_URL,
        {"file": _upload(original), "preview_sha256": preview["preview_sha256"]},
        format="multipart",
    ).status_code == 200

    changed = _csv(slug=work.canonical_slug, store="Changed")
    changed_preview = client.post(IMPORT_URL, {"file": _upload(changed)}, format="multipart").json()
    assert changed_preview["conflicts"] == 1
    response = client.post(
        APPLY_URL,
        {"file": _upload(changed), "preview_sha256": changed_preview["preview_sha256"]},
        format="multipart",
    )
    assert response.status_code == 400
    assert response.json()["can_apply"] is False
    assert list(OwnedCopy.objects.filter(user=user).values_list("store", flat=True)) == ["Original"]
