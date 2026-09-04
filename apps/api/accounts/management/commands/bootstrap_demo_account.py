"""Bootstrap or rotate the single Phase 1 demo account (AUTH-01, SEC-02).

Fail-closed: DEMO_USERNAME/DEMO_PASSWORD are read exclusively from the
runtime environment; either missing aborts before any mutation. Idempotent
and rotation-safe via a fixed, non-sensitive anchor UUID (DemoAccountAnchor)
kept independent of the username value itself, so rotating DEMO_USERNAME
renames the same account instead of creating a duplicate. A PostgreSQL
advisory lock serializes concurrent invocations so they never create two
accounts.

Never writes username, password, or password hash to stdout/stderr -- only
a redacted result line, matching the canary-check contract enforced by
apps/api/accounts/tests/test_bootstrap_demo_account.py.
"""

from __future__ import annotations

import os
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from accounts.models import DEMO_ACCOUNT_ANCHOR_ID, DemoAccountAnchor

# Distinct from IMPORT_LOCK_KEY (725_01_06) in catalogue's import_catalogue.
BOOTSTRAP_LOCK_KEY = 725_01_15

MIN_USERNAME_LENGTH = 3


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
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise CommandError("DEMO_PASSWORD does not meet the configured password policy.") from exc

        user_model = get_user_model()
        rotated = False

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [BOOTSTRAP_LOCK_KEY])

            anchor = (
                DemoAccountAnchor.objects.select_related("user")
                .filter(id=DEMO_ACCOUNT_ANCHOR_ID)
                .first()
            )
            if anchor is not None:
                user = anchor.user
                # A DEMO_USERNAME rotation could collide with an unrelated,
                # already-existing account -- fail closed rather than
                # silently overwrite someone else's row.
                if user_model.objects.filter(username=username).exclude(pk=user.pk).exists():
                    raise CommandError("DEMO_USERNAME collides with an existing, unrelated account.")
                user.username = username
                user.set_password(password)
                user.is_active = True
                user.save(update_fields=["username", "password", "is_active"])
                rotated = True
            else:
                if user_model.objects.filter(username=username).exists():
                    raise CommandError("DEMO_USERNAME collides with an existing, unrelated account.")
                user = user_model.objects.create_user(username=username, password=password)
                DemoAccountAnchor.objects.create(id=DEMO_ACCOUNT_ANCHOR_ID, user=user)

        self.stdout.write(
            self.style.SUCCESS(f"Demo account ready (anchor={DEMO_ACCOUNT_ANCHOR_ID}, rotated={rotated})")
        )
