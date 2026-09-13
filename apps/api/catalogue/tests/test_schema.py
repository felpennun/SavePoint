"""PostgreSQL schema contract for the Phase 6 CAT-05 catalogue facets."""

from __future__ import annotations

import importlib

import pytest
from django.apps import apps
from django.db import connection


def test_publishers_migration_extends_the_applied_catalogue_chain() -> None:
    module = importlib.import_module("catalogue.migrations.0019_phase6_catalogue_publishers")
    assert ("catalogue", "0018_merge_new_releases_and_curated_labels") in module.Migration.dependencies
    assert any(operation.__class__.__name__ == "CreateModel" for operation in module.Migration.operations)


@pytest.mark.django_db
def test_publisher_table_has_provenance_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'catalogue_publisher'"
        )
        columns = {row[0] for row in cursor.fetchall()}

    assert {
        "id",
        "igdb_id",
        "name",
        "slug",
        "source",
        "source_url",
        "licence",
        "snapshot_sha256",
        "retrieved_at",
    } <= columns


@pytest.mark.django_db
def test_publisher_identity_and_work_relation_are_database_backed() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conname IN "
            "('catalogue_publisher_igdb_id_key', 'catalogue_publisher_slug_key')"
        )
        constraints = {row[0] for row in cursor.fetchall()}
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'catalogue_gamework_publishers'"
        )
        relation_columns = {row[0] for row in cursor.fetchall()}

    assert constraints == {"catalogue_publisher_igdb_id_key", "catalogue_publisher_slug_key"}
    assert {"gamework_id", "publisher_id"} <= relation_columns


def test_cat05_keeps_edition_nested_under_game_release() -> None:
    edition = apps.get_model("catalogue", "Edition")
    release = apps.get_model("catalogue", "GameRelease")
    assert edition._meta.get_field("release").remote_field.model is release
    assert edition._meta.get_field("release").remote_field.on_delete.__name__ == "PROTECT"
