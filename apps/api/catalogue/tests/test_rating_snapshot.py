import hashlib
import io
from datetime import datetime, timezone

import pytest
from django.core.management import CommandError, call_command

from catalogue.models import CorpusRatingSnapshot, CorpusVersion, GameWork, SourceRecord


pytestmark = pytest.mark.django_db


def make_rating_work(source_id: int, *, rating: float | None, total_rating: float | None) -> GameWork:
    work = GameWork.objects.create(
        canonical_slug=f"rating-work-{source_id}",
        original_title=f"Rating Work {source_id}",
        first_release_date="2020-01-01",
        in_corpus=True,
        corpus_version="2026.09.2",
        rating=rating,
        rating_count=10 if rating is not None else None,
        total_rating=total_rating,
        total_rating_count=10 if total_rating is not None else None,
    )
    SourceRecord.objects.create(
        work=work,
        source="igdb",
        source_id=str(source_id),
        source_url=f"https://www.igdb.com/games/rating-work-{source_id}",
        retrieved_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
        licence="IGDB",
        snapshot_sha256=hashlib.sha256(str(source_id).encode()).hexdigest(),
    )
    return work


def setup_active_version() -> None:
    CorpusVersion.objects.create(
        version="2026.09.2",
        ruleset_sha256="a" * 64,
        is_active=True,
        governed_count=2,
    )


def run_snapshot() -> str:
    output = io.StringIO()
    call_command(
        "snapshot_corpus_ratings",
        corpus_version="2026.09.2",
        evidence_json="-",
        stdout=output,
    )
    return output.getvalue()


def test_snapshot_is_insert_only_and_reports_both_rating_coverages() -> None:
    rated = make_rating_work(1, rating=88.0, total_rating=80.0)
    make_rating_work(2, rating=None, total_rating=None)
    setup_active_version()

    first = run_snapshot()
    snapshot = CorpusRatingSnapshot.objects.get(work=rated)
    retrieved_at = snapshot.retrieved_at
    rated.rating = 12.0
    rated.save(update_fields=["rating"])
    second = run_snapshot()

    assert CorpusRatingSnapshot.objects.count() == 1
    snapshot.refresh_from_db()
    assert snapshot.rating == 88.0
    assert snapshot.retrieved_at == retrieved_at
    assert '"snapshots_inserted": 1' in first
    assert '"snapshots_inserted": 0' in second
    assert '"rating_present": 1' in second
    assert '"total_rating_count_present": 1' in second


def test_snapshot_rejects_inactive_version_without_force() -> None:
    make_rating_work(3, rating=70.0, total_rating=70.0)
    CorpusVersion.objects.create(
        version="2026.09.1",
        ruleset_sha256="b" * 64,
        is_active=False,
        governed_count=1,
    )

    with pytest.raises(CommandError, match="not active"):
        call_command(
            "snapshot_corpus_ratings",
            corpus_version="2026.09.1",
            evidence_json="-",
        )
