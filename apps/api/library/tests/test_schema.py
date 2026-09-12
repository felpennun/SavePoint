"""Schema/migration introspection tests for rating + copies (Plan 01-07 Task 1)."""

from __future__ import annotations

import importlib

import pytest
from django.apps import apps
from django.db import connection


def test_rating_copies_migration_depends_on_catalogue_hierarchy() -> None:
    module = importlib.import_module("library.migrations.0002_rating_copies")
    dependency_apps = {dep[0] for dep in module.Migration.dependencies}
    assert "catalogue" in dependency_apps
    catalogue_deps = [dep[1] for dep in module.Migration.dependencies if dep[0] == "catalogue"]
    assert "0002_catalogue_hierarchy" in catalogue_deps


@pytest.mark.django_db
def test_owned_copy_table_has_expected_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'library_ownedcopy'
            """
        )
        columns = {row[0] for row in cursor.fetchall()}

    assert {"id", "user_id", "work_id", "release_id", "edition_id", "format", "idempotency_key", "created_at"} <= columns


@pytest.mark.django_db
def test_owned_copy_unique_idempotency_constraint_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname = 'library_unique_copy_idempotency_per_user'"
        )
        assert cursor.fetchone() is not None


@pytest.mark.django_db
def test_library_entry_rating_range_check_constraint_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT conname FROM pg_constraint WHERE conname = 'library_rating_half_steps_range'")
        assert cursor.fetchone() is not None


def test_owned_copy_foreign_keys_are_protective_or_cascade() -> None:
    owned_copy_model = apps.get_model("library", "OwnedCopy")
    for field_name in ("user", "work", "release", "edition"):
        field = owned_copy_model._meta.get_field(field_name)
        assert field.remote_field.on_delete.__name__ in ("PROTECT", "CASCADE")


def test_library_entry_has_rating_field() -> None:
    library_entry_model = apps.get_model("library", "LibraryEntry")
    field = library_entry_model._meta.get_field("rating_half_steps")
    assert field.null is True


# ---------------------------------------------------------------------------
# Plan 05-02 Task 3: GameComment/CustomList/CustomListItem schema/constraints
# (LIB-03/LIB-04). The migration must already be applied (docker compose
# `migrate --noinput` per the plan's [BLOCKING] gate) before these run.
# ---------------------------------------------------------------------------


def test_phase5_comments_lists_migration_depends_on_expected_apps() -> None:
    module = importlib.import_module("library.migrations.0003_phase5_comments_lists")
    dependency_apps = {dep[0] for dep in module.Migration.dependencies}
    assert "catalogue" in dependency_apps
    assert "library" in dependency_apps
    library_deps = [dep[1] for dep in module.Migration.dependencies if dep[0] == "library"]
    assert "0002_rating_copies" in library_deps


@pytest.mark.django_db
def test_game_comment_table_has_expected_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'library_gamecomment'")
        columns = {row[0] for row in cursor.fetchall()}
    assert {"id", "user_id", "work_id", "text", "visibility", "created_at", "updated_at"} <= columns


@pytest.mark.django_db
def test_game_comment_constraints_are_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname IN "
            "('library_unique_comment_per_user_work', 'library_comment_visibility_valid')"
        )
        found = {row[0] for row in cursor.fetchall()}
    assert found == {"library_unique_comment_per_user_work", "library_comment_visibility_valid"}


def test_game_comment_foreign_keys_are_protective_or_cascade() -> None:
    comment_model = apps.get_model("library", "GameComment")
    for field_name in ("user", "work"):
        field = comment_model._meta.get_field(field_name)
        assert field.remote_field.on_delete.__name__ in ("PROTECT", "CASCADE")


@pytest.mark.django_db
def test_custom_list_table_has_expected_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'library_customlist'")
        columns = {row[0] for row in cursor.fetchall()}
    assert {"id", "user_id", "name", "visibility", "version", "created_at", "updated_at"} <= columns


@pytest.mark.django_db
def test_custom_list_visibility_constraint_is_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT conname FROM pg_constraint WHERE conname = 'library_list_visibility_valid'")
        assert cursor.fetchone() is not None


@pytest.mark.django_db
def test_custom_list_item_table_has_expected_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'library_customlistitem'")
        columns = {row[0] for row in cursor.fetchall()}
    assert {"id", "list_id", "work_id", "position", "created_at"} <= columns


@pytest.mark.django_db
def test_custom_list_item_constraints_are_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname IN "
            "('library_unique_list_item_work', 'library_unique_list_item_position')"
        )
        found = {row[0] for row in cursor.fetchall()}
    assert found == {"library_unique_list_item_work", "library_unique_list_item_position"}


def test_custom_list_item_foreign_keys_are_protective_or_cascade() -> None:
    item_model = apps.get_model("library", "CustomListItem")
    for field_name, expected in (("list", "CASCADE"), ("work", "PROTECT")):
        field = item_model._meta.get_field(field_name)
        assert field.remote_field.on_delete.__name__ == expected


def test_custom_list_has_a_default_version_of_one() -> None:
    custom_list_model = apps.get_model("library", "CustomList")
    field = custom_list_model._meta.get_field("version")
    assert field.default == 1


# ---------------------------------------------------------------------------
# Plan 05-03 Task 2: OwnedCopy purchase/conservation metadata schema and
# constraints (INV-03/INV-04). The migration must already be applied
# (docker compose `migrate --noinput` per the plan's [BLOCKING] gate) before
# these run.
# ---------------------------------------------------------------------------


def test_phase5_copy_metadata_migration_depends_on_comments_lists_migration() -> None:
    module = importlib.import_module("library.migrations.0004_phase5_copy_metadata")
    library_deps = [dep[1] for dep in module.Migration.dependencies if dep[0] == "library"]
    assert "0003_phase5_comments_lists" in library_deps


@pytest.mark.django_db
def test_owned_copy_table_has_metadata_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'library_ownedcopy'")
        columns = {row[0] for row in cursor.fetchall()}
    assert {
        "purchase_date",
        "price",
        "currency",
        "store",
        "conservation_state",
        "storage_location",
    } <= columns


@pytest.mark.django_db
def test_owned_copy_metadata_constraints_are_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname IN ("
            "'library_copy_price_non_negative', "
            "'library_copy_currency_format_valid', "
            "'library_copy_conservation_state_valid', "
            "'library_copy_digital_excludes_conservation')"
        )
        found = {row[0] for row in cursor.fetchall()}
    assert found == {
        "library_copy_price_non_negative",
        "library_copy_currency_format_valid",
        "library_copy_conservation_state_valid",
        "library_copy_digital_excludes_conservation",
    }


def test_owned_copy_conservation_fields_are_nullable() -> None:
    owned_copy_model = apps.get_model("library", "OwnedCopy")
    for field_name in ("purchase_date", "price", "currency", "store", "conservation_state", "storage_location"):
        field = owned_copy_model._meta.get_field(field_name)
        assert field.null is True
