"""Catalogue DTOs (CAT-03/CAT-04): text-only, allowlisted fields, provenance
always included, DLC/expansions rendered as non-actionable child content."""

from __future__ import annotations

from rest_framework import serializers

from catalogue.models import AssetAttribution, GameRelease, GameWork
from catalogue.ratings import display_rating


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


def _genres(work: GameWork) -> list[dict]:
    return [{"slug": g.slug, "name": g.name} for g in work.genres.all()]


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
    display_rating = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()

    def get_title(self, work: GameWork) -> str:
        return _display_title(work)

    def get_year(self, work: GameWork) -> int | None:
        return _release_year(work)

    def get_display_rating(self, work: GameWork) -> float | None:
        return display_rating(work)

    def get_platform_summary(self, work: GameWork) -> str:
        return _platform_summary(work)

    def get_cover(self, work: GameWork) -> dict:
        return _cover(work)

    def get_genres(self, work: GameWork) -> list[dict]:
        return _genres(work)


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
    """DLC/expansions: identity only, no action affordance in the DTO
    itself (D-11) -- the client renders these as non-actionable."""

    id = serializers.UUIDField(source="child_work.id")
    slug = serializers.CharField(source="child_work.canonical_slug")
    title = serializers.SerializerMethodField()
    relation = serializers.CharField()

    def get_title(self, related) -> str:  # noqa: ANN001 - RelatedContent instance
        return _display_title(related.child_work)


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
    # IGDB synopsis (D-24 P3) -- a blank string when IGDB carries none; the
    # client omits the whole section rather than render an empty heading.
    summary = serializers.CharField(allow_blank=True)
    total_rating = serializers.FloatField(allow_null=True)
    # IGDB *user* rating (D-05) and its sample size, surfaced for the
    # detail-page rating breakdown line.
    rating = serializers.FloatField(allow_null=True)
    rating_count = serializers.IntegerField(allow_null=True)
    display_rating = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    releases = serializers.SerializerMethodField()
    related_content = serializers.SerializerMethodField()
    provenance = serializers.SerializerMethodField()

    def get_title(self, work: GameWork) -> str:
        return _display_title(work)

    def get_year(self, work: GameWork) -> int | None:
        return _release_year(work)

    def get_display_rating(self, work: GameWork) -> float | None:
        return display_rating(work)

    def get_genres(self, work: GameWork) -> list[dict]:
        return _genres(work)

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
