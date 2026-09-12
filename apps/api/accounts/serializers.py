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

from accounts.models import AVATAR_URL_MAX_LENGTH, BIO_MAX_LENGTH, AccountProfile, ProfileVisibility
from library.models import BacklogStatus, LibraryEntry

User = get_user_model()

_STATUS_ORDER = [choice.value for choice in BacklogStatus]
_VISIBILITY_CHOICES = [choice.value for choice in ProfileVisibility]


def _escape_text(value: str) -> str:
    """Alias/title text is returned as plain text, never markup -- the
    client renders it, it never becomes HTML/URLs here (XSS boundary)."""
    return str(value)


def build_public_profile(user) -> dict:  # noqa: ANN001
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

    # Explicit allowlist -- every key here is intentional. Do not replace
    # this dict construction with a model/serializer that could pull in
    # unreviewed fields by accident.
    return {
        "alias": _escape_text(user.username),
        "activity": activity,
        "summary": summary,
    }


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
