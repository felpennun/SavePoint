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


class Franchise(models.Model):
    """A stable IGDB franchise facet used only when the governed data covers it."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    igdb_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Theme(models.Model):
    """An IGDB ``themes`` facet (setting/tone: Fantasy, Horror, Open world...).

    Identity is the stable upstream IGDB theme id, never the internal UUID, so
    the facet can be re-pointed at a different provider later without
    renumbering. Persisted from the catalogue import as an additive M2M only;
    it is deliberately NOT folded into the content checksum or the governed
    corpus, and no recommender consumes it until an explicit later version
    with its own feature cache and evaluation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    igdb_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class PlayerPerspective(models.Model):
    """An IGDB ``player_perspectives`` facet (First person, Bird view...).

    Same additive, non-governed contract as :class:`Theme`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    igdb_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class GameMode(models.Model):
    """An IGDB ``game_modes`` facet (Single player, Co-operative, MMO...).

    Same additive, non-governed contract as :class:`Theme`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    igdb_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Keyword(models.Model):
    """An IGDB ``keywords`` free-form community tag.

    Unlike the closed vocabularies above, IGDB keywords are an unbounded,
    ungoverned set (tens of thousands, with synonyms and noise). This model
    stores them verbatim from the import; any normalisation, synonym
    collapsing, denylisting or frequency filtering is a separate, versioned
    curation step and does not belong here. Same additive, non-governed,
    not-yet-in-any-recommender contract as :class:`Theme`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    igdb_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Subgenre(models.Model):
    """A curated, versioned subgenre derived from raw IGDB keywords.

    ``Keyword`` remains the immutable-ish raw provider layer. This separate
    entity is the only layer that a recommender may consume after an explicit
    curation run has published its versioned mapping.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    curation_version = models.CharField(max_length=64)
    source_keywords = models.ManyToManyField(
        Keyword,
        through="SubgenreKeyword",
        related_name="subgenres",
    )

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class SubgenreKeyword(models.Model):
    """Traceable link from one raw IGDB keyword to one canonical subgenre."""

    subgenre = models.ForeignKey(Subgenre, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("subgenre", "keyword"),
                name="catalogue_unique_subgenre_keyword",
            )
        ]


class CuratedLabel(models.Model):
    """Versioned editorial label exposed by the catalogue taxonomy.

    The label list intentionally spans genres, subgenres, themes, modes and
    product features. ``kind`` preserves that semantic distinction for
    recommenders while the UI may present one unified filter vocabulary.
    """

    class Kind(models.TextChoices):
        GENRE = "genre", "Genre"
        SUBGENRE = "subgenre", "Subgenre"
        THEME = "theme", "Theme"
        MODE = "mode", "Mode"
        FEATURE = "feature", "Feature"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    curation_version = models.CharField(max_length=64)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Developer(models.Model):
    """An IGDB company explicitly marked as a developer for a work."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    igdb_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

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
    franchises = models.ManyToManyField(Franchise, blank=True, related_name="works")
    developers = models.ManyToManyField(Developer, blank=True, related_name="works")
    # Additive IGDB classification facets (import-only, not governed, not yet
    # consumed by any recommender -- see the model docstrings). Kept off the
    # content checksum so attaching them never perturbs the frozen catalogue
    # evidence.
    themes = models.ManyToManyField(Theme, blank=True, related_name="works")
    player_perspectives = models.ManyToManyField(
        PlayerPerspective, blank=True, related_name="works"
    )
    game_modes = models.ManyToManyField(GameMode, blank=True, related_name="works")
    keywords = models.ManyToManyField(Keyword, blank=True, related_name="works")
    subgenres = models.ManyToManyField(Subgenre, blank=True, related_name="works")
    curated_labels = models.ManyToManyField(
        CuratedLabel,
        through="GameWorkCuratedLabel",
        blank=True,
        related_name="works",
    )

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


class GameWorkCuratedLabel(models.Model):
    """Traceable evidence linking a work to one editorial label."""

    class SourceKind(models.TextChoices):
        GENRE = "genre", "Genre"
        THEME = "theme", "Theme"
        GAME_MODE = "game_mode", "Game mode"
        PLAYER_PERSPECTIVE = "player_perspective", "Player perspective"
        KEYWORD = "keyword", "Keyword"
        SUBGENRE = "subgenre", "Subgenre"

    work = models.ForeignKey(GameWork, on_delete=models.CASCADE)
    label = models.ForeignKey(CuratedLabel, on_delete=models.CASCADE)
    source_kind = models.CharField(max_length=24, choices=SourceKind.choices)
    source_value = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("work", "label", "source_kind", "source_value"),
                name="catalogue_unique_curated_label_evidence",
            )
        ]
        indexes = [
            models.Index(
                fields=("label", "work"),
                name="cat_cur_label_work_idx",
            )
        ]


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
    """Immutable external rating observation attached to a corpus version.

    ``rating_count`` is the count attached to the displayed user rating,
    whereas ``total_rating_count`` is IGDB's broader count used as the frozen
    volume signal.  They are intentionally stored separately.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(
        GameWork, on_delete=models.CASCADE, related_name="rating_snapshots"
    )
    corpus_version = models.CharField(max_length=32)
    source = models.CharField(max_length=16)
    rating = models.FloatField(null=True, blank=True)
    rating_count = models.PositiveIntegerField(default=0)
    total_rating_count = models.PositiveIntegerField(null=True, blank=True)
    retrieved_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("work", "corpus_version", "source"),
                name="catalogue_unique_rating_snapshot",
            )
        ]


