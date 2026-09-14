"""Explicit catalogue ModelAdmin projections for platform operators."""

from django.contrib import admin

from accounts.admin import PlatformModelAdmin
from catalogue.models import CorpusVersion, Edition, GameRelease, GameWork, IgdbImportRun, SourceRecord


class GameWorkAdmin(PlatformModelAdmin):
    list_display = ("original_title", "canonical_slug", "in_corpus", "is_dlc", "first_release_date")
    list_filter = ("in_corpus", "is_dlc")
    search_fields = ("original_title", "title_en", "title_es", "canonical_slug")
    fields = (
        "canonical_slug",
        "original_title",
        "title_en",
        "title_es",
        "is_dlc",
        "first_release_date",
        "total_rating",
        "rating",
        "rating_count",
        "total_rating_count",
        "in_corpus",
        "corpus_version",
        "summary",
        "summary_es",
    )


class GameReleaseAdmin(PlatformModelAdmin):
    list_display = ("release_name", "work", "platform", "release_date")
    list_filter = ("platform",)
    search_fields = ("release_name", "work__original_title")
    fields = ("work", "platform", "release_name", "release_date")


class EditionAdmin(PlatformModelAdmin):
    list_display = ("name", "release")
    search_fields = ("name", "release__release_name", "release__work__original_title")
    fields = ("release", "name")


class ReadOnlyCatalogueAdmin(PlatformModelAdmin):
    def get_readonly_fields(self, request, obj=None):  # noqa: ANN001, ARG002
        return tuple(field.name for field in self.model._meta.concrete_fields)

    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return False


class CorpusVersionAdmin(ReadOnlyCatalogueAdmin):
    list_display = ("version", "is_active", "governed_count", "created_at")
    fields = ("version", "ruleset_sha256", "created_at", "is_active", "governed_count")


class IgdbImportRunAdmin(ReadOnlyCatalogueAdmin):
    list_display = ("source", "query_identity", "status", "updated_at", "checksum")
    list_filter = ("status", "source")
    search_fields = ("query_identity", "source")
    fields = (
        "id",
        "source",
        "query_identity",
        "last_committed_igdb_id",
        "pass_cursor",
        "batches_committed",
        "works_imported",
        "works_updated",
        "genres_seen",
        "covers_present",
        "covers_fallback",
        "eligible_count_live",
        "checksum",
        "status",
        "error_summary",
        "started_at",
        "updated_at",
    )
    readonly_fields = fields


class SourceRecordAdmin(ReadOnlyCatalogueAdmin):
    list_display = ("source", "source_id", "work", "retrieved_at")
    fields = ("id", "work", "source", "source_id", "source_url", "retrieved_at", "licence", "snapshot_sha256")
    readonly_fields = fields


def register_platform_admin_models(site) -> None:  # noqa: ANN001
    for model, model_admin in (
        (GameWork, GameWorkAdmin),
        (GameRelease, GameReleaseAdmin),
        (Edition, EditionAdmin),
        (CorpusVersion, CorpusVersionAdmin),
        (IgdbImportRun, IgdbImportRunAdmin),
        (SourceRecord, SourceRecordAdmin),
    ):
        site.register(model, model_admin)
