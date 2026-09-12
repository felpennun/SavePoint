"""Schema/migration introspection tests for the Phase 5 profile/favorites
migration (Plan 05-01 Task 3, PROF-01/PRIV-01).

Locks the PostgreSQL contract behind the endpoints in test_profile.py /
test_public_profile.py: the migration chain, its constraints and its
foreign-key semantics must actually exist in the database, not just appear
to work through the ORM.
"""

from __future__ import annotations

import importlib

import pytest
from django.apps import apps
from django.db import connection


def test_phase5_profile_migration_depends_on_demo_accounts_and_catalogue() -> None:
    module = importlib.import_module("accounts.migrations.0003_phase5_profile")
    dependency_apps = {dep[0] for dep in module.Migration.dependencies}
    assert "accounts" in dependency_apps
    assert "catalogue" in dependency_apps

    accounts_deps = [dep[1] for dep in module.Migration.dependencies if dep[0] == "accounts"]
    assert "0002_demo_accounts" in accounts_deps


@pytest.mark.django_db
def test_account_profile_table_has_expected_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'accounts_accountprofile'
            """
        )
        columns = {row[0] for row in cursor.fetchall()}

    assert {
        "id",
        "user_id",
        "bio",
        "avatar_url",
        "collection_visibility",
        "favorites_visibility",
        "created_at",
        "updated_at",
    } <= columns
    # Never persisted here -- the alias lives only on auth_user.username.
    assert "username" not in columns


@pytest.mark.django_db
def test_favorite_slot_table_has_expected_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'accounts_favoriteslot'
            """
        )
        columns = {row[0] for row in cursor.fetchall()}

    assert {"id", "user_id", "work_id", "slot", "created_at"} <= columns


@pytest.mark.django_db
def test_account_profile_user_is_unique_one_to_one() -> None:
    """OneToOneField enforces a single profile row per user at the
    database level, not merely at the ORM layer."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT tc.constraint_type FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'accounts_accountprofile'
              AND kcu.column_name = 'user_id'
              AND tc.constraint_type = 'UNIQUE'
            """
        )
        assert cursor.fetchone() is not None


@pytest.mark.django_db
def test_account_profile_visibility_check_constraints_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname = 'accounts_profile_collection_visibility_valid'"
        )
        assert cursor.fetchone() is not None
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname = 'accounts_profile_favorites_visibility_valid'"
        )
        assert cursor.fetchone() is not None


@pytest.mark.django_db
def test_favorite_slot_constraints_enforced() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname = 'accounts_favorite_unique_user_slot'"
        )
        assert cursor.fetchone() is not None
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname = 'accounts_favorite_unique_user_work'"
        )
        assert cursor.fetchone() is not None
        cursor.execute("SELECT conname FROM pg_constraint WHERE conname = 'accounts_favorite_slot_range'")
        assert cursor.fetchone() is not None


def test_account_profile_and_favorite_slot_foreign_keys_are_cascade_or_protective() -> None:
    account_profile_model = apps.get_model("accounts", "AccountProfile")
    assert account_profile_model._meta.get_field("user").remote_field.on_delete.__name__ == "CASCADE"

    favorite_slot_model = apps.get_model("accounts", "FavoriteSlot")
    assert favorite_slot_model._meta.get_field("user").remote_field.on_delete.__name__ == "CASCADE"
    assert favorite_slot_model._meta.get_field("work").remote_field.on_delete.__name__ == "PROTECT"


def test_demo_account_identity_table_remains_separate_from_account_profile() -> None:
    """D-00b: real accounts (AccountProfile) and simulated demo fixtures
    (DemoAccountIdentity) are, and remain, two distinct tables -- Phase 5
    never folds demo-marker state into the real-account profile model."""
    demo_identity_model = apps.get_model("accounts", "DemoAccountIdentity")
    account_profile_model = apps.get_model("accounts", "AccountProfile")
    assert demo_identity_model._meta.db_table != account_profile_model._meta.db_table
