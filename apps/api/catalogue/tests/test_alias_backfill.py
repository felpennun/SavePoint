"""Tests for the one-off ``backfill_game_aliases`` command (Plan 02-03 Task 1).

The IGDB import historically wrote no ``GameAlias`` rows and tolerant search
matches only on ``GameAlias.normalized_value``; this backfill revives search
over the imported catalogue. It must be idempotent (unique constraint), keep
the primary + ``title_en`` aliases per work, feed all three search tiers
(exact / prefix / trigram), and finish with ``VACUUM ANALYZE``.
"""

from __future__ import annotations

import json
from io import StringIO

import pytest
from django.core.management import call_command

from catalogue.models import GameAlias, GameWork
from catalogue.normalization import normalize_title
from catalogue.search import search_games


def _igdb_work(*, title: str, title_en: str = "", in_corpus: bool = True) -> GameWork:
    """A governed work with no ``GameAlias`` rows -- the pre-backfill state."""
    return GameWork.objects.create(
        canonical_slug=title.lower().replace(" ", "-").replace(":", "").replace("&", "and"),
        original_title=title,
        title_en=title_en or title,
        title_es="",
        in_corpus=in_corpus,
        total_rating_count=1000,
    )


def _run(**kwargs: object) -> tuple[str, str]:
    out, err = StringIO(), StringIO()
    call_command("backfill_game_aliases", stdout=out, stderr=err, **kwargs)
    return out.getvalue(), err.getvalue()


def _titles(result: dict) -> set[str]:
    return {w.original_title for w in result["results"]}


@pytest.mark.django_db
def test_backfill_creates_primary_and_distinct_title_en_aliases() -> None:
    w1 = _igdb_work(title="Chrono Trigger")
    w2 = _igdb_work(title="Ys I & II", title_en="Ys One and Two")
    w3 = _igdb_work(title="Portal", title_en="Portal")  # title_en collapses
    assert GameAlias.objects.count() == 0

    _run()

    assert set(w1.aliases.values_list("locale", "normalized_value")) == {
        ("en", normalize_title("Chrono Trigger")),
    }
    assert set(w2.aliases.values_list("normalized_value", flat=True)) == {
        normalize_title("Ys I & II"),
        normalize_title("Ys One and Two"),
    }
    assert set(w3.aliases.values_list("normalized_value", flat=True)) == {
        normalize_title("Portal"),
    }


@pytest.mark.django_db
def test_backfill_makes_work_findable_by_exact_prefix_and_trigram() -> None:
    _igdb_work(title="Boulder Dash")

    _run()

    assert _titles(search_games("Boulder Dash")) == {"Boulder Dash"}  # exact
    assert "Boulder Dash" in _titles(search_games("Boulder"))  # prefix
    assert "Boulder Dash" in _titles(search_games("Boulder Dach"))  # trigram typo


@pytest.mark.django_db
def test_backfill_is_idempotent_second_run_adds_no_rows() -> None:
    _igdb_work(title="Half-Life 2")
    _igdb_work(title="Portal", title_en="Portal")

    _run()
    after_first = GameAlias.objects.count()
    assert after_first == 2

    _run()
    assert GameAlias.objects.count() == after_first


@pytest.mark.django_db
def test_backfill_summary_reports_counts_and_leaks_no_secrets() -> None:
    _igdb_work(title="Terraria")

    out, err = _run(evidence_json="-")

    assert "postgres://" not in out and "postgresql://" not in out
    assert "password" not in out.lower()
    payload = json.loads(out)
    assert payload["works_processed"] == 1
    assert payload["aliases_created"] == 1
    assert payload["conflicts_ignored"] == 0
    assert payload["alias_table_total"] == 1


@pytest.mark.django_db(transaction=True)
def test_backfill_runs_vacuum_analyze_after_batches() -> None:
    _igdb_work(title="Stardew Valley")

    out, _err = _run(evidence_json="-")

    payload = json.loads(out)
    assert payload["vacuum_analyze_catalogue_gamealias"] is True
    assert GameAlias.objects.filter(normalized_value=normalize_title("Stardew Valley")).exists()
