"""Apply and publish the governed catalogue boundary offline."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Count

from catalogue.corpus import (
    ALLOWLIST_SLUGS,
    MAX_CATALOGUE_RELEASE_DATE,
    PLATFORM_ALLOWLIST,
    governed_works,
    is_valid_name,
)
from catalogue.models import AssetAttribution, CorpusVersion, GameWork, Platform, SourceRecord


GOVERN_CORPUS_LOCK_KEY = 902_020_201
RULESET_ID = "D-01-platform-slug+D-03-name-release-dlc-genre-date-max-2026"


def _ruleset_sha256() -> str:
    payload = {
        "ruleset": RULESET_ID,
        "platform_allowlist": PLATFORM_ALLOWLIST,
        "allowlist_slugs": sorted(ALLOWLIST_SLUGS),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _numeric_source_sort(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except (TypeError, ValueError):
        return (1, str(value))


def _checksum_for_governed() -> str:
    rows = list(
        SourceRecord.objects.filter(source="igdb", work__in_corpus=True).values_list(
            "source_id", "snapshot_sha256"
        )
    )
    rows.sort(key=lambda pair: _numeric_source_sort(pair[0]))
    digest = hashlib.sha256()
    for source_id, snapshot_sha256 in rows:
        digest.update(str(source_id).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(snapshot_sha256).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _pct(part: int, whole: int) -> float:
    return round((part / whole) * 100, 4) if whole else 0.0


class Command(BaseCommand):
    help = "Apply the D-01/D-03 governed catalogue boundary and emit citable evidence."
    stealth_options: tuple[str, ...] = ()
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        # Django reserves --version for the application version. This command
        # needs the plan's explicit corpus-version flag, so replace that base
        # action while retaining the documented CLI spelling.
        base_version_action = parser._option_string_actions.get("--version")
        if base_version_action is not None:
            parser._handle_conflict_resolve(None, [("--version", base_version_action)])
        parser.add_argument("--version", default=None)
        parser.add_argument("--evidence-json", default="-")

    def _default_version(self, ruleset_sha256: str) -> str:
        active = CorpusVersion.objects.filter(is_active=True).first()
        if active and active.ruleset_sha256 == ruleset_sha256:
            return active.version

        prefix = datetime.now(timezone.utc).strftime("%Y.%m")
        versions = CorpusVersion.objects.filter(version__startswith=f"{prefix}.").values_list(
            "version", flat=True
        )
        sequence = 0
        for value in versions:
            try:
                sequence = max(sequence, int(value.rsplit(".", 1)[1]))
            except (ValueError, IndexError):
                continue
        return f"{prefix}.{sequence + 1}"

    def _govern(self, version: str, ruleset_sha256: str) -> dict[str, Any]:
        source_works = list(
            GameWork.objects.filter(source_records__source="igdb")
            .distinct()
            .only("id", "original_title", "is_dlc", "first_release_date")
        )
        source_ids = [work.pk for work in source_works]
        valid_platform_ids = set(
            GameWork.objects.filter(
                pk__in=source_ids,
                releases__platform__slug__in=ALLOWLIST_SLUGS,
            )
            .distinct()
            .values_list("pk", flat=True)
        )
        valid_genre_ids = set(
            GameWork.objects.filter(pk__in=source_ids, genres__isnull=False)
            .distinct()
            .values_list("pk", flat=True)
        )

        valid_ids: list[Any] = []
        exclusion_reasons = Counter()
        for work in source_works:
            failed = {
                "invalid_name": not is_valid_name(work.original_title),
                "missing_allowlisted_platform": work.pk not in valid_platform_ids,
                "is_dlc": bool(work.is_dlc),
                "missing_genre": work.pk not in valid_genre_ids,
                "missing_first_release_date": work.first_release_date is None,
                "future_release_date": (
                    work.first_release_date is not None
                    and work.first_release_date > MAX_CATALOGUE_RELEASE_DATE
                ),
            }
            for reason, applies in failed.items():
                if applies:
                    exclusion_reasons[reason] += 1
            if not any(failed.values()):
                valid_ids.append(work.pk)

        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [GOVERN_CORPUS_LOCK_KEY])
        GameWork.objects.filter(pk__in=source_ids).update(in_corpus=False, corpus_version="")
        GameWork.objects.filter(pk__in=valid_ids).update(in_corpus=True, corpus_version=version)

        CorpusVersion.objects.filter(is_active=True).update(is_active=False)
        CorpusVersion.objects.update_or_create(
            version=version,
            defaults={
                "ruleset_sha256": ruleset_sha256,
                "is_active": True,
                "governed_count": len(valid_ids),
            },
        )
        return {
            "source_works": source_works,
            "valid_ids": valid_ids,
            "exclusion_reasons": exclusion_reasons,
        }

    def _quality_report(
        self,
        governed: Any,
        source_works: list[GameWork],
        exclusion_reasons: Counter,
    ) -> dict[str, Any]:
        total = governed.count()
        field_specs = {
            "total_rating": ("igdb", "FloatField", "Valor combinado vivo de IGDB."),
            "rating": ("igdb", "FloatField", "Rating medio de usuarios de IGDB."),
            "rating_count": ("igdb", "PositiveIntegerField", "Número de ratings de usuarios de IGDB."),
            "summary": ("igdb", "TextField", "Sinopsis textual de IGDB."),
            "cover": ("igdb", "URLField", "Portada hotlink o placeholder de primera parte."),
        }
        coverage: dict[str, Any] = {}
        work_field_names = {field.name for field in GameWork._meta.get_fields()}
        for field_name, (source, field_type, description) in field_specs.items():
            if field_name == "cover":
                present = governed.filter(assets__file_url__gt="").distinct().count()
            elif field_name not in work_field_names:
                present = 0
            elif field_name == "summary":
                present = governed.exclude(summary="").count()
            else:
                present = governed.filter(**{f"{field_name}__isnull": False}).count()
            coverage[field_name] = {
                "source": source,
                "type": field_type,
                "description": description,
                "present": present,
                "null_or_empty": total - present,
                "coverage_pct": _pct(present, total),
            }

        genres = {
            row["genres__slug"]: row["count"]
            for row in governed.values("genres__slug").annotate(count=Count("id", distinct=True))
            if row["genres__slug"]
        }
        platforms = {
            row["slug"]: row["count"]
            for row in Platform.objects.filter(
                slug__in=ALLOWLIST_SLUGS, releases__work__in=governed
            )
            .annotate(count=Count("releases__work", distinct=True))
            .values("slug", "count")
        }
        years = Counter(
            value.year for value in governed.values_list("first_release_date", flat=True) if value
        )
        unresolved = [
            {"slug": slug, "display_name": display_name, "igdb_id": igdb_id}
            for igdb_id, slug, display_name in PLATFORM_ALLOWLIST
            if not Platform.objects.filter(slug=slug).exists()
        ]
        return {
            "governed_count": total,
            "coverage": coverage,
            "genre_distribution": dict(sorted(genres.items())),
            "platform_distribution": dict(sorted(platforms.items())),
            "release_year_histogram": {
                str(year): count for year, count in sorted(years.items())
            },
            "exclusion_reason_histogram": {
                reason: exclusion_reasons.get(reason, 0)
                for reason in (
                    "invalid_name",
                    "missing_allowlisted_platform",
                    "is_dlc",
                    "missing_genre",
                    "missing_first_release_date",
                    "future_release_date",
                )
            },
            "unresolved_allowlist_slugs": unresolved,
            "source_work_count": len(source_works),
        }

    def _sampled_manifest(self, version: str, governed_count: int) -> list[dict[str, Any]]:
        records = list(
            SourceRecord.objects.filter(source="igdb", work__in_corpus=True)
            .select_related("work")
            .prefetch_related("work__genres", "work__releases__platform")
        )
        records.sort(key=lambda record: _numeric_source_sort(record.source_id))
        step = max(1, governed_count // 300)
        sampled = records[::step][:300]
        return [
            {
                "source_id": record.source_id,
                "canonical_slug": record.work.canonical_slug,
                "name": record.work.original_title,
                "genres": sorted(record.work.genres.values_list("slug", flat=True)),
                "platforms": sorted(
                    {
                        release.platform.slug
                        for release in record.work.releases.all()
                        if release.platform is not None
                    }
                ),
                "corpus_version": version,
            }
            for record in sampled
        ]

    def _evidence(self, version: str, state: dict[str, Any], ruleset_sha256: str) -> dict[str, Any]:
        governed = governed_works(version)
        checksum = _checksum_for_governed()
        quality = self._quality_report(
            governed, state["source_works"], state["exclusion_reasons"]
        )
        data_dictionary = {
            "name": {"type": "CharField", "source": "igdb", "nullable": False},
            "canonical_slug": {"type": "SlugField", "source": "derived", "nullable": False},
            "first_release_date": {"type": "DateField", "source": "igdb", "nullable": True},
            "summary": {"type": "TextField", "source": "igdb", "nullable": True},
            "total_rating": {"type": "FloatField", "source": "igdb", "nullable": True},
            "rating": {"type": "FloatField", "source": "igdb", "nullable": True},
            "rating_count": {"type": "PositiveIntegerField", "source": "igdb", "nullable": False},
            "in_corpus": {"type": "BooleanField", "source": "derived", "nullable": False},
            "corpus_version": {"type": "CharField", "source": "derived", "nullable": False},
            "genres": {"type": "ManyToMany", "source": "igdb", "nullable": True},
            "releases.platform": {"type": "ForeignKey", "source": "igdb", "nullable": True},
        }
        return {
            "corpus_version": version,
            "ruleset_sha256": ruleset_sha256,
            "checksum": checksum,
            "data_dictionary": data_dictionary,
            "quality_report": quality,
            "sampled_manifest": self._sampled_manifest(version, quality["governed_count"]),
        }

    def _emit_evidence(self, path: str, evidence: dict[str, Any]) -> None:
        blob = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob, ending="")
            return
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"evidence written: {target}")

    def handle(self, *args: Any, **options: Any) -> None:
        ruleset_sha256 = _ruleset_sha256()
        with transaction.atomic():
            version = options["version"] or self._default_version(ruleset_sha256)
            state = self._govern(version, ruleset_sha256)
            evidence = self._evidence(version, state, ruleset_sha256)
        self._emit_evidence(options["evidence_json"], evidence)
        if options["evidence_json"] != "-":
            self.stdout.write(
                f"governed corpus {version}: {evidence['quality_report']['governed_count']} works; "
                f"checksum {evidence['checksum']}"
            )
