"""Server-side capabilities for the read-only research publication API."""

from __future__ import annotations

from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission


RESEARCH_VIEW_PERMISSION = "evaluation.view_research_panel"
PLATFORM_ADMIN_PERMISSION = "accounts.manage_platform"
PLATFORM_ADMIN_FALLBACK_PERMISSION = "auth.change_user"


def can_view_research(user) -> bool:  # noqa: ANN001
    """Return the research capability from Django permissions only."""

    return bool(
        getattr(user, "is_authenticated", False)
        and user.has_perm(RESEARCH_VIEW_PERMISSION)
    )


def can_manage_platform(user) -> bool:  # noqa: ANN001
    """Return the separately granted platform-admin capability.

    ``accounts.manage_platform`` is the project capability.  The built-in
    user-management permission remains an explicit compatibility fallback for
    Django Admin installations that have not provisioned the project alias.
    Neither branch relies on ``is_staff`` or a frontend assertion.
    """

    if not getattr(user, "is_authenticated", False):
        return False
    return bool(
        user.has_perm(PLATFORM_ADMIN_PERMISSION)
        or user.has_perm(PLATFORM_ADMIN_FALLBACK_PERMISSION)
    )


class ResearchViewerPermission(BasePermission):
    """Allow published research reads, hiding the surface from other users.

    DRF turns the ``False`` result for an anonymous request into its normal
    authentication response.  An authenticated user without the capability
    receives the same neutral 404 used for an unknown resource.
    """

    def has_permission(self, request, view) -> bool:  # noqa: ANN001
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        if not can_view_research(user):
            raise NotFound("Not found.")
        return True


__all__ = [
    "PLATFORM_ADMIN_FALLBACK_PERMISSION",
    "PLATFORM_ADMIN_PERMISSION",
    "RESEARCH_VIEW_PERMISSION",
    "ResearchViewerPermission",
    "can_manage_platform",
    "can_view_research",
]
