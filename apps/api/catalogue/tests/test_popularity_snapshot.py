"""Tests for immutable, raw IGDB PopScore primitive snapshots."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from catalogue.models import CorpusPopularitySnapshot, CorpusVersion, GameWork, SourceRecord
from catalogue.popularity import normalised_popscore_by_work


class FakePopularityClient:
    def fetch_popularity_types(self) -> list[dict]:
        return [
            {"id": 1, "name": "Visits", "external_popularity_source": 121},
            {"id": 2, "name": "Want to Play", "external_popularity_source": 121},
            {"id": 3, "name": "Playing", "external_popularity_source": 121},
            {"id": 4, "name": "Played", "external_popularity_source": 121},
        ]

    def fetch_popularity_page(self, after_id: int, page_size: int = 500) -> list[dict]:
        if after_id:
            return []
        rows = []
        for type_id in range(1, 5):
            rows.append(
                {
                    "id": 1000 + type_id,
                    "game_id": 501,
                    "popularity_type": type_id,
                    "value": float(type_id),
                    "calculated_at": 1_700_000_000,
                    "updated_at": 1_700_000_100,
                    "checksum": f"high-{type_id}",
                }
            )
            rows.append(
                {
                    "id": 1010 + type_id,
                    "game_id": 502,
                    "popularity_type": type_id,
                    "value": 0.0,
                    "checksum": f"low-{type_id}",
                }
            )
        return rows + [{"id": 1020, "game_id": 999, "popularity_type": 2, "value": 0.3}]


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
    other_work = GameWork.objects.create(
        canonical_slug="quiet-quest", original_title="Quiet Quest", in_corpus=True, corpus_version=version
    )
    SourceRecord.objects.create(
        work=other_work,
        source="igdb",
        source_id="502",
        source_url="https://www.igdb.com/games/quiet-quest",
        retrieved_at=timezone.now(),
        licence="IGDB",
        snapshot_sha256="c" * 64,
    )

    output = StringIO()
    call_command(
        "snapshot_corpus_popularity",
        corpus_version=version,
        client=FakePopularityClient(),
        stdout=output,
    )

    snapshot = CorpusPopularitySnapshot.objects.get(work=work, popularity_type_id=2)
    assert snapshot.work_id == work.id
    assert snapshot.popularity_type_id == 2
    assert snapshot.popularity_type_name == "Want to Play"
    assert snapshot.value == pytest.approx(2.0)
    assert snapshot.normalised_value == pytest.approx(1.0)
    assert CorpusPopularitySnapshot.objects.filter(work=work).count() == 4
    assert CorpusPopularitySnapshot.objects.filter(work=other_work).count() == 4
    assert normalised_popscore_by_work(version, [work.id, other_work.id]) == {
        work.id: pytest.approx(1.0),
        other_work.id: pytest.approx(0.0),
    }
    assert '"id": "igdb-engagement-mean-v1"' in output.getvalue()

    call_command(
        "snapshot_corpus_popularity",
        corpus_version=version,
        client=FakePopularityClient(),
        stdout=StringIO(),
    )
    assert CorpusPopularitySnapshot.objects.count() == 8


@pytest.mark.django_db
def test_composed_popscore_remains_absent_when_any_required_primitive_is_missing() -> None:
    version = "incomplete-popscore-test"
    work = GameWork.objects.create(canonical_slug="partial", original_title="Partial")
    for type_id, name in enumerate(("Visits", "Want to Play", "Playing"), start=1):
        CorpusPopularitySnapshot.objects.create(
            work=work,
            corpus_version=version,
            popularity_type_id=type_id,
            popularity_type_name=name,
            value=1.0,
            normalised_value=0.5,
            retrieved_at=timezone.now(),
            payload_sha256=f"{type_id}" * 64,
        )

    assert normalised_popscore_by_work(version, [work.id]) == {}
