"""Public profile projection (PROF-02, INV-05).

This is a deliberately hand-built allowlist, never DRF's ModelSerializer
auto-introspection -- a future private field added to User/LibraryEntry/
OwnedCopy must never leak here just because it exists on the model. Only
alias, public backlog status, and aggregate counts are ever included.
Never: email, internal IDs, session data, ratings, purchase/format/
location/private-note fields, or any OwnedCopy detail.
"""

from __future__ import annotations

from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import (
    AVATAR_URL_MAX_LENGTH,
    BIO_MAX_LENGTH,
    MAX_FAVORITE_SLOT,
    MIN_FAVORITE_SLOT,
    AccountProfile,
    FavoriteSlot,
    ProfileVisibility,
)
from library.models import BacklogStatus, ContentVisibility, CustomList, GameComment, LibraryEntry
from library.serializers import serialize_profile_comment, serialize_profile_list
from social.policies import ProfileAccess, resolve_profile_access

User = get_user_model()

_STATUS_ORDER = [choice.value for choice in BacklogStatus]
_VISIBILITY_CHOICES = [choice.value for choice in ProfileVisibility]


def _escape_text(value: str) -> str:
    """Alias/title text is returned as plain text, never markup -- the
    client renders it, it never becomes HTML/URLs here (XSS boundary)."""
    return str(value)


def _serialize_public_favorites(user) -> list:  # noqa: ANN001
    """Five-position favorites shelf, ``None`` for empty slots -- the same
    stable shape whether or not the caller is authorized to see it."""
    slots_by_number = {
        slot.slot: slot
        for slot in FavoriteSlot.objects.filter(user=user).select_related("work")
    }
    return [
        None
        if (slot := slots_by_number.get(slot_number)) is None
        else {
            "work_slug": _escape_text(slot.work.canonical_slug),
            "work_title": _escape_text(slot.work.title_en or slot.work.original_title),
        }
        for slot_number in range(MIN_FAVORITE_SLOT, MAX_FAVORITE_SLOT + 1)
    ]


def _serialize_public_comments(user, *, is_owner: bool) -> list:  # noqa: ANN001
    """Public-profile comment aggregate (LIB-03/D-04/D-05): a comment's own
    ``visibility`` gates it here -- never ``collection_visibility`` or
    ``favorites_visibility``, which are independent toggles. The owner
    viewing their own profile sees every comment regardless of visibility,
    matching the owner-always-sees-own-data pattern used throughout this
    module."""
    queryset = GameComment.objects.filter(user=user).select_related("work").order_by("created_at", "id")
    if not is_owner:
        queryset = queryset.filter(visibility=ContentVisibility.PUBLIC)
    return [serialize_profile_comment(comment) for comment in queryset]


def _serialize_public_lists(user, *, is_owner: bool) -> list:  # noqa: ANN001
    """Public-profile custom-list aggregate (LIB-04/D-06/D-07): each list's
    own ``visibility`` gates it here, independent of
    ``collection_visibility``/``favorites_visibility``. The owner sees
    every list of their own regardless of visibility."""
    queryset = (
        CustomList.objects.filter(user=user).prefetch_related("items__work").order_by("created_at", "id")
    )
    if not is_owner:
        queryset = queryset.filter(visibility=ContentVisibility.PUBLIC)
    return [serialize_profile_list(custom_list) for custom_list in queryset]


def serialize_basic_profile(user, *, viewer=None) -> dict:  # noqa: ANN001
    """D-07's exact non-friend allowlist, with a contextual action only."""
    action = "login"
    if viewer is not None and getattr(viewer, "is_authenticated", False):
        from social.services import relationship_status

        action = {
            "none": "send_friend_request",
            "pending_sent": "request_sent",
            "pending_received": "review_friend_request",
        }.get(relationship_status(viewer=viewer, target=user), "send_friend_request")
    profile = getattr(user, "profile", None)
    return {
        "alias": _escape_text(user.username),
        "avatar_url": _escape_text(profile.avatar_url) if profile is not None else "",
        "bio": _escape_text(profile.bio) if profile is not None else "",
        "action": action,
    }


def _build_friend_profile(user, *, viewer=None, access: ProfileAccess) -> dict:  # noqa: ANN001
    """PRIV-01 allowlist, now also gating collection/favorites behind D-02's
    independent ``collection_visibility``/``favorites_visibility`` policies,
    plus comments/lists (LIB-03/LIB-04) whose own ``visibility`` field gates
    them independently of those two toggles (D-05/D-07).

    ``viewer`` is the requesting ``request.user`` (may be anonymous). The
    owner visiting their own profile always sees their own full data
    regardless of visibility -- everyone else gets the privacy-resolved
    projection. An account with no ``AccountProfile`` row yet (never
    edited) defaults to public, matching the pre-Phase-5 behavior where
    every account was public by design.
    """
    profile = getattr(user, "profile", None)
    is_owner = bool(viewer is not None and getattr(viewer, "is_authenticated", False) and viewer.pk == user.pk)
    collection_visible = is_owner or (
        access == ProfileAccess.ACCEPTED_FRIEND
        and (profile is None or profile.collection_visibility == ProfileVisibility.PUBLIC)
    )
    favorites_visible = is_owner or (
        access == ProfileAccess.ACCEPTED_FRIEND
        and (profile is None or profile.favorites_visibility == ProfileVisibility.PUBLIC)
    )

    if collection_visible:
        entries = (
            LibraryEntry.objects.filter(user=user, current_status__isnull=False)
            .select_related("work")
            .order_by("work__original_title", "id")
        )
        activity = [
            {
                "work_slug": _escape_text(entry.work.canonical_slug),
                "work_title": _escape_text(entry.work.title_en or entry.work.original_title),
                "status": entry.current_status,
            }
            for entry in entries
        ]
        summary = {status: 0 for status in _STATUS_ORDER}
        for entry in entries:
            summary[entry.current_status] += 1
    else:
        activity = []
        summary = {status: 0 for status in _STATUS_ORDER}

    favorites = _serialize_public_favorites(user) if favorites_visible else [None] * MAX_FAVORITE_SLOT

    # Explicit allowlist -- every key here is intentional. Do not replace
    # this dict construction with a model/serializer that could pull in
    # unreviewed fields by accident.
    return {
        "alias": _escape_text(user.username),
        "bio": _escape_text(profile.bio) if profile is not None else "",
        "avatar_url": _escape_text(profile.avatar_url) if profile is not None else "",
        "activity": activity,
        "summary": summary,
        "favorites": favorites,
        "comments": _serialize_public_comments(user, is_owner=is_owner),
        "lists": _serialize_public_lists(user, is_owner=is_owner),
    }


