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


class ProfileVisibility(models.TextChoices):
    """D-02/D-03: only two verifiable states -- "friends-only" is
    deliberately never modeled here because the backend has no friendship
    relation to resolve it against."""

    PUBLIC = "public", "Public"
    PRIVATE = "private", "Private"


BIO_MAX_LENGTH = 500
AVATAR_URL_MAX_LENGTH = 500
DISPLAY_NAME_MAX_LENGTH = 40
AVATAR_PRESET_COUNT = 5
# Profile photo and cover are cropped and compressed in the browser before
# upload, so this ceiling is generous; it only guards the database row.
PROFILE_IMAGE_MAX_BYTES = 512 * 1024


class AccountProfile(models.Model):
    """Editable profile data layered onto the immutable login alias (D-01).

    ``User.username`` remains the public, non-editable alias; this table only
    ever adds biography/avatar/visibility. The owning user is always derived
    from ``request.user`` in the service layer -- this model never accepts a
    substitutable owner from a request payload.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    # Opaque technical locator used by the explicit role bootstrap command;
    # it is not a username, email, or public identifier.
    admin_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    bio = models.CharField(max_length=BIO_MAX_LENGTH, blank=True, default="")
    # HTTPS-only, validated URL with no server-side fetch/proxy (avoids SSRF);
    # the client is responsible for actually rendering the image safely.
    avatar_url = models.URLField(max_length=AVATAR_URL_MAX_LENGTH, blank=True, default="")
    # Free-form name shown next to the immutable alias (``User.username``).
    display_name = models.CharField(max_length=DISPLAY_NAME_MAX_LENGTH, blank=True, default="")
    # One of the built-in SavePoint avatars (0..AVATAR_PRESET_COUNT-1).
    avatar_preset = models.PositiveSmallIntegerField(null=True, blank=True)
    # Uploaded images, already cropped client-side; served only through the
    # owner-scoped /me/avatar/ and /me/cover/ endpoints.
    avatar_image = models.BinaryField(null=True, blank=True, editable=False)
    avatar_image_type = models.CharField(max_length=16, blank=True, default="")
    cover_image = models.BinaryField(null=True, blank=True, editable=False)
    cover_image_type = models.CharField(max_length=16, blank=True, default="")
    # Set when the owner renames their account; a rename is allowed only once.
    username_changed_at = models.DateTimeField(null=True, blank=True)
    # Visibility given to custom lists the owner creates from now on.
    default_list_visibility = models.CharField(
        max_length=8, choices=ProfileVisibility.choices, default=ProfileVisibility.PUBLIC
    )
    collection_visibility = models.CharField(
        max_length=8, choices=ProfileVisibility.choices, default=ProfileVisibility.PUBLIC
    )
    favorites_visibility = models.CharField(
        max_length=8, choices=ProfileVisibility.choices, default=ProfileVisibility.PUBLIC
    )
    is_anonymized = models.BooleanField(default=False)
    anonymized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(collection_visibility__in=[choice.value for choice in ProfileVisibility]),
                name="accounts_profile_collection_visibility_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(favorites_visibility__in=[choice.value for choice in ProfileVisibility]),
                name="accounts_profile_favorites_visibility_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(default_list_visibility__in=[choice.value for choice in ProfileVisibility]),
                name="accounts_profile_default_list_visibility_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(avatar_preset__isnull=True) | models.Q(avatar_preset__lt=AVATAR_PRESET_COUNT),
                name="accounts_profile_avatar_preset_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"profile for user {self.user_id}"


MIN_FAVORITE_SLOT = 1
MAX_FAVORITE_SLOT = 5


class FavoriteSlot(models.Model):
    """One of the five favorite-shelf positions (D-02).

    Populated only from works already present in the owner's own collection
    (``LibraryEntry``, enforced in the service layer); slot range and
    per-user uniqueness are enforced again here as the last line of defense,
    matching the ``LibraryEntry``/``OwnedCopy`` constraint pattern.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_slots"
    )
    slot = models.PositiveSmallIntegerField()
    work = models.ForeignKey(
        "catalogue.GameWork", on_delete=models.PROTECT, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("slot",)
        constraints = [
            models.UniqueConstraint(fields=("user", "slot"), name="accounts_favorite_unique_user_slot"),
            models.UniqueConstraint(fields=("user", "work"), name="accounts_favorite_unique_user_work"),
            models.CheckConstraint(
                condition=models.Q(slot__gte=MIN_FAVORITE_SLOT) & models.Q(slot__lte=MAX_FAVORITE_SLOT),
                name="accounts_favorite_slot_range",
            ),
        ]

    def __str__(self) -> str:
        return f"favorite slot {self.slot} for user {self.user_id}"
