"""Tests for RAWG matching and bounded client behaviour."""

from __future__ import annotations

from datetime import date

import pytest
from django.core.management import CommandError, call_command

from catalogue.models import CorpusRatingSnapshot, CorpusVersion, GameAlias, GameWork, SourceRecord
from catalogue.rawg import RAWG_GAMES_URL, RawgClient, RawgClientError
from catalogue.management.commands.enrich_rawg_ratings import reconcile_rawg_candidate


pytestmark = pytest.mark.django_db


def make_work() -> GameWork:
    work = GameWork.objects.create(
        canonical_slug="the-legend-of-zelda",
        original_title="The Legend of Zelda",
        first_release_date=date(1986, 2, 21),
        in_corpus=True,
        corpus_version="2026.09.1",
    )
    GameAlias.objects.create(
        work=work,
        locale="en",
        value="Zelda",
        normalized_value="zelda",
    )
    return work


def test_reconcile_prefers_exact_slug() -> None:
    work = make_work()
    exact = {"id": 1, "slug": "the-legend-of-zelda", "name": "Wrong label", "released": "2020-01-01"}
    assert reconcile_rawg_candidate(work, [exact]) == exact


def test_reconcile_uses_normalized_title_and_year_without_fuzzy_matching() -> None:
    work = make_work()
    candidate = {"id": 2, "slug": "zelda", "name": "The Legend of Zelda", "released": "1986-01-01"}
    assert reconcile_rawg_candidate(work, [candidate]) == candidate
    assert reconcile_rawg_candidate(work, [{**candidate, "name": "The Legend of Zelda II"}]) is None
    assert reconcile_rawg_candidate(work, [{**candidate, "released": "1987-01-01"}]) is None


class FakeRawgClient:
    def __init__(self, candidates: list[dict]) -> None:
        self.candidates = candidates
        self.calls: list[str] = []

    def search_games(self, title: str) -> list[dict]:
        self.calls.append(title)
        return self.candidates


def test_enrichment_is_bounded_and_writes_rawg_snapshot() -> None:
    work = make_work()
    CorpusVersion.objects.create(version="2026.09.1", ruleset_sha256="a" * 64, is_active=True)
    fake = FakeRawgClient([
        {
            "id": 10,
            "slug": "the-legend-of-zelda",
            "name": "The Legend of Zelda",
            "released": "1986-01-01",
            "rating": 4.5,
            "ratings_count": 250,
        }
    ])
    call_command("enrich_rawg_ratings", corpus_version="2026.09.1", limit=1, client=fake)
    snapshot = CorpusRatingSnapshot.objects.get(work=work, source="rawg")
    assert snapshot.rating == 90.0
    assert snapshot.rating_count == 250
    assert SourceRecord.objects.filter(work=work, source="rawg").exists()
    assert fake.calls == ["The Legend of Zelda"]


def test_rawg_client_requires_key_without_leaking_it() -> None:
    with pytest.raises(RawgClientError, match="RAWG_API_KEY"):
        RawgClient(api_key="")

