"""Canonical catalogue identity, independent of enrichment providers.

Identity hierarchy (D-09): GameWork -> GameRelease (per platform) -> Edition.
CAT-04: the primary key is an internal UUID generated at import time; the
external provider identifier (Wikidata QID) is retained only on SourceRecord,
never as the primary key, so re-pointing at a different or absent provider
later never requires renumbering the catalogue.
"""

import uuid

from django.contrib.postgres.indexes import GinIndex
from django.db import models


class GameWork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_slug = models.SlugField(max_length=200, unique=True)
    original_title = models.CharField(max_length=300)
    title_en = models.CharField(max_length=300, blank=True)
    title_es = models.CharField(max_length=300, blank=True)
    is_dlc = models.BooleanField(default=False)

    class Meta:
        ordering = ("original_title", "id")

    def __str__(self) -> str:
        return self.original_title


class Platform(models.Model):
    """A hardware/software platform a release runs on (D-05/D-06 families)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class GameRelease(models.Model):
    """A platform-specific release variant of a work."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(GameWork, on_delete=models.PROTECT, related_name="releases")
    platform = models.ForeignKey(
        Platform, on_delete=models.PROTECT, related_name="releases", null=True, blank=True
    )
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


class Edition(models.Model):
    """A named edition of a release (e.g. "Game of the Year", "Deluxe")."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    release = models.ForeignKey(GameRelease, on_delete=models.PROTECT, related_name="editions")
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ("name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("release", "name"),
                name="catalogue_unique_edition_name_per_release",
            )
        ]

    def __str__(self) -> str:
        return f"{self.release}: {self.name}"


class GameAlias(models.Model):
    """Bilingual title/alias for tolerant search (D-10/D-12)."""

    class Locale(models.TextChoices):
        EN = "en", "English"
        ES = "es", "Spanish"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(GameWork, on_delete=models.CASCADE, related_name="aliases")
    locale = models.CharField(max_length=2, choices=Locale.choices)
    value = models.CharField(max_length=300)
    normalized_value = models.CharField(max_length=300, db_index=True)

    class Meta:
        ordering = ("work_id", "locale", "value")
        constraints = [
            models.UniqueConstraint(
                fields=("work", "locale", "normalized_value"),
                name="catalogue_unique_alias_per_work_locale",
            )
        ]
        indexes = [
            GinIndex(fields=["normalized_value"], name="catalogue_alias_trgm_gin", opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self) -> str:
        return f"{self.value} ({self.locale})"


class RelatedContent(models.Model):
    """DLC/expansion linkage: child content lives inside the parent's page,
    never as an independent catalogue result or backlog entry (D-11)."""

    class Relation(models.TextChoices):
        DLC = "dlc", "DLC"
        EXPANSION = "expansion", "Expansion"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_work = models.ForeignKey(GameWork, on_delete=models.CASCADE, related_name="related_children")
    child_work = models.ForeignKey(GameWork, on_delete=models.CASCADE, related_name="related_parents")
    relation = models.CharField(max_length=16, choices=Relation.choices)

    class Meta:
        ordering = ("parent_work_id", "child_work_id")
        constraints = [
            models.UniqueConstraint(
                fields=("parent_work", "child_work"),
                name="catalogue_unique_related_content_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(parent_work=models.F("child_work")),
                name="catalogue_related_content_no_self_reference",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.parent_work} -> {self.child_work} ({self.relation})"


class SourceRecord(models.Model):
    """Provenance for a work's canonical identity (CAT-04, DATA-02): the
    external source is retained here only, never as the primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(GameWork, on_delete=models.CASCADE, related_name="source_records")
    source = models.CharField(max_length=50)
    source_id = models.CharField(max_length=50)
    source_url = models.URLField(max_length=500)
    retrieved_at = models.DateTimeField()
    licence = models.CharField(max_length=100)
    snapshot_sha256 = models.CharField(max_length=64)

    class Meta:
        ordering = ("work_id", "source")
        constraints = [
            models.UniqueConstraint(
                fields=("source", "source_id"),
                name="catalogue_unique_source_identity",
            )
        ]

    def __str__(self) -> str:
        return f"{self.source}:{self.source_id}"


class AssetAttribution(models.Model):
    """Per-file cover licence review (D-07). display_allowed is False by
    default; only a reviewed, complete record may ever flip it true."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(GameWork, on_delete=models.CASCADE, related_name="assets")
    local_path = models.CharField(max_length=500, blank=True)
    creator = models.CharField(max_length=300, blank=True)
    licence = models.CharField(max_length=150, blank=True)
    licence_url = models.URLField(max_length=500, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    file_url = models.URLField(max_length=500, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    display_allowed = models.BooleanField(default=False)

    class Meta:
        ordering = ("work_id", "id")

    def __str__(self) -> str:
        return f"asset for {self.work} ({'allowed' if self.display_allowed else 'placeholder'})"

