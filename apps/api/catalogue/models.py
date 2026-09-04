"""Canonical catalogue identity, independent of enrichment providers."""

import uuid

from django.db import models


class GameWork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_slug = models.SlugField(max_length=200, unique=True)
    original_title = models.CharField(max_length=300)
    is_dlc = models.BooleanField(default=False)

    class Meta:
        ordering = ("original_title", "id")

    def __str__(self) -> str:
        return self.original_title


class GameRelease(models.Model):
    """A release variant of a work; platform and edition are normalized later."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(GameWork, on_delete=models.PROTECT, related_name="releases")
    release_name = models.CharField(max_length=300)
    release_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("release_date", "release_name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("work", "release_name"),
                name="catalogue_unique_release_name_per_work",
            )
        ]

    def __str__(self) -> str:
        return f"{self.work}: {self.release_name}"

