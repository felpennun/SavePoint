"""Invalidate personalized recommendation snapshots after library changes."""

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from library.models import LibraryEntry, OwnedCopy
from recommendations.models import RecommendationState


def _touch_user(user_id: int) -> None:
    state, _ = RecommendationState.objects.get_or_create(user_id=user_id)
    RecommendationState.objects.filter(pk=state.pk).update(
        collection_revision=state.collection_revision + 1
    )
    transaction.on_commit(lambda: _enqueue_latest(user_id))


def _enqueue_latest(user_id: int) -> None:
    from recommendations.jobs import enqueue_latest_refresh

    enqueue_latest_refresh(user_id)


@receiver(post_save, sender=LibraryEntry)
def library_entry_changed(sender, instance: LibraryEntry, **kwargs) -> None:  # noqa: ANN001
    _touch_user(instance.user_id)


@receiver(post_delete, sender=LibraryEntry)
def library_entry_deleted(sender, instance: LibraryEntry, **kwargs) -> None:  # noqa: ANN001
    _touch_user(instance.user_id)


@receiver(post_save, sender=OwnedCopy)
def owned_copy_changed(sender, instance: OwnedCopy, **kwargs) -> None:  # noqa: ANN001
    _touch_user(instance.user_id)


@receiver(post_delete, sender=OwnedCopy)
def owned_copy_deleted(sender, instance: OwnedCopy, **kwargs) -> None:  # noqa: ANN001
    _touch_user(instance.user_id)
