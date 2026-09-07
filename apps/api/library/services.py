"""Transactional library services (D-13/D-15/D-16): exact rating persistence
and idempotent copy creation with release/edition ownership validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from catalogue.models import Edition, GameRelease, GameWork
from library.models import BacklogStatus, CopyFormat, LibraryEntry, OwnedCopy, StatusTransition

VALID_RATING_RANGE = range(1, 11)
VALID_FORMATS = {choice.value for choice in CopyFormat}
VALID_STATUSES = {choice.value for choice in BacklogStatus}


def set_rating(*, user, work: GameWork, rating_half_steps: int | None) -> LibraryEntry:
    """Persist an exact rating (1..10 half-steps, or None to clear it).

    Rejects 0, 11, floats, and any non-canonical value without rounding --
    the caller must send the exact integer or None (LIB-02 boundary).
    """
    if rating_half_steps is not None:
        if not isinstance(rating_half_steps, int) or isinstance(rating_half_steps, bool):
            raise ValidationError("rating_half_steps must be an integer or null.")
        if rating_half_steps not in VALID_RATING_RANGE:
            raise ValidationError("rating_half_steps must be between 1 and 10.")

    with transaction.atomic():
        entry, _ = LibraryEntry.objects.select_for_update().get_or_create(
            user=user, work=work, defaults={"current_status": None}
        )
        entry.rating_half_steps = rating_half_steps
        entry.save(update_fields=["rating_half_steps", "updated_at"])
    return entry


def create_owned_copy(
    *,
    user,
    work: GameWork,
    release_id: str,
    edition_id: str | None,
    format: str,  # noqa: A002 - matches the domain vocabulary (D-15)
    idempotency_key: str,
) -> tuple[OwnedCopy, bool]:
    """Create a copy, or return the existing one for a replayed idempotency
    key (D-16: multiple copies are independent records; replay never
    duplicates). Returns (copy, created)."""
    if not idempotency_key:
        raise ValidationError("idempotency_key is required.")
    if format not in VALID_FORMATS:
        raise ValidationError("format must be 'physical' or 'digital'.")

    existing = OwnedCopy.objects.filter(user=user, idempotency_key=idempotency_key).first()
    if existing is not None:
        return existing, False

    try:
        release = GameRelease.objects.get(id=release_id, work=work)
    except GameRelease.DoesNotExist as exc:
        raise ValidationError("release does not belong to the selected work.") from exc

    edition = None
    if edition_id:
        try:
            edition = Edition.objects.get(id=edition_id, release=release)
        except Edition.DoesNotExist as exc:
            raise ValidationError("edition does not belong to the selected release.") from exc

    # A copy is also collection activity. Keep an empty work-level entry so
    # the owner-scoped collection endpoint can represent copy-only ownership;
    # status and rating remain optional fields on that entry.
    LibraryEntry.objects.get_or_create(user=user, work=work, defaults={"current_status": None})

    # select_for_update() cannot protect against a concurrent INSERT --
    # PostgreSQL has no row to lock until one exists. Two requests can both
    # pass the "does it exist" check above before either commits; the
    # UNIQUE constraint is the real safety net, and losing that race is
    # expected, not exceptional -- recover by reading back the winner's row
    # inside a savepoint (transaction.atomic here nests) so the failed
    # INSERT doesn't poison any caller-level outer transaction.
    try:
        with transaction.atomic():
            copy = OwnedCopy.objects.create(
                user=user,
                work=work,
                release=release,
                edition=edition,
                format=format,
                idempotency_key=idempotency_key,
            )
        return copy, True
    except IntegrityError:
        return OwnedCopy.objects.get(user=user, idempotency_key=idempotency_key), False


def save_library_configuration(
    *, user, work: GameWork, status: str | None, rating_half_steps: int | None, copies: list[dict]
) -> LibraryEntry | None:
    """Atomically persist the complete work configuration.

    The submitted copy list is authoritative for this user/work: existing
    rows are updated, new rows are inserted and omitted rows are removed.
    """
    if status is not None and status not in VALID_STATUSES:
        raise ValidationError("status is invalid.")
    if rating_half_steps is not None:
        if not isinstance(rating_half_steps, int) or isinstance(rating_half_steps, bool):
            raise ValidationError("rating_half_steps must be an integer or null.")
        if rating_half_steps not in VALID_RATING_RANGE:
            raise ValidationError("rating_half_steps must be between 1 and 10.")

    with transaction.atomic():
        entry = LibraryEntry.objects.select_for_update().filter(user=user, work=work).first()
        old_status = entry.current_status if entry else None
        if entry is None:
            entry = LibraryEntry.objects.create(
                user=user, work=work, current_status=status, rating_half_steps=rating_half_steps
            )
            if status is not None:
                StatusTransition.objects.create(
                    entry=entry, from_status=None, to_status=status, changed_at=datetime.now(timezone.utc)
                )
        else:
            status_changed = old_status != status
            entry.current_status = status
            entry.rating_half_steps = rating_half_steps
            entry.save(update_fields=["current_status", "rating_half_steps", "updated_at"])
            if status_changed and status is not None:
                StatusTransition.objects.create(
                    entry=entry, from_status=old_status, to_status=status, changed_at=datetime.now(timezone.utc)
                )

        existing = {
            str(copy.id): copy
            for copy in OwnedCopy.objects.select_for_update().filter(user=user, work=work)
        }
        keep_ids: set[str] = set()
        for copy_data in copies:
            copy_id = str(copy_data["id"]) if copy_data.get("id") else None
            release_id = str(copy_data["release_id"])
            try:
                release = GameRelease.objects.get(id=release_id, work=work)
            except GameRelease.DoesNotExist as exc:
                raise ValidationError("release does not belong to the selected work.") from exc

            edition = None
            if copy_data.get("edition_id"):
                try:
                    edition = Edition.objects.get(id=str(copy_data["edition_id"]), release=release)
                except Edition.DoesNotExist as exc:
                    raise ValidationError("edition does not belong to the selected release.") from exc

            if copy_id:
                copy = existing.get(copy_id)
                if copy is None:
                    raise ValidationError("copy does not belong to the current user and work.")
                copy.release = release
                copy.edition = edition
                copy.format = copy_data["format"]
                copy.save(update_fields=["release", "edition", "format"])
                keep_ids.add(copy_id)
                continue

            key = copy_data.get("idempotency_key") or str(uuid.uuid4())
            duplicate = OwnedCopy.objects.filter(user=user, idempotency_key=key).first()
            if duplicate is not None:
                if duplicate.work_id != work.id:
                    raise ValidationError("idempotency_key is already used by another work.")
                keep_ids.add(str(duplicate.id))
                continue
            copy = OwnedCopy.objects.create(
                user=user,
                work=work,
                release=release,
                edition=edition,
                format=copy_data["format"],
                idempotency_key=key,
            )
            keep_ids.add(str(copy.id))

        OwnedCopy.objects.filter(user=user, work=work).exclude(id__in=keep_ids).delete()

        if entry.current_status is None and entry.rating_half_steps is None and not keep_ids:
            entry.delete()
            return None
        return entry


def delete_owned_copy(*, user, work: GameWork, copy_id: str) -> bool:
    """Delete one copy only when it belongs to the authenticated owner."""
    deleted, _ = OwnedCopy.objects.filter(user=user, work=work, id=copy_id).delete()
    if deleted:
        entry = LibraryEntry.objects.filter(user=user, work=work).first()
        if entry and entry.current_status is None and entry.rating_half_steps is None:
            entry.delete()
    return bool(deleted)


def clear_library_configuration(*, user, work: GameWork) -> None:
    """Remove the entry, history and all copies for this owner/work pair."""
    with transaction.atomic():
        OwnedCopy.objects.filter(user=user, work=work).delete()
        LibraryEntry.objects.filter(user=user, work=work).delete()
