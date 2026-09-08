"""Tests for immutable, raw IGDB PopScore primitive snapshots."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from catalogue.models import CorpusPopularitySnapshot, CorpusVersion, GameWork, SourceRecord


class FakePopularityClient:
    def fetch_popularity_types(self) -> list[dict]:
        return [{"id": 2, "name": "Want to Play", "external_popularity_source": 121}]

    def fetch_popularity_page(self, after_id: int, page_size: int = 500) -> list[dict]:
        if after_id:
            return []
        return [
            {
                "id": 1001,
                "game_id": 501,
                "popularity_type": 2,
                "value": 0.75,
                "calculated_at": 1_700_000_000,
                "updated_at": 1_700_000_100,
                "checksum": "primitive-checksum",
            },
            {"id": 1002, "game_id": 999, "popularity_type": 2, "value": 0.3},
        ]


@pytest.mark.django_db
def test_popularity_snapshot_is_primitive_level_governed_and_immutable() -> None:
    version = "popscore-test"
    CorpusVersion.objects.create(version=version, ruleset_sha256="a" * 64, is_active=True)
    work = GameWork.objects.create(
        canonical_slug="signal-quest", original_title="Signal Quest", in_corpus=True, corpus_version=version
    )
    SourceRecord.objects.create(
        work=work,
        source="igdb",
        source_id="501",
        source_url="https://www.igdb.com/games/signal-quest",
        retrieved_at=timezone.now(),
        licence="IGDB",
        snapshot_sha256="b" * 64,
    )

    output = StringIO()
    call_command(
        "snapshot_corpus_popularity",
        corpus_version=version,
        client=FakePopularityClient(),
        stdout=output,
    )

    snapshot = CorpusPopularitySnapshot.objects.get()
    assert snapshot.work_id == work.id
    assert snapshot.popularity_type_id == 2
    assert snapshot.popularity_type_name == "Want to Play"
    assert snapshot.value == pytest.approx(0.75)
    assert '"composition": null' in output.getvalue()

    call_command(
        "snapshot_corpus_popularity",
        corpus_version=version,
        client=FakePopularityClient(),
        stdout=StringIO(),
    )
    assert CorpusPopularitySnapshot.objects.count() == 1
