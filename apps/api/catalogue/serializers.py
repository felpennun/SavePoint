"""Catalogue DTOs (CAT-03/CAT-04): text-only, allowlisted fields, provenance
always included, DLC/expansions rendered as non-actionable child content."""

from __future__ import annotations

from rest_framework import serializers

from catalogue.models import AssetAttribution, GameRelease, GameWork
from catalogue.ratings import display_rating, rating_breakdown

# Serializer context key carrying a pre-computed {work_id: (mean_x10, count)}
# map so list rendering stays query-bounded (see ratings.savepoint_rating_stats).
SAVEPOINT_STATS_CONTEXT_KEY = "savepoint_stats"


def _display_rating_for(serializer: serializers.Serializer, work: GameWork) -> float | None:
    stats_map = serializer.context.get(SAVEPOINT_STATS_CONTEXT_KEY)
    if stats_map is None:
        return display_rating(work)
    return display_rating(work, savepoint_stats=stats_map.get(work.id, (None, 0)))


def _display_title(work: GameWork) -> str:
    return work.title_en or work.original_title


def _release_year(work: GameWork) -> int | None:
    # Prefer the denormalised scalar (one indexed column, no join); fall back
    # to the releases for rows imported before it was populated.
    frd = getattr(work, "first_release_date", None)
    if frd:
        return frd.year
    dated = [r.release_date for r in work.releases.all() if r.release_date]
    return min(d.year for d in dated) if dated else None


def _tags(work: GameWork) -> list[dict]:
    # GameWorkCuratedLabel is an evidence table, not a plain tag-assignment
    # M2M: curate_labels can (deliberately) record more than one row for the
    # same (work, label) pair -- e.g. both an IGDB theme and a subgenre
    # independently mapping to the same curated tag -- to keep the curation
    # provenance auditable. A naive work.curated_labels.all() therefore
    # yields the same CuratedLabel once per evidence row, which rendered as
    # visibly duplicated tag chips (2026-09-12, reported live). Dedupe by
    # slug here, first occurrence wins; the underlying evidence rows are
    # untouched and still queryable for provenance.
    seen: dict[str, dict] = {}
    for tag in work.curated_labels.all():
        seen.setdefault(tag.slug, {"slug": tag.slug, "name": tag.name})
    return list(seen.values())


def _platform_summary(work: GameWork) -> str:
    names = sorted({r.platform.name for r in work.releases.all() if r.platform_id})
    if not names:
        return "Not available"
    if len(names) <= 3:
        return ", ".join(names)
    return f"{', '.join(names[:2])} +{len(names) - 2}"


def _cover(work: GameWork) -> dict:
    approved = next((a for a in work.assets.all() if a.display_allowed), None)
    if approved is None:
        return {"url": None, "is_placeholder": True, "alt": _display_title(work)}
    return {
        "url": approved.file_url,
        "is_placeholder": False,
        "alt": _display_title(work),
        "attribution": {
            "creator": approved.creator,
            "licence": approved.licence,
            "licence_url": approved.licence_url,
            "source_url": approved.source_url,
        },
    }


class GameCardSerializer(serializers.Serializer):
    """List/search result card -- CAT-01/CAT-06."""

    id = serializers.UUIDField()
    slug = serializers.CharField(source="canonical_slug")
    title = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    platform_summary = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    # ``total_rating`` is the IGDB user+critic blend and remains the key the
    # catalogue sort / ``min_rating`` filter operate on (Plan 02-05 flagged
    # assumption 2). ``display_rating`` is the live product number (D-09):
    # null when no source has a value, so "sin valoración" is explicit.
    total_rating = serializers.FloatField(allow_null=True)
    total_rating_count = serializers.IntegerField(allow_null=True)
    display_rating = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_title(self, work: GameWork) -> str:
        return _display_title(work)

    def get_year(self, work: GameWork) -> int | None:
        return _release_year(work)

    def get_display_rating(self, work: GameWork) -> float | None:
        return _display_rating_for(self, work)

    def get_platform_summary(self, work: GameWork) -> str:
        return _platform_summary(work)

    def get_cover(self, work: GameWork) -> dict:
        return _cover(work)

    def get_tags(self, work: GameWork) -> list[dict]:
        return _tags(work)


class ReleaseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    release_name = serializers.CharField()
    release_date = serializers.DateField(allow_null=True)
    platform = serializers.SerializerMethodField()
    # id+name pairs, not just names -- the copy-creation form (D-15) needs
    # a real edition_id to submit, not just a display label.
    editions = serializers.SerializerMethodField()

    def get_platform(self, release: GameRelease) -> str | None:
        return release.platform.name if release.platform_id else None

    def get_editions(self, release: GameRelease) -> list[dict]:
        return [{"id": str(edition.id), "name": edition.name} for edition in release.editions.all()]


class RelatedContentSerializer(serializers.Serializer):
    """DLC/expansions: display metadata, but no independent action affordance."""

    id = serializers.UUIDField(source="child_work.id")
    slug = serializers.CharField(source="child_work.canonical_slug")
    title = serializers.SerializerMethodField()
    relation = serializers.CharField()
    year = serializers.SerializerMethodField()
    platform_summary = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    def get_title(self, related) -> str:  # noqa: ANN001 - RelatedContent instance
        return _display_title(related.child_work)

    def get_year(self, related) -> int | None:  # noqa: ANN001 - RelatedContent instance
        return _release_year(related.child_work)

    def get_platform_summary(self, related) -> str:  # noqa: ANN001 - RelatedContent instance
        return _platform_summary(related.child_work)

    def get_cover(self, related) -> dict:  # noqa: ANN001 - RelatedContent instance
        return _cover(related.child_work)


class ProvenanceSerializer(serializers.Serializer):
    """Always-visible provenance summary (CAT-03/DATA-02)."""

    source = serializers.CharField()
    source_id = serializers.CharField()
    source_url = serializers.CharField()
    licence = serializers.CharField()
    retrieved_at = serializers.DateTimeField()
    snapshot_sha256 = serializers.CharField()


class GameDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    slug = serializers.CharField(source="canonical_slug")
    title = serializers.SerializerMethodField()
    title_en = serializers.CharField()
    title_es = serializers.CharField()
    original_title = serializers.CharField()
    is_dlc = serializers.BooleanField()
    year = serializers.SerializerMethodField()
    # The English source summary is kept separate from the optional Spanish
    # editorial translation. A Spanish request must never receive English
    # text as a silent fallback.
    summary = serializers.SerializerMethodField()
    total_rating = serializers.FloatField(allow_null=True)
    total_rating_count = serializers.IntegerField(allow_null=True)
    # IGDB *user* rating (D-05) and its sample size, surfaced for the
    # detail-page rating breakdown line.
    rating = serializers.FloatField(allow_null=True)
    rating_count = serializers.IntegerField(allow_null=True)
    display_rating = serializers.SerializerMethodField()
    # Aggregate-only counts for the detail-page rating breakdown line
    # (never per-user rows -- threat T-02-05-02).
    rating_breakdown = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    releases = serializers.SerializerMethodField()
    related_content = serializers.SerializerMethodField()
    provenance = serializers.SerializerMethodField()

    def get_title(self, work: GameWork) -> str:
        return _display_title(work)

    def get_summary(self, work: GameWork) -> str:
        if self.context.get("locale") == "es":
            return work.summary_es
        return work.summary

    def get_year(self, work: GameWork) -> int | None:
        return _release_year(work)

    def get_display_rating(self, work: GameWork) -> float | None:
        return _display_rating_for(self, work)

    def get_rating_breakdown(self, work: GameWork) -> dict[str, int]:
        return rating_breakdown(work)

    def get_tags(self, work: GameWork) -> list[dict]:
        return _tags(work)

    def get_cover(self, work: GameWork) -> dict:
        return _cover(work)

    def get_releases(self, work: GameWork) -> list[dict]:
        releases = work.releases.select_related("platform").prefetch_related("editions").all()
        return ReleaseSerializer(releases, many=True).data

    def get_related_content(self, work: GameWork) -> list[dict]:
        related = work.related_children.select_related("child_work").all()
        return RelatedContentSerializer(related, many=True).data

    def get_provenance(self, work: GameWork) -> dict | None:
        # Always visible per UI-SPEC -- absent only if a work somehow has no
        # SourceRecord, which the import command never produces; explicit
        # "missing" is safer than a serializer crash for that edge case.
        # Prefer the IGDB record (the enrichment source for summary/rating),
        # falling back to whatever provenance row exists. Iterates the
        # prefetched list so this stays a single query.
        records = list(work.source_records.all())
        if not records:
            return None
        record = next((r for r in records if r.source == "igdb"), records[0])
        return ProvenanceSerializer(record).data
