"""Tests for the command that makes a fresh install's base catalogue visible."""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO

import pytest
from django.core.management import call_command

from catalogue.corpus import governed_works
from catalogue.models import GameWork, SourceRecord


def _run(command: str) -> str:
    out = StringIO()
    call_command(command, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_fresh_install_shows_the_base_catalogue_and_is_idempotent() -> None:
    _run("import_catalogue")
    assert governed_works().count() == 0

    assert "150 newly visible works" in _run("publish_base_catalogue")
    assert governed_works().count() == 150

    assert "0 newly visible works" in _run("publish_base_catalogue")
    assert governed_works().count() == 150


@pytest.mark.django_db
def test_database_with_a_governed_igdb_corpus_is_left_untouched() -> None:
    _run("import_catalogue")
    igdb_work = GameWork.objects.create(
        canonical_slug="governed-igdb-work", original_title="Governed IGDB Work", in_corpus=True
    )
    SourceRecord.objects.create(
        work=igdb_work,
        source="igdb",
        source_id="1",
        source_url="https://www.igdb.com/games/governed-igdb-work",
        retrieved_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        licence="IGDB",
        snapshot_sha256="0" * 64,
    )

    assert "left untouched" in _run("publish_base_catalogue")
    assert governed_works().count() == 1
