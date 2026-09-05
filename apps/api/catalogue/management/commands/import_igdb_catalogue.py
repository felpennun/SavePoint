"""Real-scale, resumable IGDB primary-catalogue import (Plan 01.1-02, ADR-006).

Offline management command only -- never a request-time path (CAT-06 / OPS-03).
It extends the Wikidata ``import_catalogue`` idiom with the two changes the
230k+ row scale demands (01.1-RESEARCH.md Architecture Patterns 1-2):

1. **Resumable id-cursor pagination.** Pages are pulled with
   ``where game_type = 0 & id > <cursor>; sort id asc``. After every page's
   batch commits, the cursor is persisted on an ``IgdbImportRun`` row. A
   database trigger forbids the cursor from ever regressing, so an
   interrupted run resumes forward from real committed progress -- immune to
   IGDB deleting rows underneath a long pull.

2. **Batched transactions, one advisory lock per batch.** Each page is its
   own ``transaction.atomic()`` + ``pg_advisory_xact_lock`` scope, so a late
   failure rolls back only that page and never holds a lock for hours.

Idempotent: rows are keyed on ``SourceRecord(source="igdb", source_id=<igdb
numeric id>)`` via ``update_or_create``; a rerun after a complete pass
re-scans from id 0 and converges (same counts, same checksum).

Covers are hotlinked, not mirrored (ADR-006 D-06): a present cover becomes an
``AssetAttribution`` row with the ``images.igdb.com`` URL and
``display_allowed=True`` under the blanket IGDB/Twitch terms; a missing cover
becomes a fallback row (``file_url=""``, ``display_allowed=False``) so the
first-party placeholder renders. ``covers_present + covers_fallback`` always
equals the imported primary-work total.

No credential, token, or connection string is ever printed: the IGDB client
redacts every outbound string, and this command redacts any error summary it
persists or raises.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Count
from django.utils.text import slugify

from catalogue.igdb import IgdbClient, redact
from catalogue.models import (
    AssetAttribution,
    GameRelease,
    GameWork,
    Genre,
    IgdbImportRun,
    Platform,
    SourceRecord,
)

# Transaction-scoped advisory lock key -- distinct from the Wikidata importer's
# 725_01_06 so the two imports never contend with each other.
IMPORT_LOCK_KEY = 725_0101_02

IGDB_LICENCE = "IGDB / Twitch Developer Services Agreement (ADR-006)"
IGDB_TERMS_URL = "https://api-docs.igdb.com/"
COVER_TEMPLATE = "https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"


class MalformedRecord(Exception):
    """A single IGDB row is unusable -- rolls back only its batch."""


class Command(BaseCommand):
    help = "Resumable, batched import of the IGDB primary catalogue (game_type = 0)."

    # Lets tests inject a fake IGDB client via call_command(..., client=fake)
    # without exposing it as a CLI flag.
    stealth_options = ("client",)

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--query-identity", default="game_type=0")
        parser.add_argument("--where", default="game_type = 0")
        parser.add_argument("--page-size", type=int, default=500)
        parser.add_argument(
            "--max-batches",
            type=int,
            default=0,
            help="stop after N committed batches (0 = no limit); leaves the run resumable",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--evidence-json",
            default="",
            help="write the aggregate freeze evidence as JSON to this path ('-' = stdout)",
        )

    # -- helpers --------------------------------------------------------

    @staticmethod
    def _normalize(row: dict) -> dict:
        try:
            igdb_id = int(row["id"])
        except (KeyError, TypeError, ValueError):
            raise MalformedRecord("row has no usable integer id") from None
        name = str(row.get("name") or "").strip()
        if not name:
            raise MalformedRecord(f"row {igdb_id} has no name")

        slug_source = str(row.get("slug") or "").strip() or name
        base_slug = slugify(slug_source)[:200] or f"igdb-{igdb_id}"

        release_date = None
        ts = row.get("first_release_date")
        if isinstance(ts, (int, float)):
            release_date = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()

        genres = []
        for g in row.get("genres") or []:
            if isinstance(g, dict) and g.get("id") and g.get("name"):
                genres.append((int(g["id"]), str(g["name"]).strip()))
        platforms = []
        for p in row.get("platforms") or []:
            if isinstance(p, dict) and p.get("name"):
                platforms.append((str(p["name"]).strip()))

        cover_id = None
        cover = row.get("cover")
        if isinstance(cover, dict):
            cover_id = str(cover.get("image_id") or "").strip() or None
        cover_url = COVER_TEMPLATE.format(image_id=cover_id) if cover_id else ""

        return {
            "igdb_id": igdb_id,
            "name": name,
            "base_slug": base_slug,
            "source_url": str(row.get("url") or f"https://www.igdb.com/games/{slugify(slug_source)}"),
            "release_date": release_date,
            "genres": genres,
            "platforms": sorted(set(platforms)),
            "cover_url": cover_url,
        }

    @staticmethod
    def _record_digest(norm: dict) -> str:
        payload = {
            "igdb_id": norm["igdb_id"],
            "slug": norm["canonical_slug"],
            "title": norm["name"],
            "first_release_date": norm["release_date"].isoformat() if norm["release_date"] else None,
            "genres": sorted(gid for gid, _ in norm["genres"]),
            "platforms": norm["platforms"],
            "cover": norm["cover_url"],
        }
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    @staticmethod
    def _free_slug(base: str, igdb_id: int, own_work_id: Any) -> str:
        def is_taken(value: str) -> bool:
            qs = GameWork.objects.filter(canonical_slug=value)
            if own_work_id is not None:
                qs = qs.exclude(pk=own_work_id)
            return qs.exists()

        if not is_taken(base):
            return base
        candidate = f"{base[:180]}-{igdb_id}"
        suffix = 1
        while is_taken(candidate):
            candidate = f"{base[:170]}-{igdb_id}-{suffix}"
            suffix += 1
        return candidate

    def _genre_for(self, gid: int, gname: str) -> Genre:
        genre = Genre.objects.filter(igdb_id=gid).first()
        base = slugify(gname)[:120] or f"genre-{gid}"
        slug = base
        clash = Genre.objects.filter(slug=slug).exclude(igdb_id=gid).exists()
        if clash:
            slug = f"{base[:110]}-{gid}"
        if genre is None:
            return Genre.objects.create(igdb_id=gid, name=gname, slug=slug)
        if genre.name != gname or genre.slug != slug:
            genre.name = gname
            genre.slug = slug
            genre.save(update_fields=["name", "slug"])
        return genre

    def _upsert(self, norm: dict, now: datetime) -> str:
        existing = (
            SourceRecord.objects.select_related("work")
            .filter(source="igdb", source_id=str(norm["igdb_id"]))
            .first()
        )
        own_work_id = existing.work_id if existing else None
        norm["canonical_slug"] = self._free_slug(norm["base_slug"], norm["igdb_id"], own_work_id)
        digest = self._record_digest(norm)

        if existing is not None:
            work = existing.work
            work.canonical_slug = norm["canonical_slug"]
            work.original_title = norm["name"]
            work.title_en = norm["name"]
            work.is_dlc = False
            work.save(update_fields=["canonical_slug", "original_title", "title_en", "is_dlc"])
            outcome = "updated"
        else:
            work = GameWork.objects.create(
                canonical_slug=norm["canonical_slug"],
                original_title=norm["name"],
                title_en=norm["name"],
            )
            outcome = "created"

        SourceRecord.objects.update_or_create(
            source="igdb",
            source_id=str(norm["igdb_id"]),
            defaults={
                "work": work,
                "source_url": norm["source_url"],
                "retrieved_at": now,
                "licence": IGDB_LICENCE,
                "snapshot_sha256": digest,
            },
        )

        work.genres.set([self._genre_for(gid, gname) for gid, gname in norm["genres"]])

        if norm["platforms"]:
            for pname in norm["platforms"]:
                platform, _ = Platform.objects.get_or_create(
                    name=pname, defaults={"slug": slugify(pname)[:150] or "platform"}
                )
                GameRelease.objects.update_or_create(
                    work=work,
                    release_name=f"{norm['name']} ({pname})",
                    defaults={"platform": platform, "release_date": norm["release_date"]},
                )
        else:
            GameRelease.objects.update_or_create(
                work=work,
                release_name=norm["name"],
                defaults={"platform": None, "release_date": norm["release_date"]},
            )

        AssetAttribution.objects.update_or_create(
            work=work,
            source_url=IGDB_TERMS_URL,
            defaults={
                "local_path": "",
                "creator": "IGDB",
                "licence": IGDB_LICENCE,
                "licence_url": IGDB_TERMS_URL,
                "file_url": norm["cover_url"],
                "reviewed_at": now,
                "display_allowed": bool(norm["cover_url"]),
            },
        )
        return outcome

    # -- aggregate evidence -------------------------------------------------

    @staticmethod
    def _catalogue_checksum() -> str:
        rows = sorted(
            SourceRecord.objects.filter(source="igdb").values_list("source_id", "snapshot_sha256"),
            key=lambda pair: int(pair[0]),
        )
        digest = hashlib.sha256()
        for source_id, record_hash in rows:
            digest.update(source_id.encode("utf-8"))
            digest.update(b"\0")
            digest.update(record_hash.encode("utf-8"))
            digest.update(b"\n")
        return digest.hexdigest()

    def _build_evidence(self, run: IgdbImportRun, pass_start: int, created: int, updated: int) -> dict:
        igdb_works = GameWork.objects.filter(source_records__source="igdb").distinct()
        year_hist = Counter(
            d.year
            for d in GameRelease.objects.filter(
                work__source_records__source="igdb", release_date__isnull=False
            ).values_list("release_date", flat=True)
        )
        genres = [
            {"igdb_id": g.igdb_id, "name": g.name, "work_count": g.n}
            for g in Genre.objects.annotate(n=Count("works")).order_by("-n", "name")
        ]
        platforms = [
            {"name": p.name, "release_count": p.n}
            for p in Platform.objects.annotate(n=Count("releases")).order_by("-n", "name")[:20]
        ]

        ids = sorted(int(s) for s in SourceRecord.objects.filter(source="igdb").values_list("source_id", flat=True))
        step = max(1, len(ids) // 300)
        sample_ids = ids[::step][:300]
        sample_records = (
            SourceRecord.objects.filter(source="igdb", source_id__in=[str(i) for i in sample_ids])
            .select_related("work")
            .prefetch_related("work__genres", "work__releases")
        )
        manifest = []
        for rec in sorted(sample_records, key=lambda r: int(r.source_id)):
            work = rec.work
            years = [rel.release_date.year for rel in work.releases.all() if rel.release_date]
            manifest.append(
                {
                    "igdb_id": int(rec.source_id),
                    "canonical_slug": work.canonical_slug,
                    "title": work.original_title,
                    "year": min(years) if years else None,
                    "genres": sorted(gn.name for gn in work.genres.all()),
                    "cover_present": work.assets.filter(display_allowed=True).exclude(file_url="").exists(),
                }
            )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "query_identity": run.query_identity,
            "where": f"where {run.query_identity.replace('=', ' = ')};",
            "id_cursor_boundary": {
                "pass_start": pass_start,
                "last_committed": run.last_committed_igdb_id,
            },
            "eligible_count_live": run.eligible_count_live,
            "primary_works_imported": igdb_works.count(),
            "works_created_this_pass": created,
            "works_updated_this_pass": updated,
            "genres": genres,
            "platform_top20": platforms,
            "release_year_histogram": {str(y): n for y, n in sorted(year_hist.items())},
            "covers_present": run.covers_present,
            "covers_fallback": run.covers_fallback,
            "checksum_sha256": run.checksum,
            "status": run.status,
            "sampled_review_manifest": manifest,
        }

    def _emit_evidence(self, path: str, evidence: dict) -> None:
        blob = json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob)
            return
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"evidence written: {target}")

    # -- entrypoint --------------------------------------------------------

    def handle(self, *args: Any, **options: Any) -> None:
        client = options.get("client") or IgdbClient()
        query_identity = options["query_identity"]
        where = options["where"]
        page_size = options["page_size"]
        max_batches = options["max_batches"]
        dry_run = options["dry_run"]
        evidence_json = options["evidence_json"]

        now = datetime.now(timezone.utc)

        try:
            eligible = int(client.count_eligible(where))
        except Exception as exc:  # noqa: BLE001 - redact and surface, never leak
            raise CommandError(f"live eligible-count measurement failed: {redact(str(exc))}") from None

        if dry_run:
            cursor = 0
            seen = 0
            while True:
                rows = client.fetch_page(cursor, page_size=page_size, where=where)
                if not rows:
                    break
                for row in rows:
                    self._normalize(row)  # validates, writes nothing
                seen += len(rows)
                cursor = int(rows[-1]["id"])
            self.stderr.write(
                f"[dry-run] eligible={eligible} would process ~{seen} rows from id 0; no writes made"
            )
            return

        run, _ = IgdbImportRun.objects.get_or_create(
            source="igdb", query_identity=query_identity
        )

        resuming = run.status != IgdbImportRun.Status.COMPLETE and run.last_committed_igdb_id > 0
        pass_start = run.last_committed_igdb_id if resuming else 0

        run.status = IgdbImportRun.Status.RUNNING
        run.error_summary = ""
        run.eligible_count_live = eligible
        run.batches_committed = 0
        run.works_imported = 0
        run.works_updated = 0
        run.genres_seen = 0
        run.covers_present = 0
        run.covers_fallback = 0
        run.save()

        self.stderr.write(
            f"IGDB import: eligible={eligible} identity={query_identity!r} "
            f"{'resuming from id ' + str(pass_start) if resuming else 'fresh pass from id 0'}"
        )

        cursor = pass_start
        created_total = 0
        updated_total = 0
        batches = 0
        try:
            while True:
                rows = client.fetch_page(cursor, page_size=page_size, where=where)
                if not rows:
                    break
                with transaction.atomic():
                    with connection.cursor() as cur:
                        cur.execute("SELECT pg_advisory_xact_lock(%s)", [IMPORT_LOCK_KEY])
                    batch_last_id = cursor
                    batch_created = 0
                    batch_updated = 0
                    for row in rows:
                        try:
                            norm = self._normalize(row)
                        except MalformedRecord as exc:
                            raise CommandError(
                                f"malformed IGDB record in batch after id {cursor}: {redact(str(exc))}"
                            ) from None
                        outcome = self._upsert(norm, now)
                        if outcome == "created":
                            batch_created += 1
                        else:
                            batch_updated += 1
                        batch_last_id = max(batch_last_id, norm["igdb_id"])

                    run.last_committed_igdb_id = max(run.last_committed_igdb_id, batch_last_id)
                    run.batches_committed = batches + 1
                    run.works_imported += batch_created
                    run.works_updated += batch_updated
                    run.save(
                        update_fields=[
                            "last_committed_igdb_id",
                            "batches_committed",
                            "works_imported",
                            "works_updated",
                            "updated_at",
                        ]
                    )
                created_total += batch_created
                updated_total += batch_updated
                batches += 1
                cursor = batch_last_id
                if max_batches and batches >= max_batches:
                    self.stderr.write(
                        f"stopped after {batches} batches (--max-batches); run stays resumable at id {cursor}"
                    )
                    run.status = IgdbImportRun.Status.INTERRUPTED
                    run.save(update_fields=["status", "updated_at"])
                    return
        except CommandError as exc:
            run.refresh_from_db(fields=["last_committed_igdb_id"])
            run.status = IgdbImportRun.Status.FAILED
            run.error_summary = redact(str(exc))[:2000]
            run.save(update_fields=["status", "error_summary", "updated_at"])
            raise
        except Exception as exc:  # noqa: BLE001 - redact anything else and fail closed
            run.refresh_from_db(fields=["last_committed_igdb_id"])
            run.status = IgdbImportRun.Status.FAILED
            run.error_summary = redact(str(exc))[:2000]
            run.save(update_fields=["status", "error_summary", "updated_at"])
            raise CommandError(f"IGDB import aborted: {redact(str(exc))}") from None

        # Completed pass: recompute aggregates from database truth so a
        # resumed-to-completion run and a single clean run are identical.
        igdb_works = GameWork.objects.filter(source_records__source="igdb").distinct()
        total_works = igdb_works.count()
        covers_present = (
            AssetAttribution.objects.filter(work__in=igdb_works)
            .exclude(file_url="")
            .filter(display_allowed=True)
            .count()
        )
        run.works_imported = total_works
        run.works_updated = updated_total
        run.covers_present = covers_present
        run.covers_fallback = total_works - covers_present
        run.genres_seen = Genre.objects.count()
        run.checksum = self._catalogue_checksum()
        run.status = IgdbImportRun.Status.COMPLETE
        run.save()

        self.stderr.write(
            self.style.SUCCESS(
                f"IGDB import complete: {total_works} primary works "
                f"(+{created_total} new / ~{updated_total} refreshed this pass), "
                f"covers {covers_present} present / {run.covers_fallback} fallback, "
                f"checksum {run.checksum[:12]}..., eligible_live={eligible}"
            )
        )

        if evidence_json:
            self._emit_evidence(evidence_json, self._build_evidence(run, pass_start, created_total, updated_total))
