"""Personal library state at canonical game-work level."""

from django.conf import settings
from django.db import models

from catalogue.models import GameWork


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
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "work"),
                name="library_unique_entry_per_user_work",
            )
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

