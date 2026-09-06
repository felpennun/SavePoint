"""Freeze IGDB user ratings for one active governed corpus version."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from catalogue.corpus import governed_works
from catalogue.models import CorpusRatingSnapshot, CorpusVersion, SourceRecord


SNAPSHOT_LOCK_KEY = 902_020_202


class Command(BaseCommand):
    help = "Insert immutable IGDB user-rating snapshots for an active corpus version."
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--evidence-json", default="-")

    @staticmethod
    def _retrieved_at(work: Any) -> datetime:
        source_record = (
            SourceRecord.objects.filter(work=work, source="igdb")
            .order_by("retrieved_at", "id")
            .first()
        )
        if source_record is None:
            return datetime.now(timezone.utc)
        return source_record.retrieved_at

    def _emit(self, path: str, payload: dict[str, Any]) -> None:
        blob = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob, ending="")
            return
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"evidence written: {target}")

    def handle(self, *args: Any, **options: Any) -> None:
        version = options["corpus_version"]
        corpus_version = CorpusVersion.objects.filter(version=version).first()
        if corpus_version is None:
            raise CommandError(f"unknown corpus version: {version}")
        if not corpus_version.is_active and not options["force"]:
            raise CommandError(
                f"corpus version {version} is not active; pass --force to snapshot it"
            )

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [SNAPSHOT_LOCK_KEY])
            works = list(governed_works(version).filter(rating__isnull=False).order_by("pk"))
            inserted = 0
            for work in works:
                _snapshot, created = CorpusRatingSnapshot.objects.get_or_create(
                    work=work,
                    corpus_version=version,
                    source="igdb",
                    defaults={
                        "rating": work.rating,
                        "rating_count": work.rating_count or 0,
                        "retrieved_at": self._retrieved_at(work),
                    },
                )
                inserted += int(created)

            governed = governed_works(version)
            total_count = governed.count()
            total_rating_count = governed.filter(total_rating__isnull=False).count()
            rating_count = governed.filter(rating__isnull=False).count()
            payload = {
                "corpus_version": version,
                "source": "igdb",
                "snapshots_inserted": inserted,
                "governed_count": total_count,
                "total_rating_present": total_rating_count,
                "rating_present": rating_count,
                "total_rating_coverage_pct": round(total_rating_count * 100 / total_count, 4)
                if total_count
                else 0.0,
                "rating_coverage_pct": round(rating_count * 100 / total_count, 4)
                if total_count
                else 0.0,
            }
        self._emit(options["evidence_json"], payload)
