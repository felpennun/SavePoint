"""Tests for the real-scale, resumable IGDB catalogue ingestion path
(Plan 01.1-02).

Task 1 (this first block) covers only the schema: the minimal ``Genre``
entity, its many-to-many attachment to ``GameWork``, and the durable
``IgdbImportRun`` checkpoint whose committed cursor is source/query scoped
and only ever moves forward. Works are always located by ``canonical_slug``
here, never by a fixed ``GameWork`` UUID.

Task 2 appends the importer/client behaviour tests to the same file.
"""

from __future__ import annotations

import pytest
from django.db import DatabaseError, IntegrityError, transaction

from catalogue.models import Genre, GameWork, IgdbImportRun


# ---------------------------------------------------------------------------
# Task 1 -- schema: Genre membership and resumable IGDB checkpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_genre_is_unique_by_stable_igdb_identity() -> None:
    Genre.objects.create(igdb_id=12, name="Role-playing (RPG)", slug="role-playing-rpg")

    # Same IGDB identity must not be insertable twice, even with a different name.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Genre.objects.create(igdb_id=12, name="RPG", slug="rpg")

    # A different IGDB identity is fine.
    with transaction.atomic():
        Genre.objects.create(igdb_id=31, name="Adventure", slug="adventure")

    assert Genre.objects.count() == 2


@pytest.mark.django_db
def test_genre_attaches_many_to_many_and_is_reachable_by_canonical_slug() -> None:
    work = GameWork.objects.create(canonical_slug="the-witcher-3", original_title="The Witcher 3")
    rpg = Genre.objects.create(igdb_id=12, name="Role-playing (RPG)", slug="role-playing-rpg")
    adventure = Genre.objects.create(igdb_id=31, name="Adventure", slug="adventure")

    work.genres.add(rpg, adventure)

    # Re-fetch strictly by canonical_slug -- no test may depend on the random UUID.
    reloaded = GameWork.objects.get(canonical_slug="the-witcher-3")
    assert set(reloaded.genres.values_list("igdb_id", flat=True)) == {12, 31}
    assert list(rpg.works.values_list("canonical_slug", flat=True)) == ["the-witcher-3"]


@pytest.mark.django_db
def test_import_run_checkpoint_is_scoped_by_source_and_query() -> None:
    IgdbImportRun.objects.create(source="igdb", query_identity="game_type=0")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IgdbImportRun.objects.create(source="igdb", query_identity="game_type=0")

    # A different query identity under the same source is a distinct checkpoint.
    with transaction.atomic():
        IgdbImportRun.objects.create(source="igdb", query_identity="game_type=0;platform=6")

    assert IgdbImportRun.objects.count() == 2


@pytest.mark.django_db
def test_import_run_cursor_advances_monotonically_at_the_database_level() -> None:
    run = IgdbImportRun.objects.create(
        source="igdb", query_identity="game_type=0", last_committed_igdb_id=100
    )

    # Forward moves are accepted.
    run.last_committed_igdb_id = 250
    run.save(update_fields=["last_committed_igdb_id"])
    run.refresh_from_db()
    assert run.last_committed_igdb_id == 250

    # A backwards move is rejected by the database, not merely by Python.
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            IgdbImportRun.objects.filter(pk=run.pk).update(last_committed_igdb_id=175)

    run.refresh_from_db()
    assert run.last_committed_igdb_id == 250


@pytest.mark.django_db
def test_import_run_cursor_cannot_be_created_negative() -> None:
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IgdbImportRun.objects.create(
                source="igdb", query_identity="neg", last_committed_igdb_id=-1
            )
