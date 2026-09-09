"""Freeze raw IGDB PopScore primitives for one governed corpus version."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from catalogue.corpus import governed_works
from catalogue.igdb import IgdbClient, redact
from catalogue.models import CorpusPopularitySnapshot, CorpusVersion, SourceRecord
from catalogue.popularity import (
    IGDB_ENGAGEMENT_TYPES,
    POPSCORE_FORMULA_VERSION,
    POPSCORE_WEIGHTS,
)


SNAPSHOT_LOCK_KEY = 902_020_203


def _payload_sha256(payload: dict[str, Any]) -> str:
    def encode(value: object) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        raise TypeError(f"unsupported snapshot value: {type(value)!r}")

    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=encode,
        ).encode("utf-8")
    ).hexdigest()


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if not math.isfinite(value):
        return None
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


class Command(BaseCommand):
    help = "Freeze raw IGDB PopScore primitives for an active governed corpus version."
    requires_system_checks: list = []
    stealth_options = ("client",)

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--page-size", type=int, default=500)
        parser.add_argument("--evidence-json", default="-")

    def _emit(self, path: str, payload: dict[str, Any]) -> None:
        blob = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob, ending="")
            return
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"evidence written: {target}")

    @staticmethod
    def _type_index(rows: list[dict]) -> dict[int, dict[str, str]]:
        types: dict[int, dict[str, str]] = {}
        for row in rows:
            try:
                type_id = int(row["id"])
            except (KeyError, TypeError, ValueError):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            types[type_id] = {
                "name": name,
                "external_source": str(row.get("external_popularity_source") or "").strip(),
            }
        return types

    @staticmethod
    def _governed_igdb_work_ids(version: str) -> dict[int, object]:
        records = SourceRecord.objects.filter(
            source="igdb", work__in=governed_works(version)
        ).values_list("source_id", "work_id")
        result: dict[int, object] = {}
        for source_id, work_id in records:
            try:
                result[int(source_id)] = work_id
            except (TypeError, ValueError):
                continue
        return result

    @staticmethod
    def _snapshot_sha256(version: str) -> str:
        rows = list(
            CorpusPopularitySnapshot.objects.filter(corpus_version=version).values_list(
                "work_id",
                "popularity_type_id",
                "value",
                "normalised_value",
                "calculated_at",
                "source_updated_at",
                "payload_sha256",
            )
        )
        normalized = sorted(
            (
                str(work_id),
                type_id,
                value,
                normalised_value,
                calculated_at.isoformat() if calculated_at else None,
                source_updated_at.isoformat() if source_updated_at else None,
                payload_sha256,
            )
            for (
                work_id,
                type_id,
                value,
                normalised_value,
                calculated_at,
                source_updated_at,
                payload_sha256,
            ) in rows
        )
        return _payload_sha256({"corpus_version": version, "primitives": normalized})

    @staticmethod
    def _engagement_type_ids(popularity_types: dict[int, dict[str, str]]) -> dict[str, int]:
        by_name = {entry["name"].casefold(): type_id for type_id, entry in popularity_types.items()}
        missing = [name for name in IGDB_ENGAGEMENT_TYPES if name.casefold() not in by_name]
        if missing:
            raise CommandError(
                "PopScore type dictionary does not expose required IGDB engagement types: "
                + ", ".join(missing)
            )
        return {name: by_name[name.casefold()] for name in IGDB_ENGAGEMENT_TYPES}

    @staticmethod
    def _normalise_engagement(version: str, type_ids: dict[str, int]) -> dict[str, int]:
        """Apply log1p plus average-rank percentile per frozen primitive."""

        counts: dict[str, int] = {}
        for name, type_id in type_ids.items():
            rows = list(
                CorpusPopularitySnapshot.objects.filter(
                    corpus_version=version,
                    popularity_type_id=type_id,
                    value__gte=0,
                ).values_list("id", "value")
            )
            CorpusPopularitySnapshot.objects.filter(
                corpus_version=version, popularity_type_id=type_id
            ).update(normalised_value=None)
            counts[name] = len(rows)
            if not rows:
                continue
            ranked = sorted(
                (math.log1p(value), str(snapshot_id), snapshot_id)
                for snapshot_id, value in rows
            )
            denominator = len(ranked) - 1
            start = 0
            while start < len(ranked):
                end = start + 1
                while end < len(ranked) and ranked[end][0] == ranked[start][0]:
                    end += 1
                normalised = 0.5 if denominator == 0 else (start + end - 1) / (2 * denominator)
                CorpusPopularitySnapshot.objects.filter(
                    id__in=[row[2] for row in ranked[start:end]]
                ).update(normalised_value=normalised)
                start = end
        return counts

    def handle(self, *args: Any, **options: Any) -> None:
        version = options["corpus_version"]
        corpus_version = CorpusVersion.objects.filter(version=version).first()
        if corpus_version is None:
            raise CommandError(f"unknown corpus version: {version}")
        if not corpus_version.is_active and not options["force"]:
            raise CommandError(
                f"corpus version {version} is not active; pass --force to snapshot it"
            )
        page_size = max(1, min(500, int(options["page_size"])))
        client = options.get("client") or IgdbClient()

        try:
            popularity_types = self._type_index(client.fetch_popularity_types())
        except Exception as exc:  # noqa: BLE001 - redact a provider error before output
            raise CommandError(f"PopScore type lookup failed: {redact(str(exc))}") from None
        if not popularity_types:
            raise CommandError("PopScore type lookup returned no usable primitive types")
        engagement_type_ids = self._engagement_type_ids(popularity_types)

        governed_ids = self._governed_igdb_work_ids(version)
        if not governed_ids:
            raise CommandError(f"corpus version {version} has no governed IGDB works")

        inserted = 0
        existing = 0
        ignored_outside_corpus = 0
        seen_relevant = 0
        cursor = 0
        retrieved_at = datetime.now(timezone.utc)
        try:
            with transaction.atomic():
                with connection.cursor() as database_cursor:
                    database_cursor.execute("SELECT pg_advisory_xact_lock(%s)", [SNAPSHOT_LOCK_KEY])
                while True:
                    rows = client.fetch_popularity_page(cursor, page_size=page_size)
                    if not rows:
                        break
                    next_cursor = cursor
                    for row in rows:
                        try:
                            primitive_id = int(row["id"])
                            igdb_game_id = int(row["game_id"])
                            type_id = int(row["popularity_type"])
                            value = float(row["value"])
                        except (KeyError, TypeError, ValueError):
                            continue
                        next_cursor = max(next_cursor, primitive_id)
                        if not math.isfinite(value):
                            continue
                        work_id = governed_ids.get(igdb_game_id)
                        if work_id is None:
                            ignored_outside_corpus += 1
                            continue
                        type_info = popularity_types.get(type_id)
                        if type_info is None:
                            raise CommandError(
                                f"PopScore primitive for IGDB game {igdb_game_id} has unknown type {type_id}"
                            )
                        seen_relevant += 1
                        payload = {
                            "igdb_game_id": igdb_game_id,
                            "popularity_type_id": type_id,
                            "value": value,
                            "calculated_at": _timestamp(row.get("calculated_at")),
                            "source_updated_at": _timestamp(row.get("updated_at")),
                            "checksum": str(row.get("checksum") or ""),
                        }
                        snapshot, created = CorpusPopularitySnapshot.objects.get_or_create(
                            work_id=work_id,
                            corpus_version=version,
                            popularity_type_id=type_id,
                            defaults={
                                "popularity_type_name": type_info["name"],
                                "external_source": type_info["external_source"],
                                "value": value,
                                "calculated_at": payload["calculated_at"],
                                "source_updated_at": payload["source_updated_at"],
                                "retrieved_at": retrieved_at,
                                "payload_sha256": _payload_sha256(payload),
                            },
                        )
                        inserted += int(created)
                        existing += int(not created)
                    if next_cursor <= cursor:
                        raise CommandError("PopScore cursor did not advance; refusing an incomplete snapshot")
                    cursor = next_cursor
                normalised_counts = self._normalise_engagement(version, engagement_type_ids)
        except CommandError:
            raise
        except Exception as exc:  # noqa: BLE001 - provider errors must never expose credentials
            raise CommandError(f"PopScore snapshot failed: {redact(str(exc))}") from None

        payload = {
            "corpus_version": version,
            "source": "igdb_popularity_primitives",
            "captured_at": retrieved_at.isoformat(),
            "governed_igdb_work_count": len(governed_ids),
            "primitive_types": popularity_types,
            "engagement_types": engagement_type_ids,
            "normalised_observations_by_type": normalised_counts,
            "relevant_primitives_seen": seen_relevant,
            "snapshots_inserted": inserted,
            "snapshots_already_immutable": existing,
            "primitives_outside_governed_corpus": ignored_outside_corpus,
            "snapshot_sha256": self._snapshot_sha256(version),
            "composition": {
                "id": POPSCORE_FORMULA_VERSION,
                "required_types": list(IGDB_ENGAGEMENT_TYPES),
                "normalisation": "log1p then average-rank percentile within each frozen primitive type",
                "weights": POPSCORE_WEIGHTS,
                "formula": "weighted sum of the four normalised primitive values",
                "missing_policy": "no composition when any required primitive is absent",
            },
            "limitation": (
                "The normalised composition is stored for traceability only. No recommender "
                "weight is active until a versioned algorithm variant is approved."
            ),
        }
        self._emit(options["evidence_json"], payload)
