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


class Genre(models.Model):
    """A catalogue genre facet (CAT-02 filter/sort, REC-10 heuristic input).

    Deliberately minimal: Franchise / Developer / Publisher / GameMode / Tag
    are CAT-05 scope, assigned to Phase 4 in ROADMAP.md, and are NOT added
    here (01.1-RESEARCH.md Architecture Pattern 3). Identity is the stable
    upstream IGDB genre id, never the internal UUID, so the facet can be
    re-pointed at a different provider later without renumbering.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    igdb_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class GameWork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_slug = models.SlugField(max_length=200, unique=True)
    original_title = models.CharField(max_length=300)
    title_en = models.CharField(max_length=300, blank=True)
    title_es = models.CharField(max_length=300, blank=True)
    is_dlc = models.BooleanField(default=False)
    # Denormalised IGDB primary-work scalars (CAT-02 filter/sort). Kept on the
    # work itself so the year-range and rating filters/sorts are a single
    # indexed btree scan instead of a GROUP BY over 300k+ releases (threat
    # T-01.1-06, aggregate-filter DoS). ``first_release_date`` mirrors
    # ``min(releases.release_date)``; ``total_rating`` is IGDB ``total_rating``
    # on a 0-100 scale (null = unrated).
    first_release_date = models.DateField(null=True, blank=True)
    total_rating = models.FloatField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    rating_count = models.PositiveIntegerField(null=True, blank=True)
    total_rating_count = models.PositiveIntegerField(null=True, blank=True)
    # Governed-corpus state is deliberately additive and reversible. The
    # source catalogue remains intact for later discovery phases.
    in_corpus = models.BooleanField(default=False)
    corpus_version = models.CharField(max_length=32, blank=True)
    summary = models.TextField(blank=True)
    # Optional editorial translation for the Spanish UI. The source summary
    # remains intact in ``summary``; the API never displays it as Spanish.
    summary_es = models.TextField(blank=True)
    genres = models.ManyToManyField(Genre, blank=True, related_name="works")

    class Meta:
        ordering = ("original_title", "id")
        indexes = [
            models.Index(fields=["original_title"], name="catalogue_work_title_idx"),
            models.Index(fields=["first_release_date"], name="catalogue_work_release_idx"),
            models.Index(fields=["total_rating"], name="catalogue_work_rating_idx"),
            models.Index(
                fields=["in_corpus", "first_release_date"],
                name="catalogue_work_corpus_idx",
            ),
        ]

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
        indexes = [
            models.Index(fields=["release_date"], name="catalogue_release_date_idx"),
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


class CorpusRatingSnapshot(models.Model):
    """Immutable external rating observation attached to a corpus version."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(
        GameWork, on_delete=models.CASCADE, related_name="rating_snapshots"
    )
    corpus_version = models.CharField(max_length=32)
    source = models.CharField(max_length=16)
    rating = models.FloatField(null=True, blank=True)
    rating_count = models.PositiveIntegerField(default=0)
    retrieved_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("work", "corpus_version", "source"),
                name="catalogue_unique_rating_snapshot",
            )
        ]


class CorpusVersion(models.Model):
    """Metadata for one governed-corpus ruleset and its active view."""

    version = models.CharField(max_length=32, primary_key=True)
    ruleset_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    governed_count = models.PositiveIntegerField(default=0)


class IgdbImportRun(models.Model):
    """Durable, resumable checkpoint for the batched IGDB catalogue import
    (01.1-RESEARCH.md Architecture Patterns 1-2).

    One row per (source, query_identity). ``query_identity`` records the
    *non-secret* Apicalypse boundary (e.g. ``game_type=0``) -- never a token
    or connection string. ``last_committed_igdb_id`` is the id-cursor: it is
    written inside the same transaction that commits its batch, and a
    database trigger forbids it from ever moving backwards, so an interrupted
    run always resumes forward from real committed progress.
    """

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        INTERRUPTED = "interrupted", "Interrupted"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=50, default="igdb")
    query_identity = models.CharField(max_length=200)
    last_committed_igdb_id = models.BigIntegerField(default=0)
    # In-progress cursor for the CURRENT pass. Unlike last_committed_igdb_id
    # (a monotonic, trigger-guarded high-water mark used as the evidence
    # boundary), this is reset to 0 whenever a fresh pass begins and is the
    # value a resume actually restarts from -- so a chunked re-import after a
    # COMPLETE pass can no longer jump forward to the stale high-water mark
    # and silently skip the range in between (repo-review 2026-09-06 H-02).
    pass_cursor = models.BigIntegerField(default=0)
    batches_committed = models.PositiveIntegerField(default=0)
    works_imported = models.PositiveIntegerField(default=0)
    works_updated = models.PositiveIntegerField(default=0)
    genres_seen = models.PositiveIntegerField(default=0)
    covers_present = models.PositiveIntegerField(default=0)
    covers_fallback = models.PositiveIntegerField(default=0)
    eligible_count_live = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    error_summary = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-started_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("source", "query_identity"),
                name="catalogue_unique_igdb_import_identity",
            ),
            models.CheckConstraint(
                condition=models.Q(last_committed_igdb_id__gte=0),
                name="catalogue_igdb_cursor_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source}:{self.query_identity}@{self.last_committed_igdb_id} ({self.status})"


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

