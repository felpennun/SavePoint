"""Transactional library services (D-13/D-15/D-16): exact rating persistence
and idempotent copy creation with release/edition ownership validation."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction

from catalogue.models import Edition, GameRelease, GameWork
from library.models import (
    BacklogStatus,
    ConservationState,
    ContentVisibility,
    CopyFormat,
    CustomList,
    CustomListItem,
    GameComment,
    LibraryEntry,
    OwnedCopy,
    StatusTransition,
)
from social.models import Block, Friendship

VALID_RATING_RANGE = range(1, 11)
VALID_FORMATS = {choice.value for choice in CopyFormat}
VALID_STATUSES = {choice.value for choice in BacklogStatus}
VALID_VISIBILITIES = {choice.value for choice in ContentVisibility}
VALID_CONSERVATION_STATES = {choice.value for choice in ConservationState}
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


def _validate_copy_metadata(
    *,
    format: str,  # noqa: A002 - matches the domain vocabulary (D-15)
    price: Decimal | None = None,
    currency: str | None = None,
    conservation_state: str | None = None,
    storage_location: str | None = None,
) -> str | None:
    """Cross-field validation for purchase/conservation metadata (INV-03/
    INV-04), duplicated here (not just in the serializer) so a caller that
    invokes the service directly still gets the same guarantees. Returns
    the normalized (uppercase) currency, or None. Raises ``ValidationError``
    without ever touching the database."""
    if price is not None and price < 0:
        raise ValidationError("price must not be negative.")
    normalized_currency = currency.upper() if currency else None
    if normalized_currency is not None and not _CURRENCY_PATTERN.fullmatch(normalized_currency):
        raise ValidationError("currency must be exactly three uppercase letters.")
    if conservation_state is not None and conservation_state not in VALID_CONSERVATION_STATES:
        raise ValidationError("conservation_state is invalid.")
    if format == CopyFormat.DIGITAL and (conservation_state is not None or storage_location is not None):
        raise ValidationError("digital copies cannot record conservation_state or storage_location.")
    return normalized_currency


class CommentAlreadyExists(Exception):
    """Raised when the caller already has a comment for this work (D-04:
    at most one comment per user/work) -- the view maps this to HTTP 409
    without ever touching the database again."""


class StaleListVersion(Exception):
    """Raised when a reorder's ``expected_version`` no longer matches the
    list's persisted version -- the view maps this to HTTP 409. Always
    raised before any item is touched inside the reorder transaction."""


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
    purchase_date: date | None = None,
    price: Decimal | None = None,
    currency: str | None = None,
    store: str | None = None,
    conservation_state: str | None = None,
    storage_location: str | None = None,
) -> tuple[OwnedCopy, bool]:
    """Create a copy, or return the existing one for a replayed idempotency
    key (D-16: multiple copies are independent records; replay never
    duplicates). Returns (copy, created).

    Purchase/conservation metadata (INV-03/INV-04) is only applied on the
    first creation -- a replay never re-applies a differing payload to the
    already-persisted copy, matching the idempotency contract above."""
    if not idempotency_key:
        raise ValidationError("idempotency_key is required.")
    if format not in VALID_FORMATS:
        raise ValidationError("format must be 'physical' or 'digital'.")

    existing = OwnedCopy.objects.filter(user=user, idempotency_key=idempotency_key).first()
    if existing is not None:
        return existing, False

    normalized_currency = _validate_copy_metadata(
        format=format,
        price=price,
        currency=currency,
        conservation_state=conservation_state,
        storage_location=storage_location,
    )

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
                purchase_date=purchase_date,
                price=price,
                currency=normalized_currency,
                store=store,
                conservation_state=conservation_state,
                storage_location=storage_location,
            )
        return copy, True
    except IntegrityError:
        return OwnedCopy.objects.get(user=user, idempotency_key=idempotency_key), False


def save_library_configuration(
    *,
    user,
    work: GameWork,
    status: str | None,
    rating_half_steps: int | None,
    copies: list[dict],
    is_platinum: bool = False,
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
                user=user,
                work=work,
                current_status=status,
                rating_half_steps=rating_half_steps,
                is_platinum=is_platinum,
            )
            if status is not None:
                StatusTransition.objects.create(
                    entry=entry, from_status=None, to_status=status, changed_at=datetime.now(timezone.utc)
                )
        else:
            status_changed = old_status != status
            entry.current_status = status
            entry.rating_half_steps = rating_half_steps
            entry.is_platinum = is_platinum
            entry.save(update_fields=["current_status", "rating_half_steps", "is_platinum", "updated_at"])
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

            normalized_currency = _validate_copy_metadata(
                format=copy_data["format"],
                price=copy_data.get("price"),
                currency=copy_data.get("currency"),
                conservation_state=copy_data.get("conservation_state"),
                storage_location=copy_data.get("storage_location"),
            )

            if copy_id:
                copy = existing.get(copy_id)
                if copy is None:
                    raise ValidationError("copy does not belong to the current user and work.")
                copy.release = release
                copy.edition = edition
                copy.format = copy_data["format"]
                copy.purchase_date = copy_data.get("purchase_date")
                copy.price = copy_data.get("price")
                copy.currency = normalized_currency
                copy.store = copy_data.get("store")
                copy.conservation_state = copy_data.get("conservation_state")
                copy.storage_location = copy_data.get("storage_location")
                copy.save(
                    update_fields=[
                        "release",
                        "edition",
                        "format",
                        "purchase_date",
                        "price",
                        "currency",
                        "store",
                        "conservation_state",
                        "storage_location",
                    ]
                )
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
                purchase_date=copy_data.get("purchase_date"),
                price=copy_data.get("price"),
                currency=normalized_currency,
                store=copy_data.get("store"),
                conservation_state=copy_data.get("conservation_state"),
                storage_location=copy_data.get("storage_location"),
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


# ---------------------------------------------------------------------------
# Comments (D-04/D-05, LIB-03): one comment per user/work, author-owned.
# ---------------------------------------------------------------------------


def list_visible_comments(*, work: GameWork, viewer):  # noqa: ANN001
    """Return only comments authorized for the session actor.

    Public comments are friend-scoped in this phase; the author retains their
    own comment regardless of visibility. Anonymous callers receive an empty
    queryset so authorization happens before serialization or counting.
    """
    if viewer is None or not getattr(viewer, "is_authenticated", False):
        return GameComment.objects.none()
    pair_rows = Friendship.objects.filter(
        models.Q(pair__low_user=viewer) | models.Q(pair__high_user=viewer)
    ).values_list("pair__low_user_id", "pair__high_user_id")
    friend_ids = {user_id for row in pair_rows for user_id in row if user_id != viewer.pk}
    blocked_ids = set(
        Block.objects.filter(
            models.Q(blocker=viewer) | models.Q(blocked=viewer), is_active=True
        ).values_list("blocker_id", "blocked_id")
    )
    blocked_ids = {user_id for row in blocked_ids for user_id in row if user_id != viewer.pk}
    return (
        GameComment.objects.filter(work=work)
        .filter(models.Q(user=viewer) | models.Q(user_id__in=friend_ids, visibility=ContentVisibility.PUBLIC))
        .exclude(user_id__in=blocked_ids)
        .select_related("user")
        .order_by("created_at", "id")
    )


def create_comment(
    *, user, work: GameWork, text: str | None = None, visibility: str | None = None
) -> GameComment:
    """Create the caller's single comment for this work.

    Rejects (without any mutation) a work outside the caller's own
    collection, a missing/blank text, an invalid visibility, and -- via
    ``CommentAlreadyExists`` -- a second comment for the same user/work
    (D-04: exactly one comment per user/work, never a silent duplicate)."""
    if text is None or not text.strip():
        raise ValidationError("text is required.")
    resolved_visibility = visibility if visibility is not None else ContentVisibility.PUBLIC
    if resolved_visibility not in VALID_VISIBILITIES:
        raise ValidationError("visibility must be 'public' or 'private'.")
    if not LibraryEntry.objects.filter(user=user, work=work).exists():
        raise ValidationError("work is not in your collection.")
    if GameComment.objects.filter(user=user, work=work).exists():
        raise CommentAlreadyExists()

    with transaction.atomic():
        comment = GameComment.objects.create(
            user=user, work=work, text=text, visibility=resolved_visibility
        )
    return comment


def update_comment(
    *, comment: GameComment, text: str | None = None, visibility: str | None = None
) -> GameComment:
    """Update the fields provided; fields left ``None`` are left untouched
    (matches ``accounts.services.update_profile``'s partial-update
    contract)."""
    if text is not None and not text.strip():
        raise ValidationError("text is required.")
    if visibility is not None and visibility not in VALID_VISIBILITIES:
        raise ValidationError("visibility must be 'public' or 'private'.")

    update_fields: list[str] = []
    if text is not None:
        comment.text = text
        update_fields.append("text")
    if visibility is not None:
        comment.visibility = visibility
        update_fields.append("visibility")

    if update_fields:
        with transaction.atomic():
            comment.save(update_fields=[*update_fields, "updated_at"])
    return comment


def delete_comment(*, user, comment_id: str) -> bool:
    """Delete the caller's own comment. Owner-scoped by construction: the
    filter includes ``user=user`` so a non-owner's delete affects zero rows
    (indistinguishable from a nonexistent comment)."""
    deleted, _ = GameComment.objects.filter(id=comment_id, user=user).delete()
    return bool(deleted)


# ---------------------------------------------------------------------------
# Custom lists (D-06/D-07, LIB-04): manual, ordered collections of a user's
# own owned games, with optimistic-concurrency reorder.
# ---------------------------------------------------------------------------


def create_list(*, user, name: str | None = None, visibility: str | None = None) -> CustomList:
    if name is None or not name.strip():
        raise ValidationError("name is required.")
    resolved_visibility = visibility if visibility is not None else ContentVisibility.PUBLIC
    if resolved_visibility not in VALID_VISIBILITIES:
        raise ValidationError("visibility must be 'public' or 'private'.")

    with transaction.atomic():
        custom_list = CustomList.objects.create(user=user, name=name, visibility=resolved_visibility)
    return custom_list


def update_list(*, custom_list: CustomList, name: str | None = None, visibility: str | None = None) -> CustomList:
    if name is not None and not name.strip():
        raise ValidationError("name is required.")
    if visibility is not None and visibility not in VALID_VISIBILITIES:
        raise ValidationError("visibility must be 'public' or 'private'.")

    update_fields: list[str] = []
    if name is not None:
        custom_list.name = name
        update_fields.append("name")
    if visibility is not None:
        custom_list.visibility = visibility
        update_fields.append("visibility")

    if update_fields:
        with transaction.atomic():
            custom_list.save(update_fields=[*update_fields, "updated_at"])
    return custom_list


def add_list_item(*, user, custom_list: CustomList, work: GameWork) -> CustomListItem:
    """Append one owned work to the end of the list.

    Membership is re-checked against the caller's own ``LibraryEntry``
    before any write (Pitfall 3, 05-RESEARCH.md) -- a work that left the
    collection cannot be added to a new list, even if it once belonged
    here. The parent list row is locked for the duration of the insert so
    two concurrent adds can never compute the same "next" position."""
    if not LibraryEntry.objects.filter(user=user, work=work).exists():
        raise ValidationError("work is not in your collection.")

    with transaction.atomic():
        locked_list = CustomList.objects.select_for_update().get(id=custom_list.id, user=user)
        if CustomListItem.objects.filter(list=locked_list, work=work).exists():
            raise ValidationError("work is already in this list.")
        max_position = (
            CustomListItem.objects.filter(list=locked_list)
            .order_by("-position")
            .values_list("position", flat=True)
            .first()
        )
        next_position = (max_position or 0) + 1
        item = CustomListItem.objects.create(list=locked_list, work=work, position=next_position)
    return item


def reorder_list_items(*, user, list_id: str, expected_version: int, item_ids: list[str]) -> CustomList:
    """Atomically reassign consecutive ``1..N`` positions from a caller-
    submitted complete ordering of the list's current item ids.

    ``select_for_update()`` serializes concurrent reorders of the same
    list; a version mismatch raises ``StaleListVersion`` (mapped to HTTP
    409) before any item row is touched, so a losing concurrent writer
    never leaves duplicated or gapped positions. Positions are written in
    two passes -- first to unique temporary values outside the final
    ``1..N`` range, then to the final consecutive range -- so the
    intermediate state never collides with ``UniqueConstraint(list,
    position)`` (Pattern 4, 05-PATTERNS.md). Any exception raised while
    inside the surrounding ``transaction.atomic()`` rolls the whole
    operation back, leaving the previous order intact.
    """
    with transaction.atomic():
        custom_list = CustomList.objects.select_for_update().filter(id=list_id, user=user).first()
        if custom_list is None:
            raise ValidationError("list not found.")
        if custom_list.version != expected_version:
            raise StaleListVersion()

        items = list(CustomListItem.objects.filter(list=custom_list))
        items_by_id = {str(item.id): item for item in items}
        submitted_ids = [str(item_id) for item_id in item_ids]
        if set(submitted_ids) != set(items_by_id) or len(submitted_ids) != len(items_by_id):
            raise ValidationError("item_ids must exactly match the list's current items.")

        # Phase 1: unique temporary positions, well outside 1..N.
        temp_offset = len(submitted_ids) + 1000
        for offset, item_id in enumerate(submitted_ids):
            item = items_by_id[item_id]
            item.position = temp_offset + offset
            item.save(update_fields=["position"])

        # Phase 2: final consecutive 1..N positions in submission order.
        for index, item_id in enumerate(submitted_ids, start=1):
            item = items_by_id[item_id]
            item.position = index
            item.save(update_fields=["position"])

        custom_list.version += 1
        custom_list.save(update_fields=["version", "updated_at"])

    return custom_list
