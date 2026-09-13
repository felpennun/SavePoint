"""Server-side visibility decisions for profiles and social projections."""

from __future__ import annotations

from enum import Enum

from social.models import Block, Friendship


class ProfileAccess(str, Enum):
    """The only profile projections a viewer may receive."""

    OWNER = "owner"
    ACCEPTED_FRIEND = "accepted_friend"
    BASIC = "basic"
    HIDDEN = "hidden"


def _authenticated(viewer) -> bool:  # noqa: ANN001
    return viewer is not None and bool(getattr(viewer, "is_authenticated", False))


def _blocked(first, second) -> bool:  # noqa: ANN001
    return Block.objects.filter(is_active=True, blocker=first, blocked=second).exists() or Block.objects.filter(
        is_active=True, blocker=second, blocked=first
    ).exists()


def _accepted_friend(first, second) -> bool:  # noqa: ANN001
    low_id, high_id = sorted((first.pk, second.pk))
    return Friendship.objects.filter(
        pair__low_user_id=low_id, pair__high_user_id=high_id
    ).exists()


def resolve_profile_access(*, viewer, owner) -> ProfileAccess:  # noqa: ANN001
    """Resolve access from the session actor and relationship state."""
    if not getattr(owner, "is_active", False):
        return ProfileAccess.HIDDEN
    if not _authenticated(viewer):
        return ProfileAccess.BASIC
    if viewer.pk == owner.pk:
        return ProfileAccess.OWNER
    if _blocked(viewer, owner):
        return ProfileAccess.HIDDEN
    if _accepted_friend(viewer, owner):
        return ProfileAccess.ACCEPTED_FRIEND
    return ProfileAccess.BASIC


def can_view_shared_content(*, viewer, owner) -> bool:  # noqa: ANN001
    """Return whether a viewer can enter a collection/list projection."""
    return resolve_profile_access(viewer=viewer, owner=owner) in {
        ProfileAccess.OWNER,
        ProfileAccess.ACCEPTED_FRIEND,
    }
