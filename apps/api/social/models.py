"""Persistent social relationship state and its database invariants."""

import uuid

from django.conf import settings
from django.db import models


class FriendshipRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    BLOCKED = "blocked", "Blocked"


class RelationshipPair(models.Model):
    """One stable, canonical lock row for an unordered user pair."""

    low_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_low_pairs"
    )
    high_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_high_pairs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("low_user", "high_user"), name="social_unique_relationship_pair"
            ),
            models.CheckConstraint(
                condition=models.Q(low_user__lt=models.F("high_user")),
                name="social_pair_users_canonical",
            ),
        ]
        indexes = [models.Index(fields=("low_user", "high_user"), name="social_pair_lookup")]


class Friendship(models.Model):
    """The current accepted friendship for a canonical pair."""

    pair = models.OneToOneField(
        RelationshipPair, on_delete=models.CASCADE, related_name="friendship"
    )
    accepted_at = models.DateTimeField(auto_now_add=True)


class FriendshipRequest(models.Model):
    """Directed request history; only one pending request may exist per direction."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_friendship_requests"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_friendship_requests",
    )
    status = models.CharField(
        max_length=16, choices=FriendshipRequestStatus.choices, default=FriendshipRequestStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(sender=models.F("receiver")), name="social_request_no_self"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=[choice.value for choice in FriendshipRequestStatus]),
                name="social_request_status_valid",
            ),
            models.UniqueConstraint(
                fields=("sender", "receiver"),
                condition=models.Q(status=FriendshipRequestStatus.PENDING),
                name="social_unique_pending_request_direction",
            ),
        ]
        indexes = [
            models.Index(fields=("sender", "status"), name="social_request_sender_status"),
            models.Index(fields=("receiver", "status"), name="social_request_receiver_status"),
        ]


class Block(models.Model):
    """Directed, reversible block tombstone owned by the blocker."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_blocks_given"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_blocks_received"
    )
    is_active = models.BooleanField(default=True)
    blocked_at = models.DateTimeField(auto_now_add=True)
    unblocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-blocked_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("blocker", "blocked"), name="social_unique_block_direction"
            ),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")), name="social_block_no_self"
            ),
        ]
        indexes = [
            models.Index(fields=("blocker", "is_active"), name="social_blocker_active"),
            models.Index(fields=("blocked", "is_active"), name="social_blocked_active"),
        ]
