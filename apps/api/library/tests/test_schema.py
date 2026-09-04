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