class CorpusPopularitySnapshot(models.Model):
    """One immutable IGDB PopScore primitive captured for a corpus version.

    IGDB exposes primitives rather than one canonical aggregate.  Persisting
    them separately preserves the original measurement and leaves any future
    composition explicit, reproducible and independently ablatable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(
        GameWork, on_delete=models.CASCADE, related_name="popularity_snapshots"
    )
    corpus_version = models.CharField(max_length=32)
    popularity_type_id = models.PositiveIntegerField()
    popularity_type_name = models.CharField(max_length=120)
    external_source = models.CharField(max_length=120, blank=True)
    value = models.FloatField()
    normalised_value = models.FloatField(null=True, blank=True)
    calculated_at = models.DateTimeField(null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    retrieved_at = models.DateTimeField()
    payload_sha256 = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("work", "corpus_version", "popularity_type_id"),
                name="catalogue_unique_popularity_snapshot",
            )
        ]
        indexes = [
            models.Index(
                fields=("corpus_version", "popularity_type_id"),
                name="catalogue_pop_ver_type_idx",
            )
        ]


class CorpusPopularityScore(models.Model):
    """Materialised versioned PopScore for one work and corpus version."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(
        GameWork, on_delete=models.CASCADE, related_name="popularity_scores"
    )
    corpus_version = models.CharField(max_length=32)
    score = models.FloatField()
    formula_version = models.CharField(max_length=64)
    calculated_at = models.DateTimeField()
    source_snapshot_sha256 = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("work", "corpus_version"),
                name="catalogue_unique_popularity_score",
            )
        ]
        indexes = [
            models.Index(
                fields=("corpus_version", "score"),
                name="catalogue_pop_score_idx",
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


class NewReleasesSnapshot(models.Model):
    """The materialised home "Novedades" shelf (D-24).

    The shelf ranking (``0.70 * recency + 0.30 * PopScore`` over the last
    ~183 days) is recomputed only when the IGDB catalogue is re-imported --
    never per request. Until then the release window and the PopScore
    inputs do not move, so every page load serves this frozen ordered list.
    Exactly one row (``pk = 1``); ``work_ids`` is the ordered list of
    ``GameWork`` primary keys, already capped at the shelf limit.
    """

    SINGLETON_PK = 1

    id = models.PositiveSmallIntegerField(primary_key=True, default=SINGLETON_PK)
    work_ids = models.JSONField(default=list)
    formula = models.CharField(max_length=64, default="recency-0.70-popscore-0.30-v1")
    computed_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"NewReleasesSnapshot({len(self.work_ids)} works @ {self.computed_at:%Y-%m-%d %H:%M})"