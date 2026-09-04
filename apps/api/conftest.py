"""Shared pytest fixtures for the pre-scaffold PostgreSQL sentinel."""

from collections.abc import Iterator
import os

import psycopg
import pytest


@pytest.fixture
def postgres_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    """Open a real PostgreSQL connection without exposing credentials in output."""
    required = (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        pytest.fail("Missing PostgreSQL test configuration: " + ", ".join(missing), pytrace=False)

    with psycopg.connect(
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        connect_timeout=5,
    ) as connection:
        yield connection

