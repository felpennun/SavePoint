"""Import DLC/expansion relationships for already imported IGDB games."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from catalogue.igdb import GAME_FIELDS, IgdbClient, redact
from catalogue.management.commands.import_igdb_catalogue import Command as IgdbImportCommand
from catalogue.models import GameWork, RelatedContent, SourceRecord

RELATION_FIELDS = "id,dlcs,expansions"
MAX_BATCH = 100


class Command(BaseCommand):
    help = "Sync DLC and expansion relationships for imported IGDB games."
    stealth_options = ("client",)
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--slug",
            action="append",
            dest="slugs",
            help="only sync this canonical slug; repeat for more than one work",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        client = options.get("client") or IgdbClient()
        parents = SourceRecord.objects.filter(source="igdb").select_related("work")
        if options.get("slugs"):
            parents = parents.filter(work__canonical_slug__in=options["slugs"])
        parents = list(parents)
        if not parents:
            self.stdout.write("No imported IGDB parent works matched.")
            return

        try:
            relation_rows: dict[int, list[tuple[int, str]]] = {}
            for start in range(0, len(parents), MAX_BATCH):
                ids = [int(row.source_id) for row in parents[start : start + MAX_BATCH]]
                for row in client.fetch_by_ids(ids, fields=RELATION_FIELDS):
                    parent_id = int(row["id"])
                    for child_id in row.get("dlcs") or []:
                        relation_rows.setdefault(parent_id, []).append((int(child_id), "dlc"))
                    for child_id in row.get("expansions") or []:
                        relation_rows.setdefault(parent_id, []).append((int(child_id), "expansion"))

            child_ids = sorted({child_id for rows in relation_rows.values() for child_id, _ in rows})
            child_rows: dict[int, dict] = {}
            for start in range(0, len(child_ids), MAX_BATCH):
                rows = client.fetch_by_ids(child_ids[start : start + MAX_BATCH], fields=GAME_FIELDS)
                child_rows.update({int(row["id"]): row for row in rows})

            importer = IgdbImportCommand()
            now = datetime.now(timezone.utc)
            imported_children = 0
            links = 0
            parent_by_igdb = {int(row.source_id): row.work for row in parents}
            for child_id, row in child_rows.items():
                normalized = importer._normalize(row)
                importer._upsert(normalized, now)
                child = SourceRecord.objects.get(source="igdb", source_id=str(child_id)).work
                if not child.is_dlc:
                    child.is_dlc = True
                    child.save(update_fields=["is_dlc"])
                imported_children += 1

            for parent_id, rows in relation_rows.items():
                parent = parent_by_igdb.get(parent_id)
                if parent is None:
                    continue
                for child_id, relation in rows:
                    child_record = SourceRecord.objects.filter(source="igdb", source_id=str(child_id)).select_related("work").first()
                    if child_record is None or child_record.work_id == parent.id:
                        continue
                    RelatedContent.objects.update_or_create(
                        parent_work=parent,
                        child_work=child_record.work,
                        defaults={"relation": relation},
                    )
                    links += 1
        except Exception as exc:  # noqa: BLE001 - never expose credentials
            raise CommandError(f"IGDB relationship sync failed: {redact(str(exc))}") from None

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced {imported_children} related works and {links} DLC/expansion links."
            )
        )
