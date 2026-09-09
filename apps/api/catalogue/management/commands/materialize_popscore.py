"""Materialise the governed four-signal IGDB PopScore."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogue.models import CorpusPopularityScore, CorpusPopularitySnapshot, CorpusVersion
from catalogue.popularity import IGDB_ENGAGEMENT_TYPES, popscore_snapshot_sha256


FORMULA_VERSION = "igdb-engagement-mean-v1"


class Command(BaseCommand):
    help = "Materialise the unweighted mean of the four normalised IGDB engagement signals."
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument("--evidence-json", default="-")

    def handle(self, *args: Any, **options: Any) -> None:
        version = options["corpus_version"]
        if not CorpusVersion.objects.filter(version=version).exists():
            raise CommandError(f"unknown corpus version: {version}")
        source_hash = popscore_snapshot_sha256(version)
        if source_hash is None:
            raise CommandError(f"corpus version {version} has no PopScore primitives")

        values: dict[object, dict[str, float]] = {}
        for work_id, name, normalised_value in CorpusPopularitySnapshot.objects.filter(
            corpus_version=version,
            popularity_type_name__in=IGDB_ENGAGEMENT_TYPES,
            normalised_value__isnull=False,
        ).values_list("work_id", "popularity_type_name", "normalised_value"):
            values.setdefault(work_id, {})[name] = float(normalised_value)

        calculated_at = datetime.now(timezone.utc)
        materialised = 0
        with transaction.atomic():
            for work_id, parts in values.items():
                if not all(name in parts for name in IGDB_ENGAGEMENT_TYPES):
                    continue
                score = math.fsum(parts[name] for name in IGDB_ENGAGEMENT_TYPES) / len(
                    IGDB_ENGAGEMENT_TYPES
                )
                CorpusPopularityScore.objects.update_or_create(
                    work_id=work_id,
                    corpus_version=version,
                    defaults={
                        "score": score,
                        "formula_version": FORMULA_VERSION,
                        "calculated_at": calculated_at,
                        "source_snapshot_sha256": source_hash,
                    },
                )
                materialised += 1

        evidence = {
            "corpus_version": version,
            "formula_version": FORMULA_VERSION,
            "required_signals": list(IGDB_ENGAGEMENT_TYPES),
            "normalisation": "log1p then average-rank percentile per primitive",
            "composition": "unweighted arithmetic mean of the four normalised primitives",
            "missing_policy": "no score row when any required primitive is absent",
            "source_snapshot_sha256": source_hash,
            "scores_materialised": materialised,
        }
        blob = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if options["evidence_json"] == "-":
            self.stdout.write(blob, ending="")
        else:
            from pathlib import Path

            target = Path(options["evidence_json"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(blob, encoding="utf-8")
            self.stderr.write(f"evidence written: {target}")
        self.stdout.write(f"materialised PopScore: {materialised} works")
