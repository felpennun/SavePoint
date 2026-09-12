"""Derive cohort evidence from a completed evaluation artifact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from evaluation.cohort_analysis import analyse_artifact, render_markdown


class Command(BaseCommand):
    help = "Analyse an existing offline evaluation artifact by synthetic-user cohort."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--artifact-json", required=True)
        parser.add_argument("--population-manifest", required=True)
        parser.add_argument("--output-json", required=True)
        parser.add_argument("--output-markdown", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            artifact = json.loads(Path(options["artifact_json"]).read_text(encoding="utf-8"))
            manifest = json.loads(Path(options["population_manifest"]).read_text(encoding="utf-8"))
            report = analyse_artifact(artifact, manifest)
            Path(options["output_json"]).parent.mkdir(parents=True, exist_ok=True)
            Path(options["output_json"]).write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            Path(options["output_markdown"]).parent.mkdir(parents=True, exist_ok=True)
            Path(options["output_markdown"]).write_text(
                render_markdown(report), encoding="utf-8"
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CommandError(f"cannot analyse evaluation artifact: {exc}") from exc
        self.stdout.write(
            f"Wrote cohort evidence to {options['output_json']} and {options['output_markdown']}"
        )
