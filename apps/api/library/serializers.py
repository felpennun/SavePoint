"""Library DTOs for rating, owned copies, comments, and custom lists
(D-13/D-15/D-16/D-04..D-07/INV-03/INV-04)."""

from __future__ import annotations

import re
from decimal import Decimal

from rest_framework import serializers

from library.models import (
    COMMENT_TEXT_MAX_LENGTH,
    COPY_PRICE_DECIMAL_PLACES,
    COPY_PRICE_MAX_DIGITS,
    COPY_STORAGE_LOCATION_MAX_LENGTH,
    COPY_STORE_MAX_LENGTH,
    LIST_NAME_MAX_LENGTH,
    ConservationState,
    ContentVisibility,
    GameComment,
    OwnedCopy,
)

_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_CONSERVATION_STATE_CHOICES = [choice.value for choice in ConservationState]


class RatingRequestSerializer(serializers.Serializer):
    """Accepts null or an exact integer 1..10 -- never a float, never a
    string that would need coercion (LIB-02 boundary)."""

    rating_half_steps = serializers.IntegerField(min_value=1, max_value=10, allow_null=True)


def _validate_currency(value: str | None) -> str | None:
    """Normalizes to uppercase and rejects anything but exactly three
    letters (INV-03). Shared by every serializer that accepts a currency so
    the rule can never drift between the two entry points (single-copy
    creation vs. full configuration replace)."""
    if value is None:
        return value
    normalized = value.upper()
    if not _CURRENCY_PATTERN.fullmatch(normalized):
        raise serializers.ValidationError("currency must be exactly three letters (e.g. EUR, USD).")
    return normalized


def _validate_physical_digital_rule(attrs: dict) -> dict:
    """INV-04: conservation_state/storage_location are physical-only. A
    digital copy carrying either is rejected here (400) before any
    mutation -- the model's CheckConstraint is the last line of defense for
    writes that bypass this serializer entirely."""
    if attrs.get("format") == "digital" and (
        attrs.get("conservation_state") is not None or attrs.get("storage_location") is not None
    ):
        raise serializers.ValidationError(
            {"conservation_state": "digital copies cannot record conservation_state or storage_location."}
        )
    return attrs


class OwnedCopySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    release_id = serializers.UUIDField()
    edition_id = serializers.UUIDField(allow_null=True)
    format = serializers.ChoiceField(choices=["physical", "digital"])
    purchase_date = serializers.DateField(allow_null=True)
    price = serializers.DecimalField(
        max_digits=COPY_PRICE_MAX_DIGITS, decimal_places=COPY_PRICE_DECIMAL_PLACES, allow_null=True
    )
    currency = serializers.CharField(allow_null=True)
    store = serializers.CharField(allow_null=True)
    conservation_state = serializers.CharField(allow_null=True)
    storage_location = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class CreateOwnedCopyRequestSerializer(serializers.Serializer):
    release_id = serializers.UUIDField()
    edition_id = serializers.UUIDField(required=False, allow_null=True)
    format = serializers.ChoiceField(choices=["physical", "digital"])
    idempotency_key = serializers.CharField(max_length=100, allow_blank=False)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    price = serializers.DecimalField(
        max_digits=COPY_PRICE_MAX_DIGITS,
        decimal_places=COPY_PRICE_DECIMAL_PLACES,
        min_value=Decimal("0"),
        required=False,
        allow_null=True,
    )
    currency = serializers.CharField(min_length=3, max_length=3, required=False, allow_null=True)
    store = serializers.CharField(max_length=COPY_STORE_MAX_LENGTH, required=False, allow_null=True)
    conservation_state = serializers.ChoiceField(
        choices=_CONSERVATION_STATE_CHOICES, required=False, allow_null=True
    )
    storage_location = serializers.CharField(
        max_length=COPY_STORAGE_LOCATION_MAX_LENGTH, required=False, allow_null=True
    )

    def validate_currency(self, value: str | None) -> str | None:
        return _validate_currency(value)

    def validate(self, attrs: dict) -> dict:
        return _validate_physical_digital_rule(attrs)


class LibraryCopyConfigurationSerializer(serializers.Serializer):
    """One copy row in the complete library configuration payload."""

    id = serializers.UUIDField(required=False)
    release_id = serializers.UUIDField()
    edition_id = serializers.UUIDField(required=False, allow_null=True)
    format = serializers.ChoiceField(choices=["physical", "digital"])
    idempotency_key = serializers.CharField(max_length=100, required=False, allow_blank=False)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    price = serializers.DecimalField(
        max_digits=COPY_PRICE_MAX_DIGITS,
        decimal_places=COPY_PRICE_DECIMAL_PLACES,
        min_value=Decimal("0"),
        required=False,
        allow_null=True,
    )
    currency = serializers.CharField(min_length=3, max_length=3, required=False, allow_null=True)
    store = serializers.CharField(max_length=COPY_STORE_MAX_LENGTH, required=False, allow_null=True)
    conservation_state = serializers.ChoiceField(
        choices=_CONSERVATION_STATE_CHOICES, required=False, allow_null=True
    )
    storage_location = serializers.CharField(
        max_length=COPY_STORAGE_LOCATION_MAX_LENGTH, required=False, allow_null=True
    )

    def validate_currency(self, value: str | None) -> str | None:
        return _validate_currency(value)

    def validate(self, attrs: dict) -> dict:
        return _validate_physical_digital_rule(attrs)


