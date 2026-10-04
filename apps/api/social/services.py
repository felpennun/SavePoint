"""Owner-scoped, transactional social state transitions."""

from __future__ import annotations

import math
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, models, transaction
from django.utils import timezone

from catalogue.models import GameWork
from social.models import (
    Block,
    Friendship,
    FriendshipRequest,
    FriendshipRequestStatus,
    RelationshipPair,
    SocialMessage,
    SocialNotice,
    SocialNoticeKind,
)


User = get_user_model()


class SocialNotFound(LookupError):
    """An intentionally generic missing/hidden social resource."""


class SocialConflict(Exception):
    """A valid actor attempted a transition incompatible with current state."""


RECOMMENDATION_WINDOW = timedelta(days=7)
CONSERVATIVE_RETRY_AFTER = int(RECOMMENDATION_WINDOW.total_seconds())


class RecommendationCooldown(Exception):
    """The directional recommendation window is active or cannot be proven safe."""

    def __init__(self, retry_after_seconds: int = CONSERVATIVE_RETRY_AFTER):
        self.retry_after_seconds = max(1, int(retry_after_seconds))
        super().__init__("recommendation_cooldown")


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
        # Tell the person who asked that the request was accepted.
        SocialNotice.objects.create(
            recipient=request.sender, actor=receiver, kind=SocialNoticeKind.ACCEPTED
        )
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


def cancel_friendship_request(*, sender, request_id: str) -> None:
    """Withdraw a request the caller sent and that is still pending."""
    candidate = FriendshipRequest.objects.filter(id=request_id, sender=sender).select_related("receiver").first()
    if candidate is None:
        raise SocialNotFound()
    with transaction.atomic():
        _lock_pair(sender, candidate.receiver)
        deleted, _ = FriendshipRequest.objects.filter(
            id=request_id, sender=sender, status=FriendshipRequestStatus.PENDING
        ).delete()
        if not deleted:
            raise SocialNotFound()


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
        hide_messages_for_pair(first=actor, second=target, reason="removed")


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
        hide_messages_for_pair(first=actor, second=target, reason="blocked")
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


def _safe_now():  # noqa: ANN001
    """Return an aware clock value or fail closed before any message write."""
    try:
        now = timezone.now()
    except Exception as exc:  # noqa: BLE001 - an uncertain clock must fail closed
        raise RecommendationCooldown() from exc
    if not timezone.is_aware(now):
        raise RecommendationCooldown()
    return now


def _cooldown_seconds(*, created_at, now) -> int:  # noqa: ANN001
    if not timezone.is_aware(created_at) or not timezone.is_aware(now):
        raise RecommendationCooldown()
    return max(1, math.ceil((created_at + RECOMMENDATION_WINDOW - now).total_seconds()))


def send_recommendation(*, sender, recipient_alias: str, work_id, text: str = "") -> SocialMessage:  # noqa: ANN001
    """Create one private recommendation for an accepted friend.

    The canonical pair is locked before friendship and cooldown checks. Any
    uncertainty from the clock or database aborts the transaction and maps to
    the same conservative 429 as a known cooldown.
    """
    try:
        recipient = _resolve_active_user(recipient_alias)
    except DatabaseError as exc:
        raise RecommendationCooldown() from exc
    if sender.pk == recipient.pk:
        raise SocialNotFound()
    if not isinstance(text, str) or len(text) > 2000:
        raise ValidationError("text is invalid.")
    now = _safe_now()
    try:
        with transaction.atomic():
            pair = _lock_pair(sender, recipient)
            if _has_active_block(sender, recipient) or not Friendship.objects.filter(pair=pair).exists():
                raise SocialNotFound()
            try:
                recent = (
                    SocialMessage.objects.select_for_update()
                    .filter(sender=sender, receiver=recipient, created_at__gt=now - RECOMMENDATION_WINDOW)
                    .order_by("-created_at")
                    .first()
                )
            except DatabaseError as exc:
                raise RecommendationCooldown() from exc
            if recent is not None:
                raise RecommendationCooldown(_cooldown_seconds(created_at=recent.created_at, now=now))
            try:
                work = GameWork.objects.get(id=work_id, is_dlc=False)
            except GameWork.DoesNotExist as exc:
                raise ValidationError("work is invalid.") from exc
            except DatabaseError as exc:
                raise RecommendationCooldown() from exc
            try:
                return SocialMessage.objects.create(
                    sender=sender,
                    receiver=recipient,
                    work=work,
                    message=text,
                    created_at=now,
                )
            except DatabaseError as exc:
                raise RecommendationCooldown() from exc
    except RecommendationCooldown:
        raise
    except DatabaseError as exc:
        raise RecommendationCooldown() from exc


def inbox_for(*, recipient) -> list[SocialMessage]:
    """Return only visible messages addressed to the authenticated user."""
    return list(
        SocialMessage.objects.filter(receiver=recipient, hidden_at__isnull=True, work__isnull=False)
        .select_related("sender", "work")
        .prefetch_related("work__assets")
    )


def unread_count_for(*, recipient) -> int:
    """Everything waiting for the user: unread recommendations, friend requests
    still to answer, and unread notices (accepted requests, added games)."""
    messages = SocialMessage.objects.filter(
        receiver=recipient, hidden_at__isnull=True, work__isnull=False, read_at__isnull=True
    ).count()
    requests = FriendshipRequest.objects.filter(
        receiver=recipient, status=FriendshipRequestStatus.PENDING
    ).count()
    notices = SocialNotice.objects.filter(recipient=recipient, read_at__isnull=True).count()
    return messages + requests + notices


NOTIFICATION_LIMIT = 50


