"""Audit recommendation-signal coverage without rebuilding feature vectors."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from recommendations.content.features import coverage_report


class Command(BaseCommand):
    help = "Audit recommendation-signal coverage for a governed corpus version."

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument(
            "--corpus-version",
            default=None,
            help="Pin the governed view to one corpus_version (default: active view).",
        )
        parser.add_argument(
            "--evidence-json",
            default=None,
            help="Write the read-only signal coverage audit to this path.",
        )

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        report = coverage_report(options["corpus_version"])
        evidence = {
            "audit": "recommendation-signal-coverage",
            "read_only": True,
            "coverage_report": report,
        }

        evidence_path = options.get("evidence_json")
        if evidence_path:
            path = Path(evidence_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.stdout.write(f"Wrote signal coverage evidence to {path}")

        self.stdout.write(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
