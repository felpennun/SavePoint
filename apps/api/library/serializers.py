"""Library DTOs for rating and owned copies (D-13/D-15/D-16)."""

from __future__ import annotations

from rest_framework import serializers

from library.models import OwnedCopy


class RatingRequestSerializer(serializers.Serializer):
    """Accepts null or an exact integer 1..10 -- never a float, never a
    string that would need coercion (LIB-02 boundary)."""

    rating_half_steps = serializers.IntegerField(min_value=1, max_value=10, allow_null=True)


class OwnedCopySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    release_id = serializers.UUIDField()
    edition_id = serializers.UUIDField(allow_null=True)
    format = serializers.ChoiceField(choices=["physical", "digital"])
    created_at = serializers.DateTimeField()


class CreateOwnedCopyRequestSerializer(serializers.Serializer):
    release_id = serializers.UUIDField()
    edition_id = serializers.UUIDField(required=False, allow_null=True)
    format = serializers.ChoiceField(choices=["physical", "digital"])
    idempotency_key = serializers.CharField(max_length=100, allow_blank=False)


class LibraryCopyConfigurationSerializer(serializers.Serializer):
    """One copy row in the complete library configuration payload."""

    id = serializers.UUIDField(required=False)
    release_id = serializers.UUIDField()
    edition_id = serializers.UUIDField(required=False, allow_null=True)
    format = serializers.ChoiceField(choices=["physical", "digital"])
    idempotency_key = serializers.CharField(max_length=100, required=False, allow_blank=False)


class LibraryConfigurationSerializer(serializers.Serializer):
    """Complete replacement for a user's work-level configuration."""

    status = serializers.ChoiceField(
        choices=["pending", "playing", "completed", "abandoned"], allow_null=True
    )
    rating_half_steps = serializers.IntegerField(min_value=1, max_value=10, allow_null=True)
    copies = LibraryCopyConfigurationSerializer(many=True)


def serialize_copy(copy: OwnedCopy) -> dict:
    return OwnedCopySerializer(copy).data
