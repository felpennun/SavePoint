"""Account-boundary models. AUTH-01 uses Django's built-in User model
directly; this module only adds what that model doesn't provide."""

import uuid

from django.conf import settings
from django.db import models

# Fixed, non-sensitive anchor for the single Phase 1 demo account. Not a
# secret -- it identifies "the demo account row" independent of whatever
# DEMO_USERNAME happens to be at runtime, so rotating the env var renames
# the same account instead of creating a duplicate.
DEMO_ACCOUNT_ANCHOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# Namespace for deriving a stable per-account anchor UUID from a seed key
# (AUTH-02, Plan 01.1-04). Not a secret -- it makes "the simulated account
# known as <key>" a deterministic identity independent of the username that
# account currently carries, so rotating the username renames the same row
# instead of creating a duplicate. This is the plural generalisation of
# DEMO_ACCOUNT_ANCHOR_ID above.
DEMO_ACCOUNT_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-0000000000d3")

# Durable, public-safe marker stamped on every seeded account. Contains no
# credential material and is intended to be safe to surface in any public
# listing that needs to flag an account as "not a real user".
SIMULATED_ACCOUNT_MARKER = "simulated-demo-account"


def demo_identity_anchor_id(seed_key: str) -> uuid.UUID:
    """Deterministic anchor UUID for a seed key -- the opaque reference the
    bootstrap command emits instead of any credential-shaped value."""
    return uuid.uuid5(DEMO_ACCOUNT_NAMESPACE, seed_key)


class DemoAccountAnchor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demo_anchor")

    def __str__(self) -> str:
        return f"demo anchor {self.id}"


class DemoAccountIdentity(models.Model):
    """One clearly-labelled simulated account (AUTH-02).

    `seed_key` is the stable, non-secret identity from the environment-only
    seed contract; `id` is its deterministic anchor (uuid5 of the key). The
    `is_simulated` / `marker` / `display_label` fields are the durable,
    credential-free marker that a public listing can show to make clear the
    row is a synthetic demo account rather than a real user.
    """

    id = models.UUIDField(primary_key=True, editable=False)
    seed_key = models.CharField(max_length=64, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demo_identity"
    )
    is_simulated = models.BooleanField(default=True)
    marker = models.CharField(max_length=64, default=SIMULATED_ACCOUNT_MARKER)
    display_label = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("seed_key",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_simulated=True),
                name="accounts_demo_identity_always_simulated",
            ),
        ]

    def __str__(self) -> str:
        return f"demo identity {self.seed_key} ({self.id})"
