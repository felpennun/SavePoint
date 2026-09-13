from django.db import connection

import pytest

from social.models import Block, Friendship, FriendshipRequest, RelationshipPair


@pytest.mark.django_db
def test_social_schema_is_postgresql_and_migration_is_applied():
    assert connection.vendor == "postgresql"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app = %s AND name = %s",
            ["social", "0001_initial"],
        )
        assert cursor.fetchone() == (1,)

        for model in (RelationshipPair, Friendship, FriendshipRequest, Block):
            table = model._meta.db_table
            cursor.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s",
                [table],
            )
            assert cursor.fetchone() == (1,)


@pytest.mark.django_db
def test_social_constraints_and_indexes_are_present_in_postgresql():
    expected_constraints = {
        RelationshipPair: {
            "social_unique_relationship_pair",
            "social_pair_users_canonical",
        },
        FriendshipRequest: {
            "social_request_no_self",
            "social_request_status_valid",
        },
        Block: {"social_unique_block_direction", "social_block_no_self"},
    }
    expected_indexes = {
        RelationshipPair: {"social_pair_lookup"},
        FriendshipRequest: {
            "social_request_sender_status",
            "social_request_receiver_status",
            "social_unique_pending_request_direction",
        },
        Block: {"social_blocker_active", "social_blocked_active"},
    }

    with connection.cursor() as cursor:
        for model, names in expected_constraints.items():
            cursor.execute(
                "SELECT conname FROM pg_constraint WHERE conrelid = %s::regclass",
                [model._meta.db_table],
            )
            actual = {row[0] for row in cursor.fetchall()}
            assert names <= actual

        for model, names in expected_indexes.items():
            cursor.execute(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND tablename = %s",
                [model._meta.db_table],
            )
            actual = {row[0] for row in cursor.fetchall()}
            assert names <= actual


@pytest.mark.django_db
def test_model_metadata_matches_database_invariants():
    for model in (RelationshipPair, Friendship, FriendshipRequest, Block):
        assert model._meta.required_db_vendor in (None, "postgresql")
        assert model._meta.db_table.startswith("social_")
        assert model._meta.constraints or model is Friendship

    assert any(constraint.name == "social_unique_pending_request_direction" for constraint in FriendshipRequest._meta.constraints)
    assert any(constraint.name == "social_unique_block_direction" for constraint in Block._meta.constraints)
