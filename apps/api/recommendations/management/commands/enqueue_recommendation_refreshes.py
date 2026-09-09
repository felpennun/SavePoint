"""Enqueue the first personal recommendation refresh for existing collections."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from recommendations.jobs import enqueue_latest_refresh
from recommendations.models import RecommendationState


class Command(BaseCommand):
    help = "Enqueue recommendation refreshes for users with existing collection data."

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        user_model = get_user_model()
        users = user_model.objects.filter(
            Q(library_entries__isnull=False) | Q(owned_copies__isnull=False)
        ).distinct()
        enqueued = 0
        for user in users.iterator():
            state, _ = RecommendationState.objects.get_or_create(user_id=user.id)
            if state.collection_revision == 0:
                state.collection_revision = 1
                state.save(update_fields=["collection_revision", "updated_at"])
            if enqueue_latest_refresh(user.id):
                enqueued += 1
        self.stdout.write(self.style.SUCCESS(f"Enqueued {enqueued} recommendation refresh(es)."))
