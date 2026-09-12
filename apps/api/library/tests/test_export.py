"""Tests for the owner-scoped CSV export contract (Plan 05-04 Task 1,
PORT-01/PORT-04): privacy, determinism, UTF-8, and formula-injection
neutralization."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import FavoriteSlot
from catalogue.models import GameRelease, GameWork, Platform
from library.export import CSV_FIELDNAMES, CSV_SCHEMA_VERSION, neutralize_spreadsheet_formula
from library.models import CustomList, CustomListItem, GameComment, LibraryEntry, OwnedCopy

User = get_user_model()

EXPORT_URL = "/api/library/export/collection.csv"


@pytest.fixture
def user_a(db):  # noqa: ANN001
    return User.objects.create_user(username="export-user-a", password="Export-User-A-Pass-9!")


@pytest.fixture
def user_b(db):  # noqa: ANN001
    return User.objects.create_user(username="export-user-b", password="Export-User-B-Pass-9!")


@pytest.fixture
def platform(db):  # noqa: ANN001
    return Platform.objects.create(name="PC", slug="pc")


def _client_for(user) -> APIClient:  # noqa: ANN001
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _work(slug: str, title: str) -> GameWork:
    return GameWork.objects.create(canonical_slug=slug, original_title=title)


def _collect(user, work) -> LibraryEntry:  # noqa: ANN001
    entry, _ = LibraryEntry.objects.get_or_create(user=user, work=work, defaults={"current_status": None})
    return entry


def _rows_from_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# ---------------------------------------------------------------------------
# Test 1: owner-scoped, UTF-8, versioned header; user B never appears.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_export_contains_only_the_owners_authorized_data(user_a, user_b, platform) -> None:  # noqa: ANN001
    work_a = _work("export-work-a", "Export Work A")
    work_b = _work("export-work-b", "Export Work B")
    release_a = GameRelease.objects.create(work=work_a, platform=platform, release_name="Export Work A (PC)")

    entry_a = _collect(user_a, work_a)
    entry_a.current_status = "playing"
    entry_a.rating_half_steps = 8
    entry_a.save(update_fields=["current_status", "rating_half_steps"])

    FavoriteSlot.objects.create(user=user_a, slot=1, work=work_a)
    OwnedCopy.objects.create(
        user=user_a,
        work=work_a,
        release=release_a,
        format="physical",
        idempotency_key="export-copy-a",
        price=Decimal("19.99"),
        currency="EUR",
        store="Local Store",
    )
    GameComment.objects.create(user=user_a, work=work_a, text="Great game", visibility="public")
    custom_list = CustomList.objects.create(user=user_a, name="Favorites", visibility="public")
    CustomListItem.objects.create(list=custom_list, work=work_a, position=1)

    # User B has their own, separate data for the same and a different work.
    _collect(user_b, work_a)
    entry_b_other = _collect(user_b, work_b)
    entry_b_other.current_status = "completed"
    entry_b_other.save(update_fields=["current_status"])
    GameComment.objects.create(user=user_b, work=work_a, text="User B's private opinion", visibility="private")

    response = _client_for(user_a).get(EXPORT_URL)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert "attachment" in response["Content-Disposition"]

    rows = _rows_from_csv(response.content)
    assert list(rows[0].keys()) == CSV_FIELDNAMES
    assert all(row["schema_version"] == str(CSV_SCHEMA_VERSION) for row in rows)

    record_types = {row["record_type"] for row in rows}
    assert record_types == {"favorite", "collection", "copy", "comment", "list_item"}

    text_blob = response.content.decode("utf-8")
    assert "export-work-a" in text_blob
    assert "Export Work A" in text_blob
    assert "Local Store" in text_blob
    assert "Great game" in text_blob
    # User B's data never appears: neither B's private comment text nor B's
    # separately-owned collection entry for the other work.
    assert "User B's private opinion" not in text_blob
    assert "export-work-b" not in text_blob
    assert "Export Work B" not in text_blob


@pytest.mark.django_db
def test_export_never_includes_secrets_sessions_or_unnecessary_internal_ids(user_a, platform) -> None:  # noqa: ANN001
    work_a = _work("export-secrets-work", "Export Secrets Work")
    release_a = GameRelease.objects.create(work=work_a, platform=platform, release_name="Export Secrets Work (PC)")
    _collect(user_a, work_a)
    copy = OwnedCopy.objects.create(
        user=user_a,
        work=work_a,
        release=release_a,
        format="physical",
        idempotency_key="secret-key-value",
        store="Store",
    )
    custom_list = CustomList.objects.create(user=user_a, name="My List", visibility="private")
    item = CustomListItem.objects.create(list=custom_list, work=work_a, position=1)

    response = _client_for(user_a).get(EXPORT_URL)
    text_blob = response.content.decode("utf-8")

    assert user_a.password not in text_blob
    assert "sessionid" not in text_blob.lower()
    assert "password" not in text_blob.lower()
    # Internal UUIDs (work id, copy id, list id, item id) are never written --
    # only human-facing slugs/titles/names identify a row.
    assert str(work_a.id) not in text_blob
    assert str(copy.id) not in text_blob
    assert str(custom_list.id) not in text_blob
    assert str(item.id) not in text_blob
    assert copy.idempotency_key not in text_blob


@pytest.mark.django_db
def test_anonymous_export_request_is_rejected() -> None:
    response = APIClient().get(EXPORT_URL)
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Test 2: determinism -- two unchanged exports produce identical order and
# content.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_repeated_export_without_changes_is_byte_identical(user_a, platform) -> None:  # noqa: ANN001
    work_a = _work("export-repeat-work", "Export Repeat Work")
    release_a = GameRelease.objects.create(work=work_a, platform=platform, release_name="Export Repeat Work (PC)")
    entry = _collect(user_a, work_a)
    entry.current_status = "pending"
    entry.save(update_fields=["current_status"])
    OwnedCopy.objects.create(
        user=user_a, work=work_a, release=release_a, format="digital", idempotency_key="repeat-copy"
    )
    GameComment.objects.create(user=user_a, work=work_a, text="Repeat comment", visibility="public")
    custom_list = CustomList.objects.create(user=user_a, name="Repeat List", visibility="public")
    CustomListItem.objects.create(list=custom_list, work=work_a, position=1)

    client = _client_for(user_a)
    first = client.get(EXPORT_URL).content
    second = client.get(EXPORT_URL).content

    assert first == second


# ---------------------------------------------------------------------------
# Test 3: formula-like cells are neutralized and the neutralization is
# idempotent.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("hostile_prefix", ["=", "+", "-", "@"])
def test_neutralize_spreadsheet_formula_prefixes_hostile_values(hostile_prefix: str) -> None:
    hostile_value = f"{hostile_prefix}cmd|' /C calc'!A1"
    neutralized = neutralize_spreadsheet_formula(hostile_value)
    assert neutralized == f"\t{hostile_value}"


def test_neutralize_spreadsheet_formula_is_idempotent() -> None:
    hostile_value = "=SUM(A1:A2)"
    once = neutralize_spreadsheet_formula(hostile_value)
    twice = neutralize_spreadsheet_formula(once)
    assert once == twice
    assert twice.count("\t") == 1


def test_neutralize_spreadsheet_formula_leaves_normal_text_untouched() -> None:
    assert neutralize_spreadsheet_formula("Normal Store Name") == "Normal Store Name"


@pytest.mark.django_db
def test_hostile_store_and_comment_values_are_neutralized_in_the_export(user_a, platform) -> None:  # noqa: ANN001
    work_a = _work("export-hostile-work", "Export Hostile Work")
    release_a = GameRelease.objects.create(work=work_a, platform=platform, release_name="Export Hostile Work (PC)")
    _collect(user_a, work_a)
    OwnedCopy.objects.create(
        user=user_a,
        work=work_a,
        release=release_a,
        format="physical",
        idempotency_key="hostile-copy",
        store="=cmd|' /C calc'!A1",
    )
    GameComment.objects.create(user=user_a, work=work_a, text="+SUM(A1:A9)", visibility="public")
    custom_list = CustomList.objects.create(user=user_a, name="@evil-list", visibility="public")
    CustomListItem.objects.create(list=custom_list, work=work_a, position=1)

    rows = _rows_from_csv(_client_for(user_a).get(EXPORT_URL).content)

    copy_row = next(row for row in rows if row["record_type"] == "copy")
    comment_row = next(row for row in rows if row["record_type"] == "comment")
    list_row = next(row for row in rows if row["record_type"] == "list_item")

    assert copy_row["store"] == "\t=cmd|' /C calc'!A1"
    assert comment_row["comment"] == "\t+SUM(A1:A9)"
    assert list_row["list_name"] == "\t@evil-list"

    # No cell in the raw serialized output starts with an unescaped formula
    # character right after its quoting -- every hostile cell was tab-prefixed.
    raw_text = _client_for(user_a).get(EXPORT_URL).content.decode("utf-8")
    assert "\t=cmd" in raw_text
    assert "\t+SUM" in raw_text
    assert "\t@evil-list" in raw_text


# ---------------------------------------------------------------------------
# Test 4: ties on every exported column are broken by internal, non-exported
# stable keys; repeated exports of tied data are still byte-identical.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_tied_copies_of_the_same_work_are_ordered_stably_and_repeat_identically(user_a, platform) -> None:  # noqa: ANN001
    """Two copies of the same work with identical exported metadata (same
    format/price/currency/store/conservation/location) differ only by their
    internal UUID -- the export must still produce a total order and repeat
    byte-for-byte."""
    work_a = _work("export-tie-work", "Export Tie Work")
    release_a = GameRelease.objects.create(work=work_a, platform=platform, release_name="Export Tie Work (PC)")
    _collect(user_a, work_a)
    OwnedCopy.objects.create(
        user=user_a,
        work=work_a,
        release=release_a,
        format="physical",
        idempotency_key="tie-copy-1",
        price=Decimal("9.99"),
        currency="EUR",
        store="Tied Store",
    )
    OwnedCopy.objects.create(
        user=user_a,
        work=work_a,
        release=release_a,
        format="physical",
        idempotency_key="tie-copy-2",
        price=Decimal("9.99"),
        currency="EUR",
        store="Tied Store",
    )

    client = _client_for(user_a)
    first = client.get(EXPORT_URL).content
    second = client.get(EXPORT_URL).content

    assert first == second
    copy_rows = [row for row in _rows_from_csv(first) if row["record_type"] == "copy"]
    assert len(copy_rows) == 2
    # Both rows are otherwise indistinguishable -- the tie was resolved by
    # an internal key that is never written to the CSV.
    for row in copy_rows:
        assert row["work_slug"] == "export-tie-work"
        assert row["store"] == "Tied Store"
        assert row["price"] == "9.99"


@pytest.mark.django_db
def test_tied_list_items_across_different_lists_are_ordered_stably_and_repeat_identically(
    user_a, platform  # noqa: ANN001
) -> None:
    """Two different lists sharing the same name, each holding the same
    work at the same position, produce two rows identical in every exported
    column -- differing only by the (never-exported) list/item UUIDs."""
    work_a = _work("export-tie-list-work", "Export Tie List Work")
    _collect(user_a, work_a)

    list_1 = CustomList.objects.create(user=user_a, name="Shared Name", visibility="public")
    list_2 = CustomList.objects.create(user=user_a, name="Shared Name", visibility="public")
    CustomListItem.objects.create(list=list_1, work=work_a, position=1)
    CustomListItem.objects.create(list=list_2, work=work_a, position=1)

    client = _client_for(user_a)
    first = client.get(EXPORT_URL).content
    second = client.get(EXPORT_URL).content

    assert first == second
    list_rows = [row for row in _rows_from_csv(first) if row["record_type"] == "list_item"]
    assert len(list_rows) == 2
    for row in list_rows:
        assert row["list_name"] == "Shared Name"
        assert row["work_slug"] == "export-tie-list-work"
        assert row["list_position"] == "1"
