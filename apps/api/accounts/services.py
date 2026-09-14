"""Transactional, owner-derived account services (Phase 5, PROF-01/PRIV-01).

Every function here takes ``user`` explicitly from the caller (the view,
which derives it from ``request.user``) and never accepts a substitutable
identity from a request payload -- the same owner-scoped pattern already
used by ``library.services``.
"""

from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from audit.models import AuditAction, AuditResult
from audit.services import record_audit_event
from accounts.models import AVATAR_URL_MAX_LENGTH, BIO_MAX_LENGTH, AccountProfile, FavoriteSlot, ProfileVisibility
from library.models import LibraryEntry

VALID_VISIBILITIES = {choice.value for choice in ProfileVisibility}
IRREVERSIBLE_DELETE_CONFIRMATION = "DELETE ACCOUNT"


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