def build_public_profile(user, *, viewer=None) -> dict | None:  # noqa: ANN001
    """Return exactly one server-authorized profile projection."""
    access = resolve_profile_access(viewer=viewer, owner=user)
    if access == ProfileAccess.HIDDEN:
        return None
    if access == ProfileAccess.BASIC:
        return serialize_basic_profile(user, viewer=viewer)
    return _build_friend_profile(user, viewer=viewer, access=access)


class AccountProfileSerializer(serializers.Serializer):
    """Owner-facing profile update DTO (PROF-01).

    Deliberately has no ``username``/``user_id``/``owner_id`` field --
    D-01's immutable alias has nothing here it could ever change through,
    and the owner is always derived from ``request.user`` in the view, never
    from this payload (IDOR boundary).
    """

    bio = serializers.CharField(max_length=BIO_MAX_LENGTH, allow_blank=True, required=False)
    avatar_url = serializers.CharField(max_length=AVATAR_URL_MAX_LENGTH, allow_blank=True, required=False)
    collection_visibility = serializers.ChoiceField(choices=_VISIBILITY_CHOICES, required=False)
    favorites_visibility = serializers.ChoiceField(choices=_VISIBILITY_CHOICES, required=False)

    def validate_avatar_url(self, value: str) -> str:
        if value == "":
            return value
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise serializers.ValidationError("avatar_url must be an https:// URL.")
        return value


def serialize_account_profile(profile: AccountProfile) -> dict:
    """Owner-facing profile read DTO -- never includes ``username`` (D-01)
    or any internal identifier, matching the public-projection allowlist
    discipline even though this response is private to the owner."""
    return {
        "bio": _escape_text(profile.bio),
        "avatar_url": _escape_text(profile.avatar_url),
        "collection_visibility": profile.collection_visibility,
        "favorites_visibility": profile.favorites_visibility,
    }


class FavoriteSlotInputSerializer(serializers.Serializer):
    """One entry in a favorites-replace payload. Absent slots are left
    empty -- the client only ever sends the occupied positions."""

    slot = serializers.IntegerField(min_value=MIN_FAVORITE_SLOT, max_value=MAX_FAVORITE_SLOT)
    work_id = serializers.UUIDField()


class ReplaceFavoritesRequestSerializer(serializers.Serializer):
    """Full-replace payload for PUT /me/favorites/ (D-02): at most five
    entries, each in-range, no duplicate slot and no duplicate work. Actual
    collection-membership ownership is re-checked in the service layer,
    which is the only place that can see the requesting user's
    ``LibraryEntry`` rows.
    """

    slots = FavoriteSlotInputSerializer(many=True, allow_empty=True)

    def validate_slots(self, value: list[dict]) -> list[dict]:
        if len(value) > MAX_FAVORITE_SLOT:
            raise serializers.ValidationError("At most five favorite slots are allowed.")

        seen_slots: set[int] = set()
        seen_works: set[str] = set()
        for item in value:
            if item["slot"] in seen_slots:
                raise serializers.ValidationError("Duplicate slot number in payload.")
            seen_slots.add(item["slot"])

            work_id = str(item["work_id"])
            if work_id in seen_works:
                raise serializers.ValidationError("Duplicate work in payload.")
            seen_works.add(work_id)

        return value


def serialize_favorite_slots(user) -> list:  # noqa: ANN001
    """Owner-facing favorites DTO: always five positions, ``work_id`` is
    ``None`` for an empty slot."""
    slots_by_number = {
        slot.slot: slot
        for slot in FavoriteSlot.objects.filter(user=user).select_related("work")
    }
    result = []
    for slot_number in range(MIN_FAVORITE_SLOT, MAX_FAVORITE_SLOT + 1):
        slot = slots_by_number.get(slot_number)
        if slot is None:
            result.append({"slot": slot_number, "work_id": None, "work_slug": None, "work_title": None})
        else:
            result.append(
                {
                    "slot": slot_number,
                    "work_id": str(slot.work_id),
                    "work_slug": _escape_text(slot.work.canonical_slug),
                    "work_title": _escape_text(slot.work.title_en or slot.work.original_title),
                }
            )
    return result
