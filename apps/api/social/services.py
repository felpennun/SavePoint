"""Owner-scoped, transactional social state transitions."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from social.models import (
    Block,
    Friendship,
    FriendshipRequest,
    FriendshipRequestStatus,
    RelationshipPair,
)


User = get_user_model()


class SocialNotFound(LookupError):
    """An intentionally generic missing/hidden social resource."""


class SocialConflict(Exception):
    """A valid actor attempted a transition incompatible with current state."""


def _resolve_active_user(alias: str):  # noqa: ANN001
    user = User.objects.filter(username=alias, is_active=True).first()
    if user is None:
        raise SocialNotFound()
    return user


def _lock_pair(first, second) -> RelationshipPair:  # noqa: ANN001
    if first.pk == second.pk:
        raise ValidationError("Self relationships are not allowed.")
    low, high = sorted((first, second), key=lambda user: user.pk)
    # User-row locks make pair creation deterministic even when this is the
    # first operation for the pair and no lock row exists yet.
    locked_users = list(User.objects.select_for_update().filter(pk__in=[low.pk, high.pk]).order_by("pk"))
    if len(locked_users) != 2:
        raise SocialNotFound()
    pair, _ = RelationshipPair.objects.get_or_create(low_user=low, high_user=high)
    return RelationshipPair.objects.select_for_update().select_related("low_user", "high_user").get(pk=pair.pk)


def _has_active_block(first, second) -> bool:  # noqa: ANN001
    return Block.objects.filter(
        is_active=True, blocker=first, blocked=second
    ).exists() or Block.objects.filter(is_active=True, blocker=second, blocked=first).exists()


def relationship_status(*, viewer, target) -> str:
    if viewer.pk == target.pk:
        return "self"
    if _has_active_block(viewer, target):
        return "blocked"
    pair = RelationshipPair.objects.filter(
        low_user_id=min(viewer.pk, target.pk), high_user_id=max(viewer.pk, target.pk)
    ).first()
    if pair is not None and Friendship.objects.filter(pair=pair).exists():
        return "friend"
    if FriendshipRequest.objects.filter(
        sender=viewer, receiver=target, status=FriendshipRequestStatus.PENDING
    ).exists():
        return "pending_sent"
    if FriendshipRequest.objects.filter(
        sender=target, receiver=viewer, status=FriendshipRequestStatus.PENDING
    ).exists():
        return "pending_received"
    return "none"


def search_exact_alias(*, viewer, alias: str) -> list:
    target = User.objects.filter(username=alias, is_active=True).first()
    if target is None or (target.pk != viewer.pk and _has_active_block(viewer, target)):
        return []
    return [target]


def request_friendship(*, sender, alias: str) -> FriendshipRequest:
    target = _resolve_active_user(alias)
    if sender.pk == target.pk:
        raise ValidationError("Self relationships are not allowed.")
    with transaction.atomic():
        pair = _lock_pair(sender, target)
        if _has_active_block(sender, target):
            raise SocialNotFound()
        if Friendship.objects.filter(pair=pair).exists():
            raise SocialConflict("Relationship already exists.")
        if FriendshipRequest.objects.filter(
            sender=sender, receiver=target, status=FriendshipRequestStatus.PENDING
        ).exists():
            raise SocialConflict("Request already exists.")
        if FriendshipRequest.objects.filter(
            sender=target, receiver=sender, status=FriendshipRequestStatus.PENDING
        ).exists():
            raise SocialConflict("A request already exists for this pair.")
        return FriendshipRequest.objects.create(sender=sender, receiver=target)


def accept_friendship_request(*, receiver, request_id: str) -> RelationshipPair:
    candidate = FriendshipRequest.objects.filter(id=request_id, receiver=receiver).select_related("sender").first()
    if candidate is None:
        raise SocialNotFound()
    with transaction.atomic():
        pair = _lock_pair(receiver, candidate.sender)
        request = FriendshipRequest.objects.select_for_update().filter(
            id=request_id, receiver=receiver, status=FriendshipRequestStatus.PENDING
        ).select_related("sender", "receiver").first()
        if request is None or _has_active_block(receiver, candidate.sender):
            raise SocialNotFound()
        request.status = FriendshipRequestStatus.ACCEPTED
        request.responded_at = timezone.now()
        request.save(update_fields=["status", "responded_at"])
        Friendship.objects.get_or_create(pair=pair)
    return pair


def reject_friendship_request(*, receiver, request_id: str) -> FriendshipRequest:
    candidate = FriendshipRequest.objects.filter(id=request_id, receiver=receiver).select_related("sender").first()
    if candidate is None:
        raise SocialNotFound()
    with transaction.atomic():
        pair = _lock_pair(receiver, candidate.sender)
        request = FriendshipRequest.objects.select_for_update().filter(
            id=request_id, receiver=receiver, status=FriendshipRequestStatus.PENDING
        ).first()
        if request is None:
            raise SocialNotFound()
        request.status = FriendshipRequestStatus.REJECTED
        request.responded_at = timezone.now()
        request.save(update_fields=["status", "responded_at"])
    return request


def remove_friendship(*, actor, alias: str) -> None:
    target = _resolve_active_user(alias)
    if actor.pk == target.pk:
        raise ValidationError("Self relationships are not allowed.")
    with transaction.atomic():
        pair = _lock_pair(actor, target)
        if _has_active_block(actor, target):
            raise SocialNotFound()
        deleted, _ = Friendship.objects.filter(pair=pair).delete()
        if not deleted:
            raise SocialNotFound()


def block_user(*, actor, alias: str) -> Block:
    target = _resolve_active_user(alias)
    if actor.pk == target.pk:
        raise ValidationError("Self relationships are not allowed.")
    with transaction.atomic():
        pair = _lock_pair(actor, target)
        block, _ = Block.objects.select_for_update().get_or_create(blocker=actor, blocked=target)
        if not block.is_active:
            block.is_active = True
            block.unblocked_at = None
            block.blocked_at = timezone.now()
            block.save(update_fields=["is_active", "unblocked_at", "blocked_at"])
        Friendship.objects.filter(pair=pair).delete()
        FriendshipRequest.objects.select_for_update().filter(
            sender__in=[actor, target], receiver__in=[actor, target], status=FriendshipRequestStatus.PENDING
        ).update(status=FriendshipRequestStatus.BLOCKED, responded_at=timezone.now())
    return block


def unblock_user(*, actor, alias: str) -> None:
    target = _resolve_active_user(alias)
    with transaction.atomic():
        pair = _lock_pair(actor, target)
        block = Block.objects.select_for_update().filter(
            blocker=actor, blocked=target, is_active=True
        ).first()
        if block is None:
            raise SocialNotFound()
        block.is_active = False
        block.unblocked_at = timezone.now()
        block.save(update_fields=["is_active", "unblocked_at"])


def pending_requests_for(*, user) -> tuple[list[FriendshipRequest], list[FriendshipRequest]]:
    received = list(
        FriendshipRequest.objects.filter(receiver=user, status=FriendshipRequestStatus.PENDING)
        .select_related("sender", "receiver")
    )
    sent = list(
        FriendshipRequest.objects.filter(sender=user, status=FriendshipRequestStatus.PENDING)
        .select_related("sender", "receiver")
    )
    return received, sent


def friendships_for(*, user) -> list[RelationshipPair]:
    return list(
        RelationshipPair.objects.filter(
            models.Q(low_user=user) | models.Q(high_user=user), friendship__isnull=False
        ).select_related("low_user", "high_user")
    )
