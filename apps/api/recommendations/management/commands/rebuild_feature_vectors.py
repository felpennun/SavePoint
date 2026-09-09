"""Rebuild the ``WorkFeatureVector`` cache for the governed corpus.

Offline, batched, idempotent (``update_or_create`` per
``(work, feature_set_version)``) -- safe to re-run (threat T-02-10-03). The
franchise / developer facets are included only when
``features.coverage_report`` says their measured coverage clears the D-11
threshold; ``--evidence-json`` writes that report next to the run.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalogue.corpus import governed_works
from recommendations.content.features import (
    FEATURE_SET_VERSION,
    coverage_report,
    feature_vector,
)
from recommendations.models import WorkFeatureVector


class Command(BaseCommand):
    help = "Rebuild the WorkFeatureVector cache for every governed work."

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument(
            "--corpus-version",
            default=None,
            help="Pin the governed view to one corpus_version (default: active view).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Works fetched per DB round-trip (default: 1000).",
        )
        parser.add_argument(
            "--evidence-json",
            default=None,
            help="Write the D-11 coverage_report to this path.",
        )

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        corpus_version = options["corpus_version"]
        batch_size = options["batch_size"]

        report = coverage_report(corpus_version)
        include_franchise = report["include_franchise"]
        include_developer = report["include_developer"]

        queryset = governed_works(corpus_version).prefetch_related(
            "genres", "releases__platform", "franchises", "developers"
        )

        created = 0
        updated = 0
        batch: list[WorkFeatureVector] = []

        def flush() -> None:
            nonlocal created, updated
            if not batch:
                return
            work_ids = [row.work_id for row in batch]
            existing = set(
                WorkFeatureVector.objects.filter(
                    work_id__in=work_ids,
                    feature_set_version=FEATURE_SET_VERSION,
                ).values_list("work_id", flat=True)
            )
            WorkFeatureVector.objects.bulk_create(
                batch,
                update_conflicts=True,
                update_fields=["vector_json", "updated_at"],
                unique_fields=["work", "feature_set_version"],
            )
            created += len(work_ids) - len(existing)
            updated += len(existing)
            batch.clear()

        for work in queryset.iterator(chunk_size=batch_size):
            batch.append(
                WorkFeatureVector(
                    work=work,
                    feature_set_version=FEATURE_SET_VERSION,
                    vector_json=feature_vector(
                        work,
                        include_franchise=include_franchise,
                        include_developer=include_developer,
                    ),
                    updated_at=timezone.now(),
                )
            )
            if len(batch) >= batch_size:
                flush()
        flush()

        summary = {
            "feature_set_version": FEATURE_SET_VERSION,
            "corpus_version": corpus_version,
            "governed_count": report["governed_count"],
            "vectors_created": created,
            "vectors_updated": updated,
            "include_franchise": include_franchise,
            "include_developer": include_developer,
            "coverage_report": report,
        }

        if options["evidence_json"]:
            path = Path(options["evidence_json"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
            self.stdout.write(f"Wrote coverage evidence to {path}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Rebuilt {created + updated} feature vectors "
                f"({created} created, {updated} updated) at {FEATURE_SET_VERSION}."
            )
        )
