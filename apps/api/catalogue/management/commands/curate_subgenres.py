"""Build the versioned subgenre corpus from raw IGDB keyword rows."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Count
from django.utils.text import slugify

from catalogue.models import GameWork, Keyword, Subgenre, SubgenreKeyword
from catalogue.subgenres import (
    MIN_WORK_FREQUENCY,
    SUBGENRE_CURATION_VERSION,
    canonical_name_for_keyword,
    curation_manifest,
    is_excluded_canonical,
)


CURATION_LOCK_KEY = 902_020_203


class Command(BaseCommand):
    help = "Build the curated subgenre corpus from the explicit IGDB keyword mapping."
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        base_version_action = parser._option_string_actions.get("--version")
        if base_version_action is not None:
            parser._handle_conflict_resolve(None, [("--version", base_version_action)])
        parser.add_argument("--version", default=SUBGENRE_CURATION_VERSION)
        parser.add_argument("--min-work-frequency", type=int, default=MIN_WORK_FREQUENCY)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--evidence-json", default="-")

    @staticmethod
    def _report(
        *,
        version: str,
        min_work_frequency: int,
        keyword_count: int,
        mapped_keyword_count: int,
        excluded_keyword_count: int,
        omitted_keyword_count: int,
        canonical_before_frequency: int,
        canonical_after_frequency: int,
        singleton_canonical_count: int,
        singleton_canonical_names: list[str],
        included_canonical_names: list[str],
        work_count: int,
        association_count: int,
        dry_run: bool,
    ) -> dict[str, object]:
        manifest = curation_manifest()
        return {
            "curation_version": version,
            "mapping_sha256": manifest["sha256"],
            "min_work_frequency": min_work_frequency,
            "dry_run": dry_run,
            "raw_keyword_count": keyword_count,
            "mapped_keyword_count": mapped_keyword_count,
            "explicitly_excluded_keyword_count": excluded_keyword_count,
            "omitted_unlisted_keyword_count": omitted_keyword_count,
            "canonical_count_before_frequency": canonical_before_frequency,
            "canonical_count_after_frequency": canonical_after_frequency,
            "singleton_canonical_count": singleton_canonical_count,
            "singleton_canonical_names": singleton_canonical_names,
            "included_canonical_names": included_canonical_names,
            "curated_work_count": work_count,
            "subgenre_association_count": association_count,
            "manifest": manifest,
        }

    def _emit(self, path: str, report: dict[str, object]) -> None:
        blob = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob, ending="")
            return
        from pathlib import Path

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"subgenre evidence written: {target}")

    def handle(self, *args: Any, **options: Any) -> None:
        version = str(options["version"])
        min_work_frequency = int(options["min_work_frequency"])
        if min_work_frequency < 1:
            self.stderr.write(self.style.ERROR("--min-work-frequency must be at least 1"))
            return

        keyword_rows = list(Keyword.objects.all().only("id", "name"))
        groups: dict[str, list[Keyword]] = defaultdict(list)
        mapped_keyword_count = 0
        excluded_keyword_count = 0
        omitted_keyword_count = 0
        for keyword in keyword_rows:
            canonical = canonical_name_for_keyword(keyword.name)
            if canonical is None:
                omitted_keyword_count += 1
            elif is_excluded_canonical(canonical):
                excluded_keyword_count += 1
            else:
                groups[canonical].append(keyword)
                mapped_keyword_count += 1

        selected: dict[str, list[Keyword]] = {}
        singleton_canonical_count = 0
        singleton_canonical_names: list[str] = []
        for canonical, keywords in groups.items():
            keyword_ids = [keyword.pk for keyword in keywords]
            work_count = GameWork.objects.filter(keywords__id__in=keyword_ids).distinct().count()
            if work_count >= min_work_frequency:
                selected[canonical] = keywords
            else:
                singleton_canonical_count += 1
                singleton_canonical_names.append(canonical)

        work_ids: set[Any] = set()
        association_rows: list[tuple[Any, Any]] = []
        source_rows: list[tuple[Any, Any]] = []
        if not options["dry_run"]:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CURATION_LOCK_KEY])
                GameWork.subgenres.through.objects.all().delete()
                SubgenreKeyword.objects.all().delete()
                Subgenre.objects.all().delete()

                subgenres = [
                    Subgenre(name=canonical, slug=slugify(canonical)[:200], curation_version=version)
                    for canonical in sorted(selected)
                ]
                Subgenre.objects.bulk_create(subgenres)
                by_name = {subgenre.name: subgenre for subgenre in Subgenre.objects.all()}

                for canonical, keywords in selected.items():
                    subgenre = by_name[canonical]
                    for keyword in keywords:
                        source_rows.append((subgenre.pk, keyword.pk))
                    related_work_ids = set(
                        GameWork.objects.filter(keywords__id__in=[keyword.pk for keyword in keywords])
                        .distinct()
                        .values_list("pk", flat=True)
                    )
                    work_ids.update(related_work_ids)
                    association_rows.extend((work_id, subgenre.pk) for work_id in related_work_ids)

                SubgenreKeyword.objects.bulk_create(
                    [SubgenreKeyword(subgenre_id=subgenre_id, keyword_id=keyword_id) for subgenre_id, keyword_id in source_rows],
                    batch_size=5000,
                )
                GameWork.subgenres.through.objects.bulk_create(
                    [
                        GameWork.subgenres.through(gamework_id=work_id, subgenre_id=subgenre_id)
                        for work_id, subgenre_id in association_rows
                    ],
                    batch_size=5000,
                    ignore_conflicts=True,
                )
        else:
            for canonical, keywords in selected.items():
                related_work_ids = set(
                    GameWork.objects.filter(keywords__id__in=[keyword.pk for keyword in keywords])
                    .distinct()
                    .values_list("pk", flat=True)
                )
                work_ids.update(related_work_ids)
                association_rows.extend((work_id, canonical) for work_id in related_work_ids)

        report = self._report(
            version=version,
            min_work_frequency=min_work_frequency,
            keyword_count=len(keyword_rows),
            mapped_keyword_count=mapped_keyword_count,
            excluded_keyword_count=excluded_keyword_count,
            omitted_keyword_count=omitted_keyword_count,
            canonical_before_frequency=len(groups),
            canonical_after_frequency=len(selected),
            singleton_canonical_count=singleton_canonical_count,
            singleton_canonical_names=sorted(singleton_canonical_names),
            included_canonical_names=sorted(selected),
            work_count=len(work_ids),
            association_count=len(association_rows),
            dry_run=bool(options["dry_run"]),
        )
        self._emit(str(options["evidence_json"]), report)
