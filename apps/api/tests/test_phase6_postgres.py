"""Final PostgreSQL and research-snapshot sentinel for Phase 6."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


REPO_ROOT = Path(__file__).resolve().parents[3]

# These are deliberately small, immutable research inputs and generated
# evidence files. The fixed values make an accidental enrichment/evaluation
# rewrite visible without reading or emitting any credential-shaped content.
RESEARCH_SNAPSHOT_HASHES = {
    "data/raw/wikidata-games.json": "a2b5d8d1f4388b21a03a5c3c983840e38db2c5e176613913985a5e38f7408159",
    "data/manifests/catalogue.json": "8b1e3ea49090dd25fbff5a4a36fb284b9d7f5fd9170c85886b5979dcd7cc6f47",
    "data/manifests/assets.json": "7950a0125cbefdba092711ef1e6e879d97d04506492a0313a5ac6596f5eeeb5f",
    "apps/api/corpus-governance-2026.09.2.json": "fd762e4895571f2b11daf182a43a4ac647f7c8070c7261399ddba636441f86e8",
    "apps/api/corpus-ratings-2026.09.2.json": "6a8d3bdd7c2a0f2b6bec51035dfd47ed82bbebba124bfaa6ba381a66f9531b53",
    "apps/api/corpus-popularity-2026.09.2.json": "8bbc9ba9b87dbcb0637a1c2439a3a49cbc142bba6c2bfcf06a3d28ef4be69592",
    "apps/api/feature-vector-cache-2026.09.2.json": "2b7699171b3295214db117ab2f4486cfbec9a1e0d12a66e24faba33f982872d7",
}

PHASE_MIGRATIONS = {
    "accounts": {"0003_phase5_profile"},
    "catalogue": {"0019_phase6_catalogue_publishers"},
    "library": {"0005_libraryentry_is_platinum", "0006_phase6_public_list_slug"},
    "social": {"0001_initial", "0002_socialmessage"},
}

EXPECTED_TABLES = {
    "accounts_accountprofile",
    "accounts_demoaccountidentity",
    "accounts_favoriteslot",
    "catalogue_publisher",
    "catalogue_gamework_publishers",
    "library_customlist",
    "library_customlistitem",
    "library_gamecomment",
    "social_relationshippair",
    "social_friendshiprequest",
    "social_friendship",
    "social_block",
    "social_socialmessage",
}

EXPECTED_CONSTRAINTS = {
    "accounts_profile_collection_visibility_valid",
    "accounts_profile_favorites_visibility_valid",
    "accounts_favorite_slot_range",
    "catalogue_publisher_igdb_id_key",
    "catalogue_publisher_slug_key",
    "library_unique_public_slug_per_owner",
    "library_unique_list_item_work",
    "library_unique_list_item_position",
    "social_unique_relationship_pair",
    "social_pair_users_canonical",
    "social_unique_block_direction",
    "social_message_no_self",
    "social_message_hidden_reason_consistent",
}

EXPECTED_INDEXES = {
    "catalogue_publisher_igdb_id_key",
    "catalogue_publisher_slug_key",
    "catalogue_gamework_publi_gamework_id_publisher_id_61ce1e25_uniq",
    "library_unique_public_slug_per_owner",
    "social_pair_lookup",
    "social_request_sender_status",
    "social_request_receiver_status",
    "social_unique_pending_request_direction",
    "social_blocker_active",
    "social_blocked_active",
    "social_message_unread",
    "social_msg_cooldown_idx",
}


@pytest.mark.django_db
def test_phase6_uses_postgresql_18_6() -> None:
    assert connection.vendor == "postgresql"
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('server_version')")
        version = cursor.fetchone()[0]
    assert str(version).startswith("18.6"), version


@pytest.mark.django_db
def test_phase6_migrations_are_applied_without_unexpected_targets() -> None:
    executor = MigrationExecutor(connection)
    applied = {
        app: {name for app_name, name in executor.loader.applied_migrations if app_name == app}
        for app in PHASE_MIGRATIONS
    }
    for app, migrations in PHASE_MIGRATIONS.items():
        assert migrations <= applied[app]


@pytest.mark.django_db
def test_phase6_tables_constraints_and_indexes_are_database_backed() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT conname FROM pg_constraint")
        constraints = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
        indexes = {row[0] for row in cursor.fetchall()}

    assert EXPECTED_TABLES <= tables
    assert EXPECTED_CONSTRAINTS <= constraints
    assert EXPECTED_INDEXES <= indexes


@pytest.mark.django_db
def test_phase6_migration_plan_is_empty() -> None:
    executor = MigrationExecutor(connection)
    assert executor.migration_plan(executor.loader.graph.leaf_nodes()) == []


def test_frozen_research_snapshots_have_expected_sha256() -> None:
    for relative_path, expected_hash in RESEARCH_SNAPSHOT_HASHES.items():
        path = REPO_ROOT / relative_path
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == expected_hash, relative_path
