"""Show the frozen Wikidata base catalogue in the public views of a fresh install."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from catalogue.models import GameWork


class Command(BaseCommand):
    help = (
        "Mark the frozen Wikidata base works as catalogue members so a fresh local install is not empty. "
        "Does nothing when an IGDB corpus has already been governed."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        # The public catalogue only lists governed works (``in_corpus``), and governance is
        # defined over IGDB records. A clean clone has no IGDB data, so without this step the
        # 150 imported base works would stay hidden. A database that already governs an IGDB
        # corpus (the deployed one, or a full local import) is left exactly as it is.
        if GameWork.objects.filter(in_corpus=True, source_records__source="igdb").exists():
            self.stdout.write("IGDB corpus already governed; base catalogue left untouched.")
            return

        base_ids = GameWork.objects.filter(source_records__source="wikidata").exclude(
            source_records__source="igdb"
        )
        updated = base_ids.filter(in_corpus=False).update(in_corpus=True)
        self.stdout.write(self.style.SUCCESS(f"Base catalogue published: {updated} newly visible works."))
