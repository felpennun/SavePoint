"""Transactional, owner-derived account services (Phase 5, PROF-01/PRIV-01).

Every function here takes ``user`` explicitly from the caller (the view,
which derives it from ``request.user``) and never accepts a substitutable
identity from a request payload -- the same owner-scoped pattern already
used by ``library.services``.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import AVATAR_URL_MAX_LENGTH, BIO_MAX_LENGTH, AccountProfile, ProfileVisibility

VALID_VISIBILITIES = {choice.value for choice in ProfileVisibility}


def get_or_create_profile(*, user) -> AccountProfile:  # noqa: ANN001
    profile, _ = AccountProfile.objects.get_or_create(user=user)
    return profile


def update_profile(
    *,
    user,  # noqa: ANN001
    bio: str | None = None,
    avatar_url: str | None = None,
    collection_visibility: str | None = None,
    favorites_visibility: str | None = None,
) -> AccountProfile:
    """Atomically persist the fields provided in one owner-scoped write.

    Fields left as ``None`` (not present in the payload) are left untouched.
    Re-validates bio length, avatar scheme/length, and visibility enum
    *before* touching the database as a second layer of defense below the
    serializer -- matching the library.services double-validation pattern
    (serializer for client feedback, service as the last application-level
    gate before the PostgreSQL constraint). Validating first means a
    rejected update never even materializes a default profile row for an
    account that never had one.
    """
    if bio is not None and len(bio) > BIO_MAX_LENGTH:
        raise ValidationError("bio is too long.")
    if avatar_url is not None and avatar_url and (
        len(avatar_url) > AVATAR_URL_MAX_LENGTH or not avatar_url.startswith("https://")
    ):
        raise ValidationError("avatar_url must be an https:// URL within the length limit.")
    if collection_visibility is not None and collection_visibility not in VALID_VISIBILITIES:
        raise ValidationError("collection_visibility is invalid.")
    if favorites_visibility is not None and favorites_visibility not in VALID_VISIBILITIES:
        raise ValidationError("favorites_visibility is invalid.")

    with transaction.atomic():
        profile, _ = AccountProfile.objects.select_for_update().get_or_create(user=user)
        update_fields: list[str] = []

        if bio is not None:
            profile.bio = bio
            update_fields.append("bio")
        if avatar_url is not None:
            profile.avatar_url = avatar_url
            update_fields.append("avatar_url")
        if collection_visibility is not None:
            profile.collection_visibility = collection_visibility
            update_fields.append("collection_visibility")
        if favorites_visibility is not None:
            profile.favorites_visibility = favorites_visibility
            update_fields.append("favorites_visibility")

        if update_fields:
            profile.save(update_fields=[*update_fields, "updated_at"])

    return profile
