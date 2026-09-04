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


class DemoAccountAnchor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demo_anchor")

    def __str__(self) -> str:
        return f"demo anchor {self.id}"
