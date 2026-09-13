"""Explicit request and response DTOs for the social API."""

from collections.abc import Mapping

from rest_framework import serializers

from catalogue.serializers import _cover
from social.models import FriendshipRequest, RelationshipPair, SocialMessage


class ExactAliasSerializer(serializers.Serializer):
    alias = serializers.CharField(max_length=150, allow_blank=False, trim_whitespace=True)


class SocialAliasRequestSerializer(ExactAliasSerializer):
    """Reject identity-shaped fields instead of silently ignoring them."""

    def to_internal_value(self, data):  # noqa: ANN001
        if not isinstance(data, Mapping):
            raise serializers.ValidationError("A JSON object is required.")
        unexpected = set(data) - {"alias"}
        if unexpected:
            raise serializers.ValidationError(
                {"non_field_errors": ["Only an exact alias may be supplied."]}
            )
        return super().to_internal_value(data)


class RecommendationInputSerializer(serializers.Serializer):
    """Allow exactly one recipient, one catalogue work, and optional text."""

    recipient_alias = serializers.CharField(max_length=150, allow_blank=False, trim_whitespace=True)
    work_id = serializers.UUIDField()
    text = serializers.CharField(max_length=2000, allow_blank=True, required=False, default="")

    def to_internal_value(self, data):  # noqa: ANN001
        if not isinstance(data, Mapping):
            raise serializers.ValidationError("A JSON object is required.")
        unexpected = set(data) - {"recipient_alias", "work_id", "text"}
        if unexpected:
            raise serializers.ValidationError(
                {"non_field_errors": ["Only one recipient alias, work, and optional text may be supplied."]}
            )
        return super().to_internal_value(data)


def serialize_account(user, *, relationship: str) -> dict:
    profile = getattr(user, "profile", None)
    return {
        "alias": str(user.username),
        "avatar_url": str(profile.avatar_url) if profile is not None else "",
        "bio": str(profile.bio) if profile is not None else "",
        "relationship": relationship,
    }


def serialize_friendship_request(friendship_request: FriendshipRequest) -> dict:
    return {
        "id": str(friendship_request.id),
        "sender_alias": str(friendship_request.sender.username),
        "receiver_alias": str(friendship_request.receiver.username),
        "status": friendship_request.status,
        "created_at": friendship_request.created_at.isoformat(),
    }


def serialize_pair(pair: RelationshipPair, *, viewer) -> dict:  # noqa: ANN001
    other = pair.high_user if pair.low_user_id == viewer.pk else pair.low_user
    return {"alias": str(other.username), "relationship": "friend"}


def serialize_social_message(message: SocialMessage) -> dict:
    """Recipient-only DTO; hidden tombstones never reach this function."""
    work = message.work
    return {
        "id": str(message.id),
        "sender_alias": str(message.sender.username),
        "recipient_alias": str(message.receiver.username),
        "work": {
            "id": str(work.id),
            "title": str(work.title_en or work.original_title),
            "cover": _cover(work),
        },
        "text": str(message.message),
        "date": message.created_at.isoformat(),
        "read": message.read_at is not None,
    }
