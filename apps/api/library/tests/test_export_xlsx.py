"""Tests for the owner-scoped spreadsheet export of the collection."""

from __future__ import annotations

import io
import re
import zipfile
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalogue.models import (
    CuratedLabel,
    Developer,
    GameRelease,
    GameWork,
    GameWorkCuratedLabel,
    Platform,
    RelatedContent,
)
from library.export_xlsx import COLUMNS, collection_rows
from library.models import LibraryEntry, OwnedCopy

User = get_user_model()
URL = "/api/library/export/collection.xlsx"


@pytest.fixture
def owner(db):  # noqa: ANN001
    return User.objects.create_user(username="xlsx-owner", password="Xlsx-Owner-Pass-9!")


@pytest.fixture
def other(db):  # noqa: ANN001
    return User.objects.create_user(username="xlsx-other", password="Xlsx-Other-Pass-9!")


def _client(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _full_work() -> GameWork:
    work = GameWork.objects.create(
        canonical_slug="xlsx-game",
        original_title="Xlsx Game",
        first_release_date=date(2011, 5, 20),
        total_rating=87.46,
    )
    platform = Platform.objects.create(name="PC", slug="pc")
    GameRelease.objects.create(work=work, platform=platform, release_name="Xlsx Game")
    work.developers.add(Developer.objects.create(igdb_id=9001, name="Studio Uno", slug="studio-uno"))
    label = CuratedLabel.objects.create(name="Role-playing", slug="rpg", kind="genre", curation_version="t")
    GameWorkCuratedLabel.objects.create(work=work, label=label, source_kind="genre", source_value="rpg")
    dlc = GameWork.objects.create(canonical_slug="xlsx-dlc", original_title="Xlsx Game: Extra", is_dlc=True)
    RelatedContent.objects.create(parent_work=work, child_work=dlc, relation="dlc")
    return work


def test_rows_follow_the_requested_columns(owner) -> None:  # noqa: ANN001
    work = _full_work()
    LibraryEntry.objects.create(
        user=owner, work=work, current_status="completed", rating_half_steps=9, is_platinum=True
    )
    OwnedCopy.objects.create(user=owner, work=work, release=work.releases.first(), format="physical", idempotency_key="k1")

    assert COLUMNS == (
        "Juego", "Estado", "Rating IGDB", "Rating usuario", "Copia", "Año",
        "Plataforma", "Desarrollador", "Género", "Platino", "DLC",
    )
    assert collection_rows(owner) == [
        ["Xlsx Game", "Completado", 87.5, 4.5, "Sí", 2011, "PC", "Studio Uno", "RPG", "Sí", "Xlsx Game: Extra"]
    ]


def test_english_sheet_uses_english_headers_labels_and_names(owner) -> None:  # noqa: ANN001
    work = _full_work()
    work.title_es = "Juego Xlsx"
    work.title_en = "Xlsx Game"
    work.save()
    LibraryEntry.objects.create(user=owner, work=work, current_status="completed", rating_half_steps=9, is_platinum=True)

    assert collection_rows(owner, "en") == [
        ["Xlsx Game", "Completed", 87.5, 4.5, "No", 2011, "PC", "Studio Uno", "Role-playing", "Yes", "Xlsx Game: Extra"]
    ]
    assert collection_rows(owner, "es")[0][0] == "Juego Xlsx"
    response = _client(owner).get(URL + "?lang=en")
    assert "savepoint-collection.xlsx" in response["Content-Disposition"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        workbook = archive.read("xl/workbook.xml").decode("utf-8")
    assert "IGDB rating" in sheet and "Rating IGDB" not in sheet
    assert 'name="Collection"' in workbook


def test_unrated_game_without_copy_has_empty_ratings_and_no(owner) -> None:  # noqa: ANN001
    work = GameWork.objects.create(canonical_slug="bare", original_title="Bare")
    LibraryEntry.objects.create(user=owner, work=work, current_status="pending")
    assert collection_rows(owner) == [["Bare", "Pendiente", None, None, "No", None, "", "", "", "No", ""]]


def test_download_is_a_valid_workbook_scoped_to_the_caller(owner, other) -> None:  # noqa: ANN001
    LibraryEntry.objects.create(user=owner, work=GameWork.objects.create(canonical_slug="mine", original_title="Mine"))
    LibraryEntry.objects.create(user=other, work=GameWork.objects.create(canonical_slug="theirs", original_title="Theirs"))

    response = _client(owner).get(URL)

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert "savepoint-coleccion.xlsx" in response["Content-Disposition"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    texts = re.findall(r"<t xml:space=\"preserve\">([^<]*)</t>", sheet)
    assert "Mine" in texts
    assert "Theirs" not in texts
    for column in COLUMNS:
        assert column in texts


def test_export_requires_authentication(db) -> None:  # noqa: ANN001
    assert APIClient().get(URL).status_code in (401, 403)
