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

