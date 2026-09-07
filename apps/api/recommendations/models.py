"""Persistence for the content recommender laboratory.

``WorkFeatureVector`` is a **cache, not a trained model** (RESEARCH Pattern 5,
explicitly allowed): the sparse feature dict for a governed ``GameWork`` under
a given ``feature_set_version``, so the evaluation harness (Plan 02-13) and
the live endpoint (Plan 02-11) never recompute ~150k vectors per call. It is
rebuilt by the idempotent ``rebuild_feature_vectors`` command;
``feature_set_version`` is part of the published DTO (REC-09).
"""

from __future__ import annotations

import uuid

from django.db import models

from catalogue.models import GameWork


class WorkFeatureVector(models.Model):
    """Cached sparse content feature vector for one governed work."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(
        GameWork, on_delete=models.CASCADE, related_name="feature_vectors"
    )
    feature_set_version = models.CharField(max_length=64)
    vector_json = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("work_id", "feature_set_version")
        constraints = [
            models.UniqueConstraint(
                fields=("work", "feature_set_version"),
                name="recommendations_unique_work_feature_set",
            )
        ]

    def __str__(self) -> str:
        return f"{self.work_id} @ {self.feature_set_version} ({len(self.vector_json)} dims)"