def notifications_for(*, user) -> list[dict]:
    """The notification column of the friends page, newest first. Four kinds:
    ``request`` (a friend request received), ``rec`` (a game recommended to the
    user), ``accepted`` (the user's request was accepted) and ``rec_added``
    (a friend put the user's recommendation in their backlog)."""
    friend_ids = {
        pair.high_user_id if pair.low_user_id == user.pk else pair.low_user_id
        for pair in friendships_for(user=user)
    }

    def actor_dto(actor) -> dict:  # noqa: ANN001
        profile = getattr(actor, "profile", None)
        is_friend = actor.pk in friend_ids
        return {
            "alias": str(actor.username),
            "name": (profile.display_name if profile is not None and profile.display_name else str(actor.username))
            if is_friend
            else str(actor.username),
            "is_friend": is_friend,
        }

    def work_dto(work) -> dict | None:  # noqa: ANN001
        if work is None:
            return None
        return {"id": str(work.id), "title": str(work.title_en or work.original_title), "slug": work.canonical_slug}

    items: list[dict] = []
    for item in FriendshipRequest.objects.filter(receiver=user).exclude(
        status__in=[FriendshipRequestStatus.BLOCKED]
    ).select_related("sender", "sender__profile")[:NOTIFICATION_LIMIT]:
        pending = item.status == FriendshipRequestStatus.PENDING
        items.append(
            {
                "id": f"request:{item.id}",
                "kind": "request",
                "request_id": str(item.id),
                "actor": actor_dto(item.sender),
                "work": None,
                "note": "",
                "state": "" if pending else item.status,
                "read": not pending,
                "date": item.created_at,
            }
        )
    for message in inbox_for(recipient=user)[:NOTIFICATION_LIMIT]:
        items.append(
            {
                "id": f"message:{message.id}",
                "kind": "rec",
                "message_id": str(message.id),
                "actor": actor_dto(message.sender),
                "work": work_dto(message.work),
                "note": str(message.message),
                "state": message.response,
                "read": message.read_at is not None,
                "date": message.created_at,
            }
        )
    for notice in SocialNotice.objects.filter(recipient=user).select_related(
        "actor", "actor__profile", "work"
    )[:NOTIFICATION_LIMIT]:
        items.append(
            {
                "id": f"notice:{notice.id}",
                "kind": notice.kind,
                "actor": actor_dto(notice.actor),
                "work": work_dto(notice.work),
                "note": "",
                "state": "",
                "read": notice.read_at is not None,
                "date": notice.created_at,
            }
        )
    # Unread first; inside each group the newest first.
    items.sort(key=lambda entry: entry["date"], reverse=True)
    items.sort(key=lambda entry: entry["read"])
    return items[:NOTIFICATION_LIMIT]


def mark_all_read(*, recipient) -> None:  # noqa: ANN001
    now = _safe_now()
    SocialMessage.objects.filter(
        receiver=recipient, hidden_at__isnull=True, work__isnull=False, read_at__isnull=True
    ).update(read_at=now)
    SocialNotice.objects.filter(recipient=recipient, read_at__isnull=True).update(read_at=now)


def respond_to_recommendation(*, recipient, message_id, response: str) -> SocialMessage | None:  # noqa: ANN001
    """Answer a recommendation once: ``added`` puts the game in the recipient's
    backlog (unless it is already in their collection) and tells the sender;
    ``dismissed`` just closes it. Either way it counts as read."""
    from datetime import datetime, timezone as dt_timezone

    from library.models import BacklogStatus, LibraryEntry, StatusTransition

    if response not in {"added", "dismissed"}:
        raise ValidationError("response is invalid.")
    now = _safe_now()
    with transaction.atomic():
        message = (
            SocialMessage.objects.select_for_update()
            .filter(id=message_id, receiver=recipient, hidden_at__isnull=True, work__isnull=False)
            .select_related("sender", "work")
            .first()
        )
        if message is None:
            return None
        if message.response:
            raise SocialConflict("Recommendation already answered.")
        message.response = response
        message.responded_at = now
        if message.read_at is None:
            message.read_at = now
        message.save(update_fields=["response", "responded_at", "read_at"])
        if response == "added":
            entry, created = LibraryEntry.objects.get_or_create(
                user=recipient, work=message.work, defaults={"current_status": BacklogStatus.PENDING}
            )
            if created:
                StatusTransition.objects.create(
                    entry=entry,
                    from_status=None,
                    to_status=BacklogStatus.PENDING,
                    changed_at=datetime.now(dt_timezone.utc),
                )
            SocialNotice.objects.create(
                recipient=message.sender, actor=recipient, kind=SocialNoticeKind.REC_ADDED, work=message.work
            )
    return message


def mark_message(*, recipient, message_id, read: bool) -> SocialMessage | None:  # noqa: ANN001
    """Mark one visible message read/unread without crossing recipient scope."""
    now = _safe_now()
    with transaction.atomic():
        message = (
            SocialMessage.objects.select_for_update()
            .filter(id=message_id, receiver=recipient, hidden_at__isnull=True, work__isnull=False)
            .select_related("sender", "work")
            .first()
        )
        if message is None:
            return None
        message.read_at = now if read else None
        message.save(update_fields=["read_at"])
        return message


def hide_messages_for_pair(*, first, second, reason: str) -> int:  # noqa: ANN001
    """Replace message content with an audit tombstone on remove/block."""
    now = _safe_now()
    return SocialMessage.objects.filter(
        sender__in=[first, second], receiver__in=[first, second], hidden_at__isnull=True
    ).update(work=None, message="", read_at=now, hidden_at=now, hidden_reason=reason)
