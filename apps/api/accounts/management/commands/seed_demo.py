"""Load deterministic demo interactions (Plan 01-16: REC-02, AUTH-01, LIB-01,
LIB-02, OPS-03).

Fail-closed: requires the bootstrap demo account (via its stable anchor
UUID, never a password) and every referenced catalogue work to already
exist -- run bootstrap_demo_account and import_catalogue first. Never
reads DEMO_USERNAME/DEMO_PASSWORD, never calls set_password, never prints
or accepts anything credential-shaped (checked by an explicit denylist
scan of the whole manifest before any mutation).

Idempotent via LibraryEntry's own (user, work) upsert semantics: a second
run reproduces the exact same rows. Advisory-lock-guarded so a concurrent
invocation serializes rather than leaving partial state.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from accounts.models import DemoAccountAnchor
from catalogue.models import GameWork
from library.models import LibraryEntry
from library.popularity import rank_popularity_v1

REPO_ROOT = Path(__file__).resolve().parents[5]
SEED_PATH = REPO_ROOT / "data" / "demo" / "seed-v1.json"

SEED_LOCK_KEY = 725_01_16

# Any key whose name contains one of these (case-insensitive, anywhere in
# the document) aborts the load before any mutation -- this manifest must
# never carry authentication material of any kind.
FORBIDDEN_KEY_SUBSTRINGS = ("password", "token", "cookie", "secret", "credential")


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _check_no_sensitive_keys(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = key.lower()
            if any(bad in lowered for bad in FORBIDDEN_KEY_SUBSTRINGS):
                raise CommandError(f"Seed manifest contains a forbidden key '{path}{key}'.")
            _check_no_sensitive_keys(nested, f"{path}{key}.")
    elif isinstance(value, list):
        for item in value:
            _check_no_sensitive_keys(item, path)


class Command(BaseCommand):
    help = "Load deterministic demo interactions from data/demo/seed-v1.json."

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CommandError(f"Seed manifest not found at {SEED_PATH}.") from exc

        _check_no_sensitive_keys(seed)

        interactions = seed["interactions"]
        actual_hash = hashlib.sha256(_canonical_bytes(interactions)).hexdigest()
        if actual_hash != seed["interactions_sha256"]:
            raise CommandError("Seed manifest interactions checksum mismatch -- refusing to load.")

        try:
            anchor = DemoAccountAnchor.objects.select_related("user").get(id=seed["account_anchor_id"])
        except DemoAccountAnchor.DoesNotExist as exc:
            raise CommandError(
                "Demo account not found -- run bootstrap_demo_account before seed_demo."
            ) from exc
        user = anchor.user

        loaded = 0
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [SEED_LOCK_KEY])

            for interaction in interactions:
                try:
                    work = GameWork.objects.get(id=interaction["work_id"])
                except GameWork.DoesNotExist as exc:
                    raise CommandError(
                        f"Seed references unknown work {interaction['work_id']} -- "
                        "run import_catalogue before seed_demo."
                    ) from exc

                entry, _ = LibraryEntry.objects.select_for_update().get_or_create(user=user, work=work)
                entry.current_status = interaction["status"]
                entry.rating_half_steps = interaction["rating_half_steps"]
                entry.save(update_fields=["current_status", "rating_half_steps", "updated_at"])
                loaded += 1

        # Read-only verification of what was just committed, against the
        # manifest's own declared expectation -- catches data or
        # popularity-formula drift immediately rather than silently.
        expected = seed["expected_popularity_v1"]["results"]
        expected_ids = {row["work_id"] for row in expected}
        actual = rank_popularity_v1()
        actual_subset = [
            {"work_id": row["work_id"], "slug": row["slug"], "score": row["score"]}
            for row in actual["results"]
            if row["work_id"] in expected_ids
        ]
        if actual_subset != expected:
            raise CommandError(
                "Loaded interactions do not reproduce the manifest's expected "
                "popularity-v1 result -- data or formula drift."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed loaded ({loaded} interactions, digest={actual_hash[:12]}..., "
                f"popularity-v1 matches {len(expected)}/{len(expected)} expected results)"
            )
        )
