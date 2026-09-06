"""Bootstrap or rotate the plural set of clearly-labelled simulated demo
accounts (AUTH-02, D-02/D-08).

The seed contract is environment-only: ``DEMO_ACCOUNTS`` holds a JSON array
of ``{"key", "username", "password", "label"?}`` objects. ``key`` is a
stable, non-secret identifier -- the plural generalisation of
``DEMO_ACCOUNT_ANCHOR_ID`` -- so rotating a username renames the same
account row instead of creating a duplicate. Every referenced password is
run through Django's configured validators *before* any write. A single
failure (missing env, malformed JSON, duplicate key, duplicate alias, weak
password, or an alias colliding with an unrelated account) aborts the whole
run inside one transaction with no partial mutation. A PostgreSQL
transaction-scoped advisory lock serialises concurrent runs -- including
against the singular ``bootstrap_demo_account`` command, which delegates
here. Output is redacted: only counts and opaque anchor UUIDs, never a
username, password, or password hash.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from accounts.models import (
    DEMO_ACCOUNT_ANCHOR_ID,
    SIMULATED_ACCOUNT_MARKER,
    DemoAccountAnchor,
    DemoAccountIdentity,
    demo_identity_anchor_id,
)

# Shared with the singular bootstrap_demo_account command so the two never
# race each other into creating two accounts. Same key the singular command
# has always used (725_01_15); distinct from seed_demo (725_01_16) and the
# catalogue importers.
BOOTSTRAP_LOCK_KEY = 725_01_15

# Seed key the singular DEMO_USERNAME/DEMO_PASSWORD path delegates under.
LEGACY_ANCHOR_KEY = "demo-anchor-primary"

MIN_USERNAME_LENGTH = 3
MAX_KEY_LENGTH = 64
_KEY_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")

ENV_VAR = "DEMO_ACCOUNTS"


class SeedContractError(CommandError):
    """A problem with the seed contract. Subclasses CommandError so
    ``call_command`` surfaces it the same way the singular command does.
    Messages here never interpolate a username or password."""


@dataclass(frozen=True)
class SeedEntry:
    key: str
    username: str
    password: str
    label: str


@dataclass
class BootstrapResult:
    created: int = 0
    rotated: int = 0
    users: dict[str, Any] = field(default_factory=dict)
    anchor_ids: list[str] = field(default_factory=list)


def parse_seed_contract(raw: str | None) -> list[SeedEntry]:
    """Parse and fully validate the DEMO_ACCOUNTS contract. Never touches the
    database; every structural problem is caught here before any mutation."""
    if not raw or not raw.strip():
        raise SeedContractError(
            f"{ENV_VAR} must be set to a non-empty JSON array in the runtime environment "
            "-- refusing to bootstrap without it."
        )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SeedContractError(f"{ENV_VAR} is not valid JSON.") from exc

    if not isinstance(payload, list) or not payload:
        raise SeedContractError(f"{ENV_VAR} must be a non-empty JSON array of account objects.")

    entries: list[SeedEntry] = []
    seen_keys: set[str] = set()
    seen_usernames: set[str] = set()

    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise SeedContractError(f"{ENV_VAR}[{index}] must be a JSON object.")

        key = str(item.get("key", "")).strip()
        username = str(item.get("username", "")).strip()
        password = item.get("password")
        label = str(item.get("label", "")).strip()

        if not key or not username or not isinstance(password, str) or not password:
            raise SeedContractError(
                f"{ENV_VAR}[{index}] needs a non-empty 'key', 'username', and 'password'."
            )
        if len(key) > MAX_KEY_LENGTH or not _KEY_RE.fullmatch(key):
            raise SeedContractError(
                f"{ENV_VAR}[{index}] 'key' must be 1-{MAX_KEY_LENGTH} chars of [a-z0-9_-]."
            )
        if len(username) < MIN_USERNAME_LENGTH:
            raise SeedContractError(
                f"{ENV_VAR}[{index}] 'username' does not meet the minimum length policy."
            )
        if key in seen_keys:
            raise SeedContractError(f"{ENV_VAR} contains the duplicate key '{key}'.")
        if username in seen_usernames:
            raise SeedContractError(f"{ENV_VAR} contains a duplicate username.")

        seen_keys.add(key)
        seen_usernames.add(username)
        entries.append(
            SeedEntry(
                key=key,
                username=username,
                password=password,
                label=label or f"Simulated demo account ({key})",
            )
        )

    return entries


def validate_seed_passwords(entries: Sequence[SeedEntry]) -> None:
    """Run every password through the configured validators before any write.
    The error message is deliberately generic -- it never echoes the value."""
    for entry in entries:
        try:
            validate_password(entry.password)
        except DjangoValidationError as exc:
            raise SeedContractError(
                "A seed password does not meet the configured password policy."
            ) from exc


def _bootstrap_identities(
    entries: Sequence[SeedEntry], *, legacy_anchor_key: str | None = None
) -> BootstrapResult:
    """Create or rotate each identity. Caller MUST already hold an open
    transaction and the advisory lock.

    ``legacy_anchor_key`` names the entry (if any) that stands in for the
    Phase 1 primary demo account. When the switch from the singular
    ``bootstrap_demo_account`` to this plural command happens on an
    environment that already ran the singular one, the primary user exists
    but may not yet carry a ``DemoAccountIdentity``. Rather than aborting on
    a username collision, that pre-existing account -- and only the one
    behind the fixed ``DEMO_ACCOUNT_ANCHOR_ID`` anchor -- is *adopted* into
    the plural model. Same "coexist with existing state" pattern as
    ``fix(01.1-02)``.
    """
    user_model = get_user_model()
    result = BootstrapResult()

    legacy_user = None
    if legacy_anchor_key is not None:
        legacy_anchor = (
            DemoAccountAnchor.objects.select_related("user")
            .filter(id=DEMO_ACCOUNT_ANCHOR_ID)
            .first()
        )
        legacy_user = legacy_anchor.user if legacy_anchor is not None else None

    for entry in sorted(entries, key=lambda e: e.key):
        anchor_id = demo_identity_anchor_id(entry.key)
        result.anchor_ids.append(str(anchor_id))

        identity = (
            DemoAccountIdentity.objects.select_related("user").filter(seed_key=entry.key).first()
        )
        if identity is not None:
            user = identity.user
            if user_model.objects.filter(username=entry.username).exclude(pk=user.pk).exists():
                raise SeedContractError(
                    "A seed username collides with an existing, unrelated account."
                )
            user.username = entry.username
            user.set_password(entry.password)
            user.is_active = True
            user.save(update_fields=["username", "password", "is_active"])

            identity.is_simulated = True
            identity.marker = SIMULATED_ACCOUNT_MARKER
            identity.display_label = entry.label
            identity.save(update_fields=["is_simulated", "marker", "display_label", "updated_at"])
            result.rotated += 1
        else:
            adopt_user = legacy_user if entry.key == legacy_anchor_key else None
            collision = user_model.objects.filter(username=entry.username)
            if adopt_user is not None:
                collision = collision.exclude(pk=adopt_user.pk)
            if collision.exists():
                raise SeedContractError(
                    "A seed username collides with an existing, unrelated account."
                )
            if adopt_user is not None:
                user = adopt_user
                user.username = entry.username
                user.set_password(entry.password)
                user.is_active = True
                user.save(update_fields=["username", "password", "is_active"])
            else:
                user = user_model.objects.create_user(
                    username=entry.username, password=entry.password
                )
            DemoAccountIdentity.objects.create(
                id=anchor_id,
                seed_key=entry.key,
                user=user,
                is_simulated=True,
                marker=SIMULATED_ACCOUNT_MARKER,
                display_label=entry.label,
            )
            result.created += 1

        result.users[entry.key] = user

    return result


def _sync_legacy_anchor(user: Any) -> None:
    """Keep the Phase 1 DemoAccountAnchor row pointed at the delegated user so
    seed_demo and the compose startup chain keep working unchanged."""
    anchor = DemoAccountAnchor.objects.filter(id=DEMO_ACCOUNT_ANCHOR_ID).first()
    if anchor is None:
        DemoAccountAnchor.objects.create(id=DEMO_ACCOUNT_ANCHOR_ID, user=user)
    elif anchor.user_id != user.pk:
        anchor.user = user
        anchor.save(update_fields=["user"])


def apply_seed_contract(
    entries: Sequence[SeedEntry], *, legacy_anchor_key: str | None = None
) -> BootstrapResult:
    """Serialised, all-or-nothing application of a validated seed contract.

    Passwords must already have been validated (see ``validate_seed_passwords``).
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [BOOTSTRAP_LOCK_KEY])

        result = _bootstrap_identities(entries, legacy_anchor_key=legacy_anchor_key)

        if legacy_anchor_key is not None:
            _sync_legacy_anchor(result.users[legacy_anchor_key])

    return result


class Command(BaseCommand):
    help = "Bootstrap or rotate the simulated demo accounts defined by DEMO_ACCOUNTS."

    def handle(self, *args: Any, **options: Any) -> None:
        entries = parse_seed_contract(os.environ.get(ENV_VAR))
        validate_seed_passwords(entries)
        # If the contract carries the legacy primary key, keep the Phase 1
        # DemoAccountAnchor pointed at it (seed_demo + the startup chain rely
        # on that row) and let that one entry adopt a pre-existing singular
        # demo account instead of colliding with it.
        has_legacy = any(entry.key == LEGACY_ANCHOR_KEY for entry in entries)
        result = apply_seed_contract(
            entries, legacy_anchor_key=LEGACY_ANCHOR_KEY if has_legacy else None
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo accounts ready (total={len(entries)}, created={result.created}, "
                f"rotated={result.rotated}, anchors={result.anchor_ids})"
            )
        )
