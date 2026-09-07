"""Generate the reproducible synthetic population used by evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from catalogue.models import CorpusVersion
from evaluation.archetypes import DEFAULT_ARCHETYPES
from evaluation.synthetic import (
    SyntheticGenerationError,
    apply_population,
    default_report_path,
    generate,
    render_validation_report,
)


class Command(BaseCommand):
    help = "Generate deterministic synthetic evaluation users from the governed corpus."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--seed", type=int, required=True)
        parser.add_argument("--corpus-version", default=None)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--validation-report", nargs="?", const="__default__", default=None)

    def handle(self, *args: Any, **options: Any) -> None:
        corpus_version = options.get("corpus_version")
        if corpus_version is None:
            corpus_version = (
                CorpusVersion.objects.filter(is_active=True)
                .values_list("version", flat=True)
                .first()
            )
        try:
            population = generate(options["seed"], DEFAULT_ARCHETYPES, corpus_version)
        except (SyntheticGenerationError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        report_option = options.get("validation_report")
        if report_option is not None:
            report_path = default_report_path() if report_option == "__default__" else Path(report_option)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(render_validation_report(population), encoding="utf-8")
            self.stdout.write(f"Validation report written (path={report_path})")

        if options.get("dry_run"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Synthetic population validated (users={len(population.users)}, dry_run=true)"
                )
            )
            return

        try:
            result = apply_population(population)
        except SyntheticGenerationError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Synthetic population ready (users={len(population.users)}, "
                f"created={result['created']}, updated={result['updated']}, "
                f"anchors={result['anchor_ids']})"
            )
        )
