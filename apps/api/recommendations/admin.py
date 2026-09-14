"""Read-only operational views for recommendation jobs and snapshots."""

from django.contrib import admin

from accounts.admin import PlatformModelAdmin
from recommendations.models import (
    RecommendationRefreshJob,
    RecommendationSignalCache,
    RecommendationSnapshot,
    RecommendationState,
    WorkFeatureVector,
)


class ReadOnlyRecommendationAdmin(PlatformModelAdmin):
    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ANN001, ARG002
        return False


class RecommendationRefreshJobAdmin(ReadOnlyRecommendationAdmin):
    list_display = ("user", "algorithm_id", "status", "attempts", "available_at", "updated_at")
    list_filter = ("status", "algorithm_id")
    search_fields = ("user__username", "algorithm_id", "configuration_fingerprint")
    fields = (
        "id", "user", "requested_revision", "configuration_fingerprint", "algorithm_id", "status",
        "attempts", "available_at", "locked_at", "last_error", "created_at", "updated_at",
    )
    readonly_fields = fields


class RecommendationSnapshotAdmin(ReadOnlyRecommendationAdmin):
    list_display = ("user", "collection_revision", "corpus_version", "feature_set_version", "generated_at")
    search_fields = ("user__username", "input_fingerprint", "configuration_fingerprint")
    fields = (
        "id", "user", "collection_revision", "input_fingerprint", "configuration_fingerprint",
        "corpus_version", "feature_set_version", "generated_at", "created_at",
    )
    readonly_fields = fields


class RecommendationStateAdmin(ReadOnlyRecommendationAdmin):
    list_display = ("user", "collection_revision", "active_snapshot", "updated_at")
    fields = ("user", "collection_revision", "active_snapshot", "updated_at")
    readonly_fields = fields


class RecommendationSignalCacheAdmin(ReadOnlyRecommendationAdmin):
    list_display = ("user", "requested_revision", "configuration_fingerprint", "corpus_version", "created_at")
    fields = ("id", "user", "requested_revision", "configuration_fingerprint", "corpus_version", "created_at")
    readonly_fields = fields


class WorkFeatureVectorAdmin(ReadOnlyRecommendationAdmin):
    list_display = ("work", "feature_set_version", "updated_at")
    fields = ("id", "work", "feature_set_version", "updated_at")
    readonly_fields = fields


def register_platform_admin_models(site) -> None:  # noqa: ANN001
    for model, model_admin in (
        (RecommendationRefreshJob, RecommendationRefreshJobAdmin),
        (RecommendationSnapshot, RecommendationSnapshotAdmin),
        (RecommendationState, RecommendationStateAdmin),
        (RecommendationSignalCache, RecommendationSignalCacheAdmin),
        (WorkFeatureVector, WorkFeatureVectorAdmin),
    ):
        site.register(model, model_admin)
