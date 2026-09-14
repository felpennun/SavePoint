"""The sole administrative surface for platform operations."""

from __future__ import annotations

from django.contrib.admin import AdminSite

from evaluation.access import PLATFORM_ADMIN_PERMISSION


class PlatformAdminSite(AdminSite):
    """Django Admin site gated by a project capability, not staff status."""

    site_header = "SavePoint Platform Admin"
    site_title = "SavePoint Platform Admin"
    index_title = "Platform operations"

    def has_permission(self, request) -> bool:  # noqa: ANN001
        user = request.user
        return bool(
            getattr(user, "is_authenticated", False)
            and getattr(user, "is_active", False)
            and user.has_perm(PLATFORM_ADMIN_PERMISSION)
        )


platform_admin_site = PlatformAdminSite(name="platform-admin")


def register_platform_models(site: PlatformAdminSite = platform_admin_site) -> None:
    """Register only the reviewed ModelAdmin allowlist on this site."""
    from accounts.admin import register_platform_admin_models
    from audit.admin import register_platform_admin_models as register_audit
    from catalogue.admin import register_platform_admin_models as register_catalogue
    from evaluation.admin import register_platform_admin_models as register_evaluation
    from library.admin import register_platform_admin_models as register_library
    from recommendations.admin import register_platform_admin_models as register_recommendations

    register_evaluation(site)
    register_platform_admin_models(site)
    register_audit(site)
    register_catalogue(site)
    register_library(site)
    register_recommendations(site)


register_platform_models()
