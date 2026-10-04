"""Transactional, owner-derived account services (Phase 5, PROF-01/PRIV-01).

Every function here takes ``user`` explicitly from the caller (the view,
which derives it from ``request.user``) and never accepts a substitutable
identity from a request payload -- the same owner-scoped pattern already
used by ``library.services``.
"""

from __future__ import annotations

import re
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from audit.models import AuditAction, AuditResult
from audit.services import record_audit_event
from accounts.models import (
    AVATAR_PRESET_COUNT,
    AVATAR_URL_MAX_LENGTH,
    BIO_MAX_LENGTH,
    DISPLAY_NAME_MAX_LENGTH,
    PROFILE_IMAGE_MAX_BYTES,
    AccountProfile,
    FavoriteSlot,
    ProfileVisibility,
)
from library.models import LibraryEntry

VALID_VISIBILITIES = {choice.value for choice in ProfileVisibility}
IRREVERSIBLE_DELETE_CONFIRMATION = "DELETE ACCOUNT"

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
# Prefix given to anonymized accounts; never assignable by a user.
RESERVED_USERNAME_PREFIXES = ("anonymous-",)

_UNSET = object()

# Magic-number signatures of the only image formats accepted for uploads.
_IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)


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
    display_name: str | None = None,
    avatar_preset=_UNSET,  # noqa: ANN001 - int, None (clear) or untouched
    default_list_visibility: str | None = None,
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
    if default_list_visibility is not None and default_list_visibility not in VALID_VISIBILITIES:
        raise ValidationError("default_list_visibility is invalid.")
    if display_name is not None and len(display_name.strip()) > DISPLAY_NAME_MAX_LENGTH:
        raise ValidationError("display_name is too long.")
    if avatar_preset is not _UNSET and avatar_preset is not None and not 0 <= avatar_preset < AVATAR_PRESET_COUNT:
        raise ValidationError("avatar_preset is invalid.")

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
        if default_list_visibility is not None:
            profile.default_list_visibility = default_list_visibility
            update_fields.append("default_list_visibility")
        if display_name is not None:
            profile.display_name = display_name.strip()
            update_fields.append("display_name")
        if avatar_preset is not _UNSET:
            profile.avatar_preset = avatar_preset
            update_fields.append("avatar_preset")

        if update_fields:
            profile.save(update_fields=[*update_fields, "updated_at"])

    return profile


def check_username(*, user, candidate: str) -> str:  # noqa: ANN001
    """Classify a candidate username for ``user``: ``"ok"``, ``"same"`` (it is
    already theirs), ``"invalid"`` (format) or ``"taken"`` (another account
    has it, compared case-insensitively)."""
    candidate = candidate.strip()
    if candidate == user.username:
        return "same"
    if (
        not USERNAME_MIN_LENGTH <= len(candidate) <= USERNAME_MAX_LENGTH
        or not USERNAME_PATTERN.match(candidate)
        or candidate.lower().startswith(RESERVED_USERNAME_PREFIXES)
    ):
        return "invalid"
    if get_user_model().objects.filter(username__iexact=candidate).exclude(pk=user.pk).exists():
        return "taken"
    return "ok"


def change_username(*, user, new_username: str):  # noqa: ANN001
    """Rename the owner's account. Allowed once per account, and only to a
    name no other account has. Raises ``ValidationError`` whose ``code`` is
    ``already_changed``, ``invalid``, ``same`` or ``taken``."""
    from django.db import IntegrityError

    new_username = new_username.strip()
    with transaction.atomic():
        profile, _ = AccountProfile.objects.select_for_update().get_or_create(user=user)
        if profile.username_changed_at is not None:
            raise ValidationError("The username can only be changed once.", code="already_changed")
        outcome = check_username(user=user, candidate=new_username)
        if outcome != "ok":
            raise ValidationError(f"The username is not available ({outcome}).", code=outcome)
        user.username = new_username
        try:
            with transaction.atomic():
                user.save(update_fields=["username"])
        except IntegrityError as exc:
            raise ValidationError("The username is already taken.", code="taken") from exc
        profile.username_changed_at = timezone.now()
        profile.save(update_fields=["username_changed_at", "updated_at"])
    return user


def detect_image_type(data: bytes) -> str | None:
    """Return the MIME type of a JPEG/PNG/WebP payload from its signature, or
    ``None`` -- the declared Content-Type of an upload is never trusted."""
    for signature, mime in _IMAGE_SIGNATURES:
        if data.startswith(signature):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def set_profile_image(*, user, kind: str, data: bytes) -> AccountProfile:  # noqa: ANN001
    """Store the owner's cropped avatar or cover image (``kind`` is
    ``"avatar"`` or ``"cover"``)."""
    if kind not in {"avatar", "cover"}:
        raise ValidationError("kind is invalid.")
    if not data:
        raise ValidationError("An image is required.")
    if len(data) > PROFILE_IMAGE_MAX_BYTES:
        raise ValidationError("The image is too large.")
    mime = detect_image_type(data)
    if mime is None:
        raise ValidationError("Only JPEG, PNG or WebP images are accepted.")
    with transaction.atomic():
        profile, _ = AccountProfile.objects.select_for_update().get_or_create(user=user)
        setattr(profile, f"{kind}_image", data)
        setattr(profile, f"{kind}_image_type", mime)
        profile.save(update_fields=[f"{kind}_image", f"{kind}_image_type", "updated_at"])
    return profile


