"""Personal library state at canonical game-work level."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from catalogue.models import Edition, GameRelease, GameWork


class BacklogStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PLAYING = "playing", "Playing"
    COMPLETED = "completed", "Completed"
    ABANDONED = "abandoned", "Abandoned"


class LibraryEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="library_entries")
    work = models.ForeignKey(GameWork, on_delete=models.PROTECT, related_name="library_entries")
    current_status = models.CharField(
        max_length=16,
        choices=BacklogStatus.choices,
        null=True,
        blank=True,
    )
    # D-13: five stars in half-star increments, stored as an exact integer of
    # half-steps (1..10); null means unrated. Never a float -- see
    # RESEARCH.md anti-pattern "Guardar rating como float".
    rating_half_steps = models.IntegerField(null=True, blank=True)
    # Personal "platinum" mark (own accomplishment, not an external trophy
    # feed) -- a simple owner-set boolean on the same per-user/work entity
    # as status and rating. Only ever shown on the owner's own collection
    # view; never surfaced on the public profile or the shared catalogue.
    is_platinum = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "work"),
                name="library_unique_entry_per_user_work",
            ),
            models.CheckConstraint(
                condition=models.Q(rating_half_steps__isnull=True)
                | (models.Q(rating_half_steps__gte=1) & models.Q(rating_half_steps__lte=10)),
                name="library_rating_half_steps_range",
            ),
        ]


class StatusTransition(models.Model):
    entry = models.ForeignKey(LibraryEntry, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(
        max_length=16,
        choices=BacklogStatus.choices,
        null=True,
        blank=True,
    )
    to_status = models.CharField(max_length=16, choices=BacklogStatus.choices)
    changed_at = models.DateTimeField()

    class Meta:
        ordering = ("-changed_at", "-id")


class CopyFormat(models.TextChoices):
    PHYSICAL = "physical", "Physical"
    DIGITAL = "digital", "Digital"


class ConservationState(models.TextChoices):
    """D-01/discretion, INV-04: a small, documented conservation taxonomy for
    physical copies. Deliberately not modeled for digital copies -- there is
    nothing physical to conserve, and the model-level CheckConstraint below
    rejects any digital row that carries one."""

    NEW = "new", "New"
    GOOD = "good", "Good"
    FAIR = "fair", "Fair"
    POOR = "poor", "Poor"
    DAMAGED = "damaged", "Damaged"


COPY_CURRENCY_LENGTH = 3
COPY_STORE_MAX_LENGTH = 120
COPY_STORAGE_LOCATION_MAX_LENGTH = 200
COPY_PRICE_MAX_DIGITS = 10
COPY_PRICE_DECIMAL_PLACES = 2


class OwnedCopy(models.Model):
    """A single owned copy (D-15/D-16). Status/rating live on LibraryEntry,
    not here -- multiple copies of the same work are independent ownership
    records that never fork the work-level status or rating.

    INV-03/INV-04: ``purchase_date``/``price``/``currency``/``store`` are
    auditable purchase metadata for any copy; ``conservation_state``/
    ``storage_location`` are physical-only and must stay null for a
    ``format="digital"`` row -- enforced here at the serializer/service
    layers and, as the last line of defense, by
    ``library_copy_digital_excludes_conservation`` below. None of these
    fields are ever part of a public projection (INV-05, PRIV-01)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_copies")
    work = models.ForeignKey(GameWork, on_delete=models.PROTECT, related_name="owned_copies")
    release = models.ForeignKey(GameRelease, on_delete=models.PROTECT, related_name="owned_copies")
    edition = models.ForeignKey(
        Edition, on_delete=models.PROTECT, related_name="owned_copies", null=True, blank=True
    )
    format = models.CharField(max_length=16, choices=CopyFormat.choices)
    # Client-supplied idempotency key: replaying the same key for the same
    # user returns the existing copy instead of creating a duplicate.
    idempotency_key = models.CharField(max_length=100)
    purchase_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=COPY_PRICE_MAX_DIGITS, decimal_places=COPY_PRICE_DECIMAL_PLACES, null=True, blank=True
    )
    # Three uppercase letters (e.g. "EUR", "USD") -- never a float, never a
    # locale-formatted string; validated in serializer/service and by
    # ``library_copy_currency_format_valid`` below.
    currency = models.CharField(max_length=COPY_CURRENCY_LENGTH, null=True, blank=True)
    store = models.CharField(max_length=COPY_STORE_MAX_LENGTH, null=True, blank=True)
    conservation_state = models.CharField(
        max_length=8, choices=ConservationState.choices, null=True, blank=True
    )
    storage_location = models.CharField(max_length=COPY_STORAGE_LOCATION_MAX_LENGTH, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "idempotency_key"),
                name="library_unique_copy_idempotency_per_user",
            ),
            models.CheckConstraint(
                condition=models.Q(price__isnull=True) | models.Q(price__gte=0),
                name="library_copy_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(currency__isnull=True) | models.Q(currency__regex=r"^[A-Z]{3}$"),
                name="library_copy_currency_format_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(conservation_state__isnull=True)
                | models.Q(conservation_state__in=[choice.value for choice in ConservationState]),
                name="library_copy_conservation_state_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(format="physical")
                | (models.Q(conservation_state__isnull=True) & models.Q(storage_location__isnull=True)),
                name="library_copy_digital_excludes_conservation",
            ),
        ]


