"""One-off backfill of English ``GameAlias`` rows for existing ``GameWork`` rows.

Offline management command only -- never a request-time path (CAT-06 / OPS-03).

Root cause it fixes: the IGDB catalogue import historically wrote no
``GameAlias`` rows, and tolerant search (:mod:`catalogue.search`) matches
*only* on ``GameAlias.normalized_value``. Without this backfill the ~312k
imported works are effectively unsearchable.

For every ``GameWork`` it rebuilds the desired English alias set with
:func:`catalogue.aliasing.desired_aliases` (primary ``original_title`` plus
``title_en`` when distinct) and ``bulk_create``s the missing rows. Idempotent
via the ``(work, locale, normalized_value)`` unique constraint: a second run
inserts nothing. Work rows are paged by ascending primary key -- no held
server-side cursor -- and each page's inserts commit in their own
``transaction.atomic()`` guarded by one ``pg_advisory_xact_lock`` (importer
discipline). After the batches a single ``VACUUM ANALYZE catalogue_gamealias``
flushes the GIN trigram pending list and refreshes planner stats; it is
skipped with a notice when the command runs inside an existing transaction
(``VACUUM`` cannot run in a transaction block).

No credential, token, or connection string is ever printed: the summary is
counts only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from catalogue.aliasing import ALIAS_LOCALE, desired_aliases
from catalogue.models import GameAlias, GameWork

# Transaction-scoped advisory lock key -- distinct from the Wikidata importer's
# 725_01_06 and the IGDB importer's 725_0101_02.
BACKFILL_LOCK_KEY = 725_0203_03

# Works read per page; alias rows flushed per bulk_create.
WORK_PAGE_SIZE = 2000
ALIAS_BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "One-off backfill of English GameAlias rows for existing GameWork rows."

    # Offline data command: skip the system-check pass so `--evidence-json -`
    # keeps stdout to pure JSON.
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--evidence-json",
            default="",
            help="write the backfill summary as JSON to this path ('-' = stdout)",
        )

    def _flush(self, objs: list[GameAlias]) -> None:
        if not objs:
            return
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(%s)", [BACKFILL_LOCK_KEY])
            GameAlias.objects.bulk_create(
                objs, ignore_conflicts=True, batch_size=ALIAS_BATCH_SIZE
            )

    def handle(self, *args: Any, **options: Any) -> None:
        evidence_json = options["evidence_json"]

        before = GameAlias.objects.count()
        works_processed = 0
        alias_rows_considered = 0
        pending: list[GameAlias] = []

        last_id = None
        while True:
            page_qs = GameWork.objects.order_by("id")
            if last_id is not None:
                page_qs = page_qs.filter(id__gt=last_id)
            page = list(
                page_qs.values_list("id", "original_title", "title_en")[:WORK_PAGE_SIZE]
            )
            if not page:
                break
            for work_id, original_title, title_en in page:
                for normalized, value in desired_aliases(original_title, title_en).items():
                    pending.append(
                        GameAlias(
                            work_id=work_id,
                            locale=ALIAS_LOCALE,
                            value=value,
                            normalized_value=normalized,
                        )
                    )
                    alias_rows_considered += 1
                works_processed += 1
            if len(pending) >= ALIAS_BATCH_SIZE:
                self._flush(pending)
                pending = []
            last_id = page[-1][0]
        self._flush(pending)

        after = GameAlias.objects.count()
        created = after - before
        conflicts_ignored = alias_rows_considered - created

        vacuumed = False
        if connection.in_atomic_block:
            self.stderr.write(
                "VACUUM ANALYZE catalogue_gamealias skipped: running inside an "
                "atomic block (test harness / nested transaction)"
            )
        else:
            with connection.cursor() as cur:
                cur.execute("VACUUM ANALYZE catalogue_gamealias")
            vacuumed = True

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "works_processed": works_processed,
            "alias_rows_considered": alias_rows_considered,
            "aliases_created": created,
            "conflicts_ignored": conflicts_ignored,
            "alias_table_total": after,
            "vacuum_analyze_catalogue_gamealias": vacuumed,
        }
        self.stderr.write(
            self.style.SUCCESS(
                f"alias backfill: {works_processed} works processed, "
                f"{created} aliases created, {conflicts_ignored} conflicts ignored, "
                f"{after} alias rows total"
            )
        )
        if evidence_json:
            self._emit_evidence(evidence_json, summary)

    def _emit_evidence(self, path: str, evidence: dict) -> None:
        blob = json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob)
            return
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"evidence written: {target}")
