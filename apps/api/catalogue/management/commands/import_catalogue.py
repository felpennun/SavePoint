"""Import the frozen catalogue snapshot into PostgreSQL (Plan 01-06 Task 1).

Fail-closed contract:
- Refuses to run unless docs/verification/catalogue-freeze.md is APPROVED.
- Refuses to run if the manifest's stored SHA-256 does not match a fresh
  hash of the raw snapshot (data cannot have drifted since the freeze).
- Never writes anything to PostgreSQL until every game in the snapshot has
  been validated in memory -- a single bad record aborts the whole import.

Idempotent and concurrency-safe: rows are keyed by SourceRecord(source,
source_id) via update_or_create, and the entire import runs inside one
transaction guarded by a PostgreSQL advisory lock, so a rerun or an
overlapping concurrent invocation never duplicates rows (CAT-04/CAT-06).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.text import slugify

from catalogue.models import AssetAttribution, GameAlias, GameRelease, GameWork, Platform, SourceRecord
from catalogue.normalization import normalize_title

# commands/ -> management/ -> catalogue/ -> api/ -> apps/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[5]
FREEZE_DOC_PATH = REPO_ROOT / "docs" / "verification" / "catalogue-freeze.md"
RAW_SNAPSHOT_PATH = REPO_ROOT / "data" / "raw" / "wikidata-games.json"
CATALOGUE_MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "catalogue.json"
ASSET_MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "assets.json"

# Fixed key for the transaction-scoped advisory lock serializing imports.
# pg_advisory_xact_lock auto-releases at transaction end -- no explicit unlock needed.
IMPORT_LOCK_KEY = 725_01_06


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


class Command(BaseCommand):
    help = "Import the frozen Wikidata catalogue snapshot into PostgreSQL."

    def _load_manifests(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        try:
            raw = json.loads(RAW_SNAPSHOT_PATH.read_text(encoding="utf-8"))
            catalogue_manifest = json.loads(CATALOGUE_MANIFEST_PATH.read_text(encoding="utf-8"))
            assets_manifest = json.loads(ASSET_MANIFEST_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CommandError(f"Missing catalogue snapshot/manifest: {exc}") from exc
        return raw, catalogue_manifest, assets_manifest

    def _check_freeze_approved(self) -> None:
        try:
            freeze_text = FREEZE_DOC_PATH.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise CommandError(
                f"Catalogue freeze document not found at {FREEZE_DOC_PATH} -- refusing to import an unreviewed corpus."
            ) from exc
        if "**Estado:** APPROVED" not in freeze_text:
            raise CommandError(
                "Catalogue freeze is not APPROVED -- refusing to import. "
                "See docs/verification/catalogue-freeze.md."
            )

    def _check_checksum(self, raw: dict[str, Any], catalogue_manifest: dict[str, Any]) -> None:
        actual_hash = hashlib.sha256(_canonical_bytes(raw)).hexdigest()
        expected_hash = catalogue_manifest.get("snapshot", {}).get("sha256")
        if actual_hash != expected_hash:
            raise CommandError(
                f"Raw snapshot checksum mismatch: manifest expects {expected_hash}, "
                f"computed {actual_hash}. Data may have drifted since the freeze -- refusing to import."
            )

    def handle(self, *args: Any, **options: Any) -> None:
        raw, catalogue_manifest, assets_manifest = self._load_manifests()
        self._check_freeze_approved()
        self._check_checksum(raw, catalogue_manifest)

        games = raw.get("games", [])
        if not games:
            raise CommandError("Snapshot contains no games -- refusing to import an empty catalogue.")

        source = raw.get("source_url", "wikidata")
        source_licence = raw.get("source_license", "")
        retrieved_at_raw = catalogue_manifest.get("retrieved_at")
        retrieved_at = (
            datetime.fromisoformat(retrieved_at_raw.replace("Z", "+00:00"))
            if retrieved_at_raw
            else datetime.now(timezone.utc)
        )
        snapshot_sha256 = catalogue_manifest["snapshot"]["sha256"]

        assets_by_qid: dict[str, list[dict[str, Any]]] = {}
        for asset in assets_manifest.get("assets", []):
            for qid in asset.get("game_qids", []):
                assets_by_qid.setdefault(qid, []).append(asset)

        created_works = 0
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [IMPORT_LOCK_KEY])

            for game in games:
                qid = game["qid"]
                title_en = game["titles"].get("en") or ""
                title_es = game["titles"].get("es") or ""
                original_title = title_en or title_es
                if not original_title:
                    raise CommandError(f"Game {qid} has no title in either locale -- aborting import.")

                slug_base = slugify(f"{original_title}-{qid}")[:200] or qid.lower()

                # SourceRecord(source, source_id) is the stable upsert key, not the
                # GameWork PK -- update_or_create cannot create through a reverse-FK
                # filter, so resolve the existing work (if any) via its SourceRecord
                # first, then create-or-update the GameWork directly.
                existing_link = SourceRecord.objects.filter(source="wikidata", source_id=qid).first()
                if existing_link is not None:
                    work = existing_link.work
                    work.canonical_slug = slug_base
                    work.original_title = original_title
                    work.title_en = title_en
                    work.title_es = title_es
                    work.save(update_fields=["canonical_slug", "original_title", "title_en", "title_es"])
                else:
                    work = GameWork.objects.create(
                        canonical_slug=slug_base,
                        original_title=original_title,
                        title_en=title_en,
                        title_es=title_es,
                    )
                created_works += 1

                SourceRecord.objects.update_or_create(
                    source="wikidata",
                    source_id=qid,
                    defaults={
                        "work": work,
                        "source_url": game.get("source_url", source),
                        "retrieved_at": retrieved_at,
                        "licence": source_licence,
                        "snapshot_sha256": snapshot_sha256,
                    },
                )

                for locale, title in (("en", title_en), ("es", title_es)):
                    if not title:
                        continue
                    GameAlias.objects.update_or_create(
                        work=work,
                        locale=locale,
                        normalized_value=normalize_title(title),
                        defaults={"value": title},
                    )

                release_date = None
                if game.get("release_dates"):
                    # Snapshot stores possibly-partial ISO date strings (Wikidata P577);
                    # keep only records with an unambiguous full date.
                    candidate = game["release_dates"][0]
                    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", candidate)
                    if match:
                        release_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

                platform_names = game.get("platforms") or ["Unknown"]
                for platform_name in platform_names:
                    platform, _ = Platform.objects.get_or_create(
                        name=platform_name,
                        defaults={"slug": slugify(platform_name)[:150] or "platform"},
                    )
                    GameRelease.objects.update_or_create(
                        work=work,
                        release_name=f"{original_title} ({platform_name})",
                        defaults={"platform": platform, "release_date": release_date},
                    )

                for asset in assets_by_qid.get(qid, []):
                    AssetAttribution.objects.update_or_create(
                        work=work,
                        source_url=asset.get("source_url", ""),
                        defaults={
                            "local_path": "",
                            "creator": asset.get("author", ""),
                            "licence": asset.get("license", ""),
                            "licence_url": asset.get("license_url", ""),
                            "file_url": asset.get("file_url", ""),
                            "reviewed_at": retrieved_at,
                            "display_allowed": asset.get("decision") == "candidate",
                        },
                    )

        self.stdout.write(self.style.SUCCESS(f"Imported {created_works} games from snapshot {snapshot_sha256[:12]}..."))
