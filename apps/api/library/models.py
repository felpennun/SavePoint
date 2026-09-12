"""Personal library state at canonical game-work level."""

import uuid

from django.conf import settings
from django.db import models

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


class OwnedCopy(models.Model):
    """A single owned copy (D-15/D-16). Status/rating live on LibraryEntry,
    not here -- multiple copies of the same work are independent ownership
    records that never fork the work-level status or rating."""

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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "idempotency_key"),
                name="library_unique_copy_idempotency_per_user",
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
    """One comment per user/work (D-04/D-05): only the author can create,
    edit, or delete it; the author always retains access regardless of
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
            models.UniqueConstraint(
                fields=("user", "work"),
                name="library_unique_comment_per_user_work",
            ),
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
        ]

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
