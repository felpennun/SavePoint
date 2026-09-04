"""Transactional library services (D-13/D-15/D-16): exact rating persistence
and idempotent copy creation with release/edition ownership validation."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from catalogue.models import Edition, GameRelease, GameWork
from library.models import CopyFormat, LibraryEntry, OwnedCopy

VALID_RATING_RANGE = range(1, 11)
VALID_FORMATS = {choice.value for choice in CopyFormat}


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