class ContentVisibility(models.TextChoices):
    """D-05/D-07: comments and custom lists each carry their own independent
    public/private toggle -- never derived from AccountProfile's
    collection_visibility/favorites_visibility. "Friends-only" is
    deliberately not modeled: the backend has no friendship relation to
    resolve it against (matches accounts.ProfileVisibility)."""

    PUBLIC = "public", "Public"
    PRIVATE = "private", "Private"


COMMENT_TEXT_MAX_LENGTH = 2000


class GameComment(models.Model):
    """A comment by a user on a work; a user may write several per work. Only
    the author can edit or delete it; the author always retains access regardless of
    visibility, while a public/private third-party projection is resolved
    server-side (never on the client)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    work = models.ForeignKey(GameWork, on_delete=models.PROTECT, related_name="comments")
    text = models.CharField(max_length=COMMENT_TEXT_MAX_LENGTH)
    visibility = models.CharField(
        max_length=8, choices=ContentVisibility.choices, default=ContentVisibility.PUBLIC
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(visibility__in=[choice.value for choice in ContentVisibility]),
                name="library_comment_visibility_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"comment by {self.user_id} on {self.work_id}"


LIST_NAME_MAX_LENGTH = 120


class CustomList(models.Model):
    """A user's manual, ordered collection of games already in their own
    collection (LIB-04/D-06/D-07). Not a saved search or a recommendation --
    every item must already have a ``LibraryEntry`` for this same user;
    that membership check lives in the service layer, never here.

    ``version`` is the optimistic-concurrency counter the reorder endpoint
    guards with: every accepted reorder increments it, and a stale
    ``expected_version`` is rejected with HTTP 409 before any item is
    touched (Plan 05-02 Task 2).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="custom_lists")
    name = models.CharField(max_length=LIST_NAME_MAX_LENGTH)
    public_slug = models.SlugField(max_length=140, editable=False)
    visibility = models.CharField(
        max_length=8, choices=ContentVisibility.choices, default=ContentVisibility.PUBLIC
    )
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(visibility__in=[choice.value for choice in ContentVisibility]),
                name="library_list_visibility_valid",
            ),
            models.UniqueConstraint(
                fields=("user", "public_slug"), name="library_unique_public_slug_per_owner"
            ),
        ]

    def save(self, *args, **kwargs):  # noqa: ANN002, ANN003
        """Assign a stable owner-scoped locator on first persistence."""
        if not self.public_slug:
            base = slugify(self.name) or "list"
            candidate = base[:140]
            suffix = 2
            queryset = type(self).objects.filter(user_id=self.user_id)
            if self.pk is not None:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.filter(public_slug=candidate).exists():
                suffix_text = f"-{suffix}"
                candidate = f"{base[: 140 - len(suffix_text)]}{suffix_text}"
                suffix += 1
            self.public_slug = candidate
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"list {self.name} ({self.id})"


class CustomListItem(models.Model):
    """One game inside a ``CustomList``, with a persisted manual position.

    ``position`` is a plain integer, never inferred from list index or
    ``created_at`` -- the reorder endpoint is the only writer of this field
    after creation, and it always reassigns the complete consecutive
    ``1..N`` range inside one transaction (Pattern 4, 05-PATTERNS.md).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    list = models.ForeignKey(CustomList, on_delete=models.CASCADE, related_name="items")
    work = models.ForeignKey(GameWork, on_delete=models.PROTECT, related_name="list_items")
    position = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("list", "position")
        constraints = [
            models.UniqueConstraint(fields=("list", "work"), name="library_unique_list_item_work"),
            models.UniqueConstraint(fields=("list", "position"), name="library_unique_list_item_position"),
        ]

    def __str__(self) -> str:
        return f"item {self.work_id} at position {self.position} in list {self.list_id}"
