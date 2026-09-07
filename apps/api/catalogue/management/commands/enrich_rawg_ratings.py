"""Enrich a bounded governed-corpus subset with RAWG user ratings."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import F

from catalogue.corpus import governed_works
from catalogue.models import CorpusRatingSnapshot, CorpusVersion, SourceRecord
from catalogue.normalization import normalize_title
from catalogue.rawg import RAWG_LICENCE, RAWG_TERMS_URL, RawgClient

RAWG_LOCK_KEY = 902_020_203
RAWG_SOURCE = "rawg"


def _release_year(value: object) -> int | None:
    if isinstance(value, date):
        return value.year
    if not isinstance(value, str) or len(value) < 4:
        return None
    try:
        return int(value[:4])
    except ValueError:
        return None


def _candidate_rating(candidate: dict) -> tuple[float, int] | None:
    rating = candidate.get("rating")
    count = candidate.get("ratings_count")
    if not isinstance(rating, (int, float)) or isinstance(rating, bool):
        return None
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return None
    return round(float(rating) * 20, 4), count


def reconcile_rawg_candidate(work: Any, candidates: list[dict]) -> dict | None:
    """Match by exact slug, then normalized title plus release year.

    A title/year match is accepted only when the candidate has a usable
    rating. No fuzzy distance or popularity heuristic is used.
    """

    slug = str(work.canonical_slug or "").strip().casefold()
    exact_slug = [item for item in candidates if str(item.get("slug") or "").casefold() == slug]
    if exact_slug:
        return exact_slug[0]

    allowed_titles = {normalize_title(work.original_title)}
    if work.title_en:
        allowed_titles.add(normalize_title(work.title_en))
    allowed_titles.update(work.aliases.values_list("normalized_value", flat=True))
    year = _release_year(work.first_release_date)
    matches = [
        item
        for item in candidates
        if normalize_title(str(item.get("name") or "")) in allowed_titles
        and year is not None
        and _release_year(item.get("released")) == year
    ]
    return matches[0] if matches else None


def _payload_hash(candidate: dict) -> str:
    payload = json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "Insert bounded RAWG user-rating snapshots for an active governed corpus."
    stealth_options = ("client",)
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument("--limit", type=int, default=10_000)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--evidence-json", default="-")

    @staticmethod
    def _retrieved_at() -> datetime:
        return datetime.now(timezone.utc)

    def _emit(self, path: str, payload: dict[str, Any]) -> None:
        blob = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob, ending="")
            return
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"evidence written: {target}")

    def handle(self, *args: Any, **options: Any) -> None:
        version = options["corpus_version"]
        corpus_version = CorpusVersion.objects.filter(version=version).first()
        if corpus_version is None:
            raise CommandError(f"unknown corpus version: {version}")
        if not corpus_version.is_active:
            raise CommandError(f"corpus version {version} is not active")
        limit = options["limit"]
        offset = options["offset"]
        if limit < 1 or limit > 20_000 or offset < 0:
            raise CommandError("RAWG limit must be between 1 and 20000; offset must be non-negative")

        client = options.get("client") or RawgClient()
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [RAWG_LOCK_KEY])
            works = list(
                governed_works(version)
                .order_by(F("rating_count").desc(nulls_last=True), "original_title", "pk")
                [offset : offset + limit]
            )
            retrieved_at = self._retrieved_at()
            matched = inserted = 0
            no_match = no_rating = 0
            for work in works:
                candidates = client.search_games(work.original_title)
                candidate = reconcile_rawg_candidate(work, candidates)
                if candidate is None:
                    no_match += 1
                    continue
                rating = _candidate_rating(candidate)
                if rating is None:
                    no_rating += 1
                    continue
                rawg_id = candidate.get("id")
                rawg_slug = str(candidate.get("slug") or "").strip()
                if not isinstance(rawg_id, int) or not rawg_slug:
                    no_match += 1
                    continue
                matched += 1
                source_record, _ = SourceRecord.objects.update_or_create(
                    source=RAWG_SOURCE,
                    source_id=str(rawg_id),
                    defaults={
                        "work": work,
                        "source_url": f"https://rawg.io/games/{rawg_slug}",
                        "retrieved_at": retrieved_at,
                        "licence": RAWG_LICENCE,
                        "snapshot_sha256": _payload_hash(candidate),
                    },
                )
                _snapshot, created = CorpusRatingSnapshot.objects.get_or_create(
                    work=work,
                    corpus_version=version,
                    source=RAWG_SOURCE,
                    defaults={
                        "rating": rating[0],
                        "rating_count": rating[1],
                        "retrieved_at": source_record.retrieved_at,
                    },
                )
                inserted += int(created)

            payload = {
                "corpus_version": version,
                "source": RAWG_SOURCE,
                "limit": limit,
                "offset": offset,
                "works_considered": len(works),
                "matched": matched,
                "snapshots_inserted": inserted,
                "not_matched": no_match,
                "matched_without_rating": no_rating,
                "terms_url": RAWG_TERMS_URL,
                "backlink_required": True,
            }
        self._emit(options["evidence_json"], payload)