def clear_profile_image(*, user, kind: str) -> AccountProfile:  # noqa: ANN001
    if kind not in {"avatar", "cover"}:
        raise ValidationError("kind is invalid.")
    with transaction.atomic():
        profile, _ = AccountProfile.objects.select_for_update().get_or_create(user=user)
        setattr(profile, f"{kind}_image", None)
        setattr(profile, f"{kind}_image_type", "")
        profile.save(update_fields=[f"{kind}_image", f"{kind}_image_type", "updated_at"])
    return profile


def change_password(*, user, current_password: str, new_password: str) -> None:  # noqa: ANN001
    """Change the owner's password after re-checking the current one."""
    from django.contrib.auth.password_validation import validate_password

    if not user.check_password(current_password):
        raise ValidationError("The current password is incorrect.")
    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])


def delete_own_account(*, user, password: str) -> None:  # noqa: ANN001
    """Permanently delete the caller's own account and everything attached to
    it (collection, lists, comments, friendships, messages). Requires the
    current password. The audit trail is append-only, so the event carries no
    actor (it would be nulled by the deletion anyway) and keeps only the
    account id as the resource."""
    if not user.check_password(password):
        raise ValidationError("The password is incorrect.")
    with transaction.atomic():
        record_audit_event(
            actor=None,
            action=AuditAction.ACCOUNT_DELETED,
            resource_type="account",
            resource_id=user.pk,
            result=AuditResult.SUCCEEDED,
        )
        user.delete()


def replace_favorites(*, user, slots: list[dict]) -> list[FavoriteSlot]:  # noqa: ANN001
    """Atomically replace the caller's complete favorites set (D-02).

    Every work must belong to *this* user's own collection
    (``LibraryEntry``) -- re-checked here, never trusted from the payload
    or from any other user's ownership of the same work (IDOR boundary).
    Validation happens before any delete/create so a rejected payload never
    mutates the existing set.
    """
    work_ids = [str(item["work_id"]) for item in slots]

    with transaction.atomic():
        owned_work_ids = set(
            str(work_id)
            for work_id in LibraryEntry.objects.filter(
                user=user, work_id__in=work_ids
            ).values_list("work_id", flat=True)
        )
        missing = [work_id for work_id in work_ids if work_id not in owned_work_ids]
        if missing:
            raise ValidationError("Every favorite must belong to the owner's own collection.")

        FavoriteSlot.objects.filter(user=user).delete()
        created = [
            FavoriteSlot.objects.create(user=user, slot=item["slot"], work_id=item["work_id"])
            for item in slots
        ]

    return created


def anonymize_account(*, actor, target_user, operation_ref: str | uuid.UUID | None = None):  # noqa: ANN001
    """Deactivate and anonymize an account atomically and idempotently."""

    with transaction.atomic():
        user_model = get_user_model()
        user = user_model.objects.select_for_update().get(pk=target_user.pk)
        profile, _ = AccountProfile.objects.select_for_update().get_or_create(user=user)
        already_applied = profile.is_anonymized
        if not already_applied:
            user.username = f"anonymous-{profile.admin_uuid.hex[:24]}"
            user.email = ""
            user.first_name = ""
            user.last_name = ""
            user.is_active = False
            user.save(update_fields=["username", "email", "first_name", "last_name", "is_active"])
            user.groups.clear()
            user.user_permissions.clear()
            profile.bio = ""
            profile.avatar_url = ""
            profile.collection_visibility = ProfileVisibility.PRIVATE
            profile.favorites_visibility = ProfileVisibility.PRIVATE
            profile.is_anonymized = True
            profile.anonymized_at = timezone.now()
            profile.save(
                update_fields=[
                    "bio",
                    "avatar_url",
                    "collection_visibility",
                    "favorites_visibility",
                    "is_anonymized",
                    "anonymized_at",
                    "updated_at",
                ]
            )
        event = record_audit_event(
            actor=actor,
            action=AuditAction.ACCOUNT_ANONYMIZED,
            resource_type="account",
            resource_id=user.pk,
            result=AuditResult.ALREADY_APPLIED if already_applied else AuditResult.SUCCEEDED,
            operation_ref=operation_ref,
        )
    return user, event


def deactivate_and_anonymize_account(*, actor, target_user, operation_ref=None):  # noqa: ANN001
    """Compatibility name for the normal privacy operation."""

    return anonymize_account(actor=actor, target_user=target_user, operation_ref=operation_ref)


def delete_account_irreversibly(
    *, actor, target_user, confirmation: str, operation_ref: str | uuid.UUID | None = None
):  # noqa: ANN001
    """Delete only after explicit confirmation by a superuser."""

    if not getattr(actor, "is_superuser", False):
        raise PermissionDenied("Only a superuser may permanently delete an account.")
    if confirmation != IRREVERSIBLE_DELETE_CONFIRMATION:
        raise ValidationError("Explicit permanent-delete confirmation is required.")
    if actor.pk == target_user.pk:
        raise ValidationError("A superuser cannot permanently delete the active account.")

    with transaction.atomic():
        user_model = get_user_model()
        user = user_model.objects.select_for_update().get(pk=target_user.pk)
        event = record_audit_event(
            actor=actor,
            action=AuditAction.ACCOUNT_DELETED,
            resource_type="account",
            resource_id=user.pk,
            result=AuditResult.SUCCEEDED,
            operation_ref=operation_ref,
        )
        user.delete()
    return event
