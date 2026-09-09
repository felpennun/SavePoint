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
from django.db import IntegrityError, connection, transaction
from django.db.models import Count
from django.utils.text import slugify

from catalogue.igdb import IgdbClient, redact
from catalogue.models import (
    AssetAttribution,
    Developer,
    Franchise,
    GameAlias,
    GameMode,
    GameRelease,
    GameWork,
    Genre,
    IgdbImportRun,
    Keyword,
    Platform,
    PlayerPerspective,
    SourceRecord,
    Theme,
)
from catalogue.normalization import normalize_title

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

    # Offline data command: skip the system-check pass so `--evidence-json -`
    # keeps stdout to pure JSON (no "System check identified no issues" line).
    requires_system_checks: list = []

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
            # A corrupt/out-of-range epoch value (huge -> OverflowError, deep
            # negative -> OSError on some platforms, non-finite -> ValueError)
            # must degrade to "no date", never raise past the per-row skip and
            # mark the whole resumable run FAILED (repo-review 2026-09-06 M-04).
            try:
                release_date = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
            except (ValueError, OverflowError, OSError):
                release_date = None

        total_rating = None
        raw_total_rating = row.get("total_rating")
        if isinstance(raw_total_rating, (int, float)):
            total_rating = round(float(raw_total_rating), 4)

        user_rating = None
        raw_rating = row.get("rating")
        if isinstance(raw_rating, (int, float)):
            user_rating = round(float(raw_rating), 4)

        rating_count = row.get("rating_count")
        if not isinstance(rating_count, int) or isinstance(rating_count, bool) or rating_count < 0:
            rating_count = None
        total_rating_count = row.get("total_rating_count")
        if (
            not isinstance(total_rating_count, int)
            or isinstance(total_rating_count, bool)
            or total_rating_count < 0
        ):
            total_rating_count = None
        summary = str(row.get("summary") or "").strip()
        title_en = str(row.get("title_en") or name).strip()

        alternative_names = []
        for alias in row.get("alternative_names") or []:
            if isinstance(alias, dict):
                value = str(alias.get("name") or "").strip()
            else:
                value = str(alias or "").strip()
            if value:
                alternative_names.append(value)

        franchises = []
        for item in row.get("franchises") or []:
            if not isinstance(item, dict):
                continue
            try:
                franchise_id = int(item["id"])
            except (KeyError, TypeError, ValueError):
                continue
            franchise_name = str(item.get("name") or "").strip()
            if franchise_name:
                franchises.append((franchise_id, franchise_name))
        collections = [
            str(item.get("name") or "").strip()
            for item in row.get("collections") or []
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
        involved_companies = []
        for item in row.get("involved_companies") or []:
            if not isinstance(item, dict):
                continue
            company = item.get("company") or {}
            company_name = str(company.get("name") or "").strip() if isinstance(company, dict) else ""
            try:
                company_id = int(company["id"])
            except (KeyError, TypeError, ValueError):
                continue
            if company_name and bool(item.get("developer")):
                involved_companies.append(
                    {"id": company_id, "name": company_name}
                )

        genres = []
        for g in row.get("genres") or []:
            if isinstance(g, dict) and g.get("id") and g.get("name"):
                genres.append((int(g["id"]), str(g["name"]).strip()))
        platforms = []
        for p in row.get("platforms") or []:
            if isinstance(p, dict) and p.get("name"):
                platforms.append((str(p["name"]).strip()))

        # Additive classification facets: parsed here but deliberately kept
        # out of _record_digest so attaching them never moves the frozen
        # content checksum. ``name`` is clamped to each model's column width.
        def _id_name_pairs(raw: Any, limit: int) -> list[tuple[int, str]]:
            pairs: set[tuple[int, str]] = set()
            for item in raw or []:
                if not isinstance(item, dict):
                    continue
                try:
                    item_id = int(item["id"])
                except (KeyError, TypeError, ValueError):
                    continue
                item_name = str(item.get("name") or "").strip()[:limit]
                if item_name:
                    pairs.add((item_id, item_name))
            return sorted(pairs)

        themes = _id_name_pairs(row.get("themes"), 120)
        player_perspectives = _id_name_pairs(row.get("player_perspectives"), 120)
        game_modes = _id_name_pairs(row.get("game_modes"), 120)
        keywords = _id_name_pairs(row.get("keywords"), 200)

        cover_id = None
        cover = row.get("cover")
        if isinstance(cover, dict):
            cover_id = str(cover.get("image_id") or "").strip() or None
        cover_url = COVER_TEMPLATE.format(image_id=cover_id) if cover_id else ""

        return {
            "igdb_id": igdb_id,
            "name": name,
            "title_en": title_en,
            "base_slug": base_slug,
            "source_url": str(row.get("url") or f"https://www.igdb.com/games/{slugify(slug_source)}"),
            "release_date": release_date,
            "total_rating": total_rating,
            "rating": user_rating,
            "rating_count": rating_count,
            "total_rating_count": total_rating_count,
            "summary": summary,
            "alternative_names": sorted(set(alternative_names)),
            "franchises": sorted(set(franchises)),
            "collections": sorted(set(collections)),
            "developers": sorted(
                {(item["id"], item["name"]) for item in involved_companies}
            ),
            "genres": genres,
            "platforms": sorted(set(platforms)),
            "themes": themes,
            "player_perspectives": player_perspectives,
            "game_modes": game_modes,
            "keywords": keywords,
            "cover_url": cover_url,
        }

    @staticmethod
    def _record_digest(norm: dict) -> str:
        payload = {
            "igdb_id": norm["igdb_id"],
            "slug": norm["canonical_slug"],
            "title": norm["name"],
            "title_en": norm["title_en"],
            "first_release_date": norm["release_date"].isoformat() if norm["release_date"] else None,
            "total_rating": norm["total_rating"],
            "rating": norm["rating"],
            "rating_count": norm["rating_count"],
            "total_rating_count": norm["total_rating_count"],
            "summary": norm["summary"],
            "alternative_names": norm["alternative_names"],
            "franchises": norm["franchises"],
            "collections": norm["collections"],
            "developers": norm["developers"],
            "genres": sorted(gid for gid, _ in norm["genres"]),
            "platforms": norm["platforms"],
            "cover": norm["cover_url"],
            # themes / player_perspectives / game_modes / keywords are
            # intentionally absent: they are additive, non-governed enrichment
            # and folding them in would move every record digest (and the
            # catalogue content checksum pinned in the freeze evidence) on the
            # first pass that attaches them.
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

    @staticmethod
    def _platform_for(pname: str) -> Platform:
        """Reconcile a platform on its natural key against ANY existing row,
        whatever its origin (Wikidata or IGDB).

        The Wikidata importer keys platforms on ``name`` and slugifies its
        (often lowercase) label; IGDB spells the same hardware differently in
        case/punctuation ("Web browser" vs Wikidata's "web browser"), so two
        spellings collapse to one ``slug``. A blind ``get_or_create(name=...)``
        then misses the pre-existing Wikidata row and its INSERT trips
        ``catalogue_platform_slug_key``, poisoning the whole batch transaction
        and aborting the run. Match on ``slug`` first, then ``name``; only
        INSERT when neither exists, inside a savepoint so even a concurrent
        writer racing the same slug cannot abort the batch.
        """
        slug = slugify(pname)[:150] or "platform"
        platform = (
            Platform.objects.filter(slug=slug).first()
            or Platform.objects.filter(name=pname).first()
        )
        if platform is not None:
            return platform
        try:
            with transaction.atomic():
                return Platform.objects.create(name=pname, slug=slug)
        except IntegrityError:
            existing = (
                Platform.objects.filter(slug=slug).first()
                or Platform.objects.filter(name=pname).first()
            )
            if existing is None:
                raise
            return existing

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

    @staticmethod
    def _facet_slug(base: str, igdb_id: int, model: Any) -> str:
        slug = slugify(base)[:200] or f"igdb-{igdb_id}"
        if model.objects.filter(slug=slug).exclude(igdb_id=igdb_id).exists():
            slug = f"{slug[:180]}-{igdb_id}"
        return slug

    def _franchise_for(self, franchise_id: int, name: str) -> Franchise:
        slug = self._facet_slug(name, franchise_id, Franchise)
        franchise, _ = Franchise.objects.update_or_create(
            igdb_id=franchise_id,
            defaults={"name": name, "slug": slug},
        )
        return franchise

    def _developer_for(self, developer_id: int, name: str) -> Developer:
        slug = self._facet_slug(name, developer_id, Developer)
        developer, _ = Developer.objects.update_or_create(
            igdb_id=developer_id,
            defaults={"name": name, "slug": slug},
        )
        return developer

    def _classification_facet_for(self, model: Any, igdb_id: int, name: str) -> Any:
        """Reconcile a Theme/PlayerPerspective/GameMode/Keyword row on its
        stable IGDB id, minimising write churn on a 330k-work rescan: create
        when missing, and only UPDATE when the display name or slug actually
        changed."""
        obj = model.objects.filter(igdb_id=igdb_id).first()
        slug = self._facet_slug(name, igdb_id, model)
        if obj is None:
            return model.objects.create(igdb_id=igdb_id, name=name, slug=slug)
        if obj.name != name or obj.slug != slug:
            obj.name = name
            obj.slug = slug
            obj.save(update_fields=["name", "slug"])
        return obj

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
            update_fields: list[str] = []
            if not work.title_en and norm["title_en"]:
                work.title_en = norm["title_en"]
                update_fields.append("title_en")
            for field, normalized_field in (
                ("first_release_date", "release_date"),
                ("total_rating", "total_rating"),
                ("rating", "rating"),
                ("rating_count", "rating_count"),
                ("total_rating_count", "total_rating_count"),
            ):
                if getattr(work, field) is None and norm[normalized_field] is not None:
                    setattr(work, field, norm[normalized_field])
                    update_fields.append(field)
            if not work.summary and norm["summary"]:
                work.summary = norm["summary"]
                update_fields.append("summary")
            if update_fields:
                work.save(update_fields=update_fields)
            outcome = "updated"
        else:
            work = GameWork.objects.create(
                canonical_slug=norm["canonical_slug"],
                original_title=norm["name"],
                title_en=norm["title_en"],
                first_release_date=norm["release_date"],
                total_rating=norm["total_rating"],
                rating=norm["rating"],
                rating_count=norm["rating_count"],
                total_rating_count=norm["total_rating_count"],
                summary=norm["summary"],
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

        if norm["genres"]:
            work.genres.add(*[self._genre_for(gid, gname) for gid, gname in norm["genres"]])
        if norm["franchises"]:
            work.franchises.add(
                *[self._franchise_for(franchise_id, name) for franchise_id, name in norm["franchises"]]
            )
        if norm["developers"]:
            work.developers.add(
                *[self._developer_for(developer_id, name) for developer_id, name in norm["developers"]]
            )
        # Additive classification facets. ``.add()`` is idempotent and only
        # ever inserts join rows -- it never clears an existing membership, so
        # a facet IGDB later stops returning for a work is preserved, matching
        # the importer's "reimports enrich, never erase" contract.
        for facet_key, facet_model, manager_name in (
            ("themes", Theme, "themes"),
            ("player_perspectives", PlayerPerspective, "player_perspectives"),
            ("game_modes", GameMode, "game_modes"),
            ("keywords", Keyword, "keywords"),
        ):
            if norm[facet_key]:
                getattr(work, manager_name).add(
                    *[
                        self._classification_facet_for(facet_model, facet_id, facet_name)
                        for facet_id, facet_name in norm[facet_key]
                    ]
                )

        # IGDB is the owner of the English alias set. The legacy Wikidata
        # importer also uses locale=en/es but its Spanish aliases are kept;
        # no unmarked alias is deleted outside the English import boundary.
        desired_aliases: dict[str, str] = {}
        for value in [norm["name"], *norm["alternative_names"]]:
            normalized = normalize_title(value)
            if normalized:
                desired_aliases.setdefault(normalized, value)
        title_en = str(norm.get("title_en") or "").strip()
        if title_en and normalize_title(title_en) not in desired_aliases:
            desired_aliases[normalize_title(title_en)] = title_en
        GameAlias.objects.bulk_create(
            [
                GameAlias(work=work, locale="en", value=value, normalized_value=normalized)
                for normalized, value in desired_aliases.items()
            ],
            ignore_conflicts=True,
            batch_size=5000,
        )
        for normalized, value in desired_aliases.items():
            GameAlias.objects.filter(
                work=work, locale="en", normalized_value=normalized
            ).update(value=value)
        written_release_names: list[str] = []
        if norm["platforms"]:
            for pname in norm["platforms"]:
                platform = self._platform_for(pname)
                release_name = f"{norm['name']} ({pname})"
                written_release_names.append(release_name)
                release, created = GameRelease.objects.get_or_create(
                    work=work,
                    release_name=release_name,
                    defaults={"platform": platform, "release_date": norm["release_date"]},
                )
                if not created:
                    release_updates: list[str] = []
                    if release.platform_id is None:
                        release.platform = platform
                        release_updates.append("platform")
                    if release.release_date is None and norm["release_date"] is not None:
                        release.release_date = norm["release_date"]
                        release_updates.append("release_date")
                    if release_updates:
                        release.save(update_fields=release_updates)
        elif existing is None:
            written_release_names.append(norm["name"])
            GameRelease.objects.update_or_create(
                work=work,
                release_name=norm["name"],
                defaults={"platform": None, "release_date": norm["release_date"]},
            )

        # Keep prior releases even if an upstream title or platform label
        # changes. Reimports enrich the existing catalogue; they never erase
        # previously observed source or user data.
        if norm["cover_url"] or existing is None:
            asset, created = AssetAttribution.objects.get_or_create(
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
            if not created and not asset.file_url and norm["cover_url"]:
                asset.file_url = norm["cover_url"]
                asset.reviewed_at = now
                asset.display_allowed = True
                asset.save(update_fields=["file_url", "reviewed_at", "display_allowed"])
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

    def _build_evidence(
        self, run: IgdbImportRun, pass_start: int, created: int, updated: int, skipped: int = 0
    ) -> dict:
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

        # Additive classification facet coverage: how many distinct values
        # exist and how many IGDB works carry at least one. Evidence only --
        # these facets are outside the governed corpus and the checksum.
        classification_facets = {
            "themes": {
                "distinct_values": Theme.objects.count(),
                "works_with_any": igdb_works.filter(themes__isnull=False).distinct().count(),
                "top_values": [
                    {"igdb_id": t.igdb_id, "name": t.name, "work_count": t.n}
                    for t in Theme.objects.annotate(n=Count("works")).order_by("-n", "name")[:25]
                ],
            },
            "player_perspectives": {
                "distinct_values": PlayerPerspective.objects.count(),
                "works_with_any": igdb_works.filter(player_perspectives__isnull=False)
                .distinct()
                .count(),
                "top_values": [
                    {"igdb_id": p.igdb_id, "name": p.name, "work_count": p.n}
                    for p in PlayerPerspective.objects.annotate(n=Count("works")).order_by(
                        "-n", "name"
                    )
                ],
            },
            "game_modes": {
                "distinct_values": GameMode.objects.count(),
                "works_with_any": igdb_works.filter(game_modes__isnull=False).distinct().count(),
                "top_values": [
                    {"igdb_id": m.igdb_id, "name": m.name, "work_count": m.n}
                    for m in GameMode.objects.annotate(n=Count("works")).order_by("-n", "name")
                ],
            },
            "keywords": {
                "distinct_values": Keyword.objects.count(),
                "works_with_any": igdb_works.filter(keywords__isnull=False).distinct().count(),
                "top_values": [
                    {"igdb_id": k.igdb_id, "name": k.name, "work_count": k.n}
                    for k in Keyword.objects.annotate(n=Count("works")).order_by("-n", "name")[:50]
                ],
            },
        }

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
            "malformed_skipped_this_pass": skipped,
            "genres": genres,
            "platform_top20": platforms,
            "classification_facets": classification_facets,
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
            skipped = 0
            while True:
                rows = client.fetch_page(cursor, page_size=page_size, where=where)
                if not rows:
                    break
                for row in rows:
                    try:
                        self._normalize(row)  # validates, writes nothing
                    except MalformedRecord:
                        skipped += 1
                seen += len(rows)
                cursor = int(rows[-1]["id"])
            self.stderr.write(
                f"[dry-run] eligible={eligible} would process ~{seen} rows from id 0 "
                f"({skipped} malformed skipped); no writes made"
            )
            return

        run, _ = IgdbImportRun.objects.get_or_create(
            source="igdb", query_identity=query_identity
        )

        # Resume from the CURRENT pass's own cursor, not the monotonic
        # high-water mark. After a COMPLETE pass a chunked rerun (--max-batches)
        # restarts at 0; earlier this reused last_committed_igdb_id, so a rerun
        # that was then interrupted and resumed would jump straight back to the
        # stale high-water mark and skip every id below it while still
        # finalizing COMPLETE with a fresh checksum -- a false converged pass
        # (repo-review 2026-09-06 H-02).
        resuming = run.status != IgdbImportRun.Status.COMPLETE and run.pass_cursor > 0
        pass_start = run.pass_cursor if resuming else 0

        run.status = IgdbImportRun.Status.RUNNING
        run.error_summary = ""
        run.eligible_count_live = eligible
        run.pass_cursor = pass_start
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
        skipped_total = 0
        batches = 0
        try:
            while True:
                rows = client.fetch_page(cursor, page_size=page_size, where=where)
                if not rows:
                    break
                page_last_id = max(int(r.get("id", cursor) or cursor) for r in rows)
                with transaction.atomic():
                    with connection.cursor() as cur:
                        cur.execute("SELECT pg_advisory_xact_lock(%s)", [IMPORT_LOCK_KEY])
                    batch_last_id = cursor
                    batch_created = 0
                    batch_updated = 0
                    batch_skipped = 0
                    for row in rows:
                        try:
                            norm = self._normalize(row)
                        except MalformedRecord as exc:
                            # One unusable row must never wedge a 300k resumable
                            # import: skip and count it, keep the batch alive.
                            batch_skipped += 1
                            self.stderr.write(f"  skipped malformed record: {redact(str(exc))}")
                            continue
                        outcome = self._upsert(norm, now)
                        if outcome == "created":
                            batch_created += 1
                        else:
                            batch_updated += 1
                        batch_last_id = max(batch_last_id, norm["igdb_id"])

                    # Advance past the whole page even if its trailing rows were
                    # all skipped, so the cursor cannot stall on a poison tail.
                    batch_last_id = max(batch_last_id, page_last_id)

                    # last_committed_igdb_id is the non-regressing evidence
                    # boundary; pass_cursor tracks this pass and is what a
                    # resume restarts from (H-02).
                    run.last_committed_igdb_id = max(run.last_committed_igdb_id, batch_last_id)
                    run.pass_cursor = batch_last_id
                    run.batches_committed = batches + 1
                    run.works_imported += batch_created
                    run.works_updated += batch_updated
                    run.save(
                        update_fields=[
                            "last_committed_igdb_id",
                            "pass_cursor",
                            "batches_committed",
                            "works_imported",
                            "works_updated",
                            "updated_at",
                        ]
                    )
                created_total += batch_created
                updated_total += batch_updated
                skipped_total += batch_skipped
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
        # Field semantics (repo-review 2026-09-06 L-06): on a COMPLETE run
        # works_imported is the all-time IGDB catalogue size (DB truth, so a
        # resumed-to-completion run matches a single clean run), while
        # works_updated stays this-pass-only. The per-pass created/updated
        # counts live in the evidence JSON as works_created_this_pass /
        # works_updated_this_pass.
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
                f"(+{created_total} new / ~{updated_total} refreshed / {skipped_total} skipped this pass), "
                f"covers {covers_present} present / {run.covers_fallback} fallback, "
                f"checksum {run.checksum[:12]}..., eligible_live={eligible}"
            )
        )

        if evidence_json:
            self._emit_evidence(
                evidence_json,
                self._build_evidence(run, pass_start, created_total, updated_total, skipped_total),
            )
