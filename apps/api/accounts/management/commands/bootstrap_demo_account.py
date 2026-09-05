"""Bootstrap or rotate the single Phase 1 demo account (AUTH-01, SEC-02).

Fail-closed: DEMO_USERNAME/DEMO_PASSWORD are read exclusively from the
runtime environment; either missing aborts before any mutation. Idempotent
and rotation-safe via a fixed, non-sensitive anchor kept independent of the
username value itself, so rotating DEMO_USERNAME renames the same account
instead of creating a duplicate. A PostgreSQL advisory lock serialises
concurrent invocations so they never create two accounts.

Since Plan 01.1-04 (AUTH-02) this command is a thin adapter: it builds a
one-entry seed contract from DEMO_USERNAME/DEMO_PASSWORD and delegates to
the plural ``bootstrap_demo_accounts`` implementation, which also keeps the
legacy ``DemoAccountAnchor`` row (still consumed by ``seed_demo`` and the
compose startup chain) pointed at the same user.

Never writes username, password, or password hash to stdout/stderr -- only
a redacted result line, matching the canary-check contract enforced by
apps/api/accounts/tests/test_bootstrap_demo_account.py.
"""

from __future__ import annotations

import os
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from accounts.models import DEMO_ACCOUNT_ANCHOR_ID
from accounts.management.commands.bootstrap_demo_accounts import (
    LEGACY_ANCHOR_KEY,
    MIN_USERNAME_LENGTH,
    SeedEntry,
    apply_seed_contract,
    validate_seed_passwords,
)


class Command(BaseCommand):
    help = "Bootstrap or rotate the demo account from DEMO_USERNAME/DEMO_PASSWORD."

    def handle(self, *args: Any, **options: Any) -> None:
        username = os.environ.get("DEMO_USERNAME")
        password = os.environ.get("DEMO_PASSWORD")
        if not username or not password:
            raise CommandError(
                "DEMO_USERNAME and DEMO_PASSWORD must both be set in the runtime "
                "environment -- refusing to bootstrap without them."
            )
        if len(username) < MIN_USERNAME_LENGTH:
            raise CommandError("DEMO_USERNAME does not meet the minimum length policy.")

        entries = [
            SeedEntry(
                key=LEGACY_ANCHOR_KEY,
                username=username,
                password=password,
                label="Simulated demo account (primary)",
            )
        ]
        validate_seed_passwords(entries)
        result = apply_seed_contract(entries, legacy_anchor_key=LEGACY_ANCHOR_KEY)

        rotated = result.rotated == 1
        self.stdout.write(
            self.style.SUCCESS(f"Demo account ready (anchor={DEMO_ACCOUNT_ANCHOR_ID}, rotated={rotated})")
        )
