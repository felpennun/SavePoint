"""Remove catalogue works released after the reproducible 2026 cutoff."""

from __future__ import annotations

from datetime import date
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from catalogue.models import Edition, GameRelease, GameWork
from library.models import LibraryEntry, OwnedCopy


class Command(BaseCommand):
    help = "Remove games whose first release date is after the selected year."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--through-year", type=int, default=2026)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the rows that would be removed without changing the database.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        through_year = options["through_year"]
        cutoff = date(through_year, 12, 31)
        works = GameWork.objects.filter(first_release_date__gt=cutoff)
        counts = {
            "works": works.count(),
            "entries": LibraryEntry.objects.filter(work__in=works).count(),
            "copies": OwnedCopy.objects.filter(work__in=works).count(),
            "releases": GameRelease.objects.filter(work__in=works).count(),
            "editions": Edition.objects.filter(release__work__in=works).count(),
        }
        action = "would remove" if options["dry_run"] else "removing"
        self.stdout.write(
            f"{action} {counts['works']} works, {counts['releases']} releases, "
            f"{counts['editions']} editions, {counts['entries']} library entries, "
            f"and {counts['copies']} owned copies (after {cutoff.isoformat()})"
        )

        if options["dry_run"]:
            return

        with transaction.atomic():
            # PROTECT relations must be removed before their work/release.
            OwnedCopy.objects.filter(work__in=works).delete()
            LibraryEntry.objects.filter(work__in=works).delete()
            Edition.objects.filter(release__work__in=works).delete()
            GameRelease.objects.filter(work__in=works).delete()
            deleted_count, _details = GameWork.objects.filter(
                first_release_date__gt=cutoff
            ).delete()

        self.stdout.write(self.style.SUCCESS(f"removed {deleted_count} catalogue rows"))
