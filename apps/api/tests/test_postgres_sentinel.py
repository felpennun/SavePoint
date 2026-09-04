"""Fail-fast proof that integration tests use PostgreSQL, never SQLite."""

import psycopg


def test_integration_database_is_postgresql(
    postgres_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    with postgres_connection.cursor() as cursor:
        cursor.execute("SELECT version(), current_setting('server_version_num')")
        version, numeric_version = cursor.fetchone()

    assert version.startswith("PostgreSQL 18.6")
    assert int(numeric_version) >= 180000