class LibraryConfigurationSerializer(serializers.Serializer):
    """Complete replacement for a user's work-level configuration."""

    status = serializers.ChoiceField(
        choices=["pending", "playing", "completed", "abandoned"], allow_null=True
    )
    rating_half_steps = serializers.IntegerField(min_value=1, max_value=10, allow_null=True)
    is_platinum = serializers.BooleanField(required=False, default=False)
    copies = LibraryCopyConfigurationSerializer(many=True)


def serialize_copy(copy: OwnedCopy) -> dict:
    return OwnedCopySerializer(copy).data


def _escape_text(value: str) -> str:
    """Comment text, list names, and titles are returned as plain text,
    never markup -- the client renders them, they never become HTML here
    (XSS boundary), matching accounts.serializers._escape_text."""
    return str(value)


_VISIBILITY_CHOICES = [choice.value for choice in ContentVisibility]


class CommentInputSerializer(serializers.Serializer):
    """Create/update payload for a single owner comment (D-04/D-05).

    ``text``/``visibility`` are both optional at the serializer level so the
    same class serves PATCH (``partial=True``, either field alone is valid)
    -- POST creation requires ``text`` to actually be present, which the
    service layer enforces as the second validation gate."""

    text = serializers.CharField(max_length=COMMENT_TEXT_MAX_LENGTH, allow_blank=False, required=False)
    visibility = serializers.ChoiceField(choices=_VISIBILITY_CHOICES, required=False)


def serialize_comment(comment: GameComment, *, viewer=None) -> dict:  # noqa: ANN001
    """Comment DTO for the by-work comments endpoint (owner + third parties
    share this shape; visibility filtering happens before this is called,
    in ``library.services.list_visible_comments``)."""
    is_owner = bool(
        viewer is not None and getattr(viewer, "is_authenticated", False) and viewer.pk == comment.user_id
    )
    return {
        "id": str(comment.id),
        "work_id": str(comment.work_id),
        "author": _escape_text(comment.user.username),
        "text": _escape_text(comment.text),
        "visibility": comment.visibility,
        "is_own": is_owner,
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
    }


def serialize_profile_comment(comment: GameComment) -> dict:
    """Minimal allowlist for the public-profile aggregate (PRIV-01): no
    comment id, no visibility flag, no author key (the profile itself is
    already scoped to one alias) -- only the work reference and the text."""
    return {
        "work_slug": _escape_text(comment.work.canonical_slug),
        "work_title": _escape_text(comment.work.title_en or comment.work.original_title),
        "text": _escape_text(comment.text),
    }


class CustomListInputSerializer(serializers.Serializer):
    """Create/update payload for a ``CustomList`` (D-06/D-07). ``name`` is
    required for POST create; PATCH instantiates this with ``partial=True``
    so either field alone is a valid update."""

    name = serializers.CharField(max_length=LIST_NAME_MAX_LENGTH, allow_blank=False)
    visibility = serializers.ChoiceField(choices=_VISIBILITY_CHOICES, required=False)


class AddListItemSerializer(serializers.Serializer):
    work_id = serializers.UUIDField()


class ReorderListSerializer(serializers.Serializer):
    """Full-set optimistic-concurrency reorder payload: ``expected_version``
    is mandatory (a request without it is rejected with 400 before any
    mutation, per the plan's fail-closed contract) and ``item_ids`` must be
    the list's complete current item-id set, order defining the new
    ``1..N`` positions."""

    expected_version = serializers.IntegerField(min_value=1)
    item_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)


def serialize_list(custom_list) -> dict:  # noqa: ANN001
    """Owner-facing list DTO: id/version (needed for the next reorder call)
    plus the ordered item set."""
    items = list(custom_list.items.select_related("work").all())
    return {
        "id": str(custom_list.id),
        "name": _escape_text(custom_list.name),
        "visibility": custom_list.visibility,
        "version": custom_list.version,
        "items": [
            {
                "id": str(item.id),
                "work_id": str(item.work_id),
                "work_slug": _escape_text(item.work.canonical_slug),
                "work_title": _escape_text(item.work.title_en or item.work.original_title),
                "position": item.position,
            }
            for item in items
        ],
    }


def serialize_profile_list(custom_list) -> dict:  # noqa: ANN001
    """Minimal allowlist for the public-profile aggregate (PRIV-01): name,
    ordered work slugs/titles/positions only -- no list id, no version, no
    visibility flag (the profile has already filtered to public lists)."""
    items = list(custom_list.items.select_related("work").all())
    return {
        "name": _escape_text(custom_list.name),
        "items": [
            {
                "work_slug": _escape_text(item.work.canonical_slug),
                "work_title": _escape_text(item.work.title_en or item.work.original_title),
                "position": item.position,
            }
            for item in items
        ],
    }
