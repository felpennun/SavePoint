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

from django.conf import settings
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


class RecommendationSnapshot(models.Model):
    """Atomically publishable recommendation bundle for one collection revision."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendation_snapshots"
    )
    collection_revision = models.PositiveBigIntegerField()
    input_fingerprint = models.CharField(max_length=64)
    configuration_fingerprint = models.CharField(max_length=64, default="legacy-v1")
    corpus_version = models.CharField(max_length=64, null=True, blank=True)
    feature_set_version = models.CharField(max_length=64)
    payload = models.JSONField()
    generated_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "user",
                    "collection_revision",
                    "input_fingerprint",
                    "configuration_fingerprint",
                ),
                name="recommendations_unique_snapshot_revision",
            )
        ]
        indexes = [models.Index(fields=("user", "-created_at"))]


class RecommendationState(models.Model):
    """Current collection revision and atomically selected snapshot per user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendation_state"
    )
    collection_revision = models.PositiveBigIntegerField(default=0)
    active_snapshot = models.ForeignKey(
        RecommendationSnapshot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_for_states",
    )
    updated_at = models.DateTimeField(auto_now=True)


class RecommendationSignalCache(models.Model):
    """One user's shared content signals, computed once by the signals job.

    ``rating_term`` and ``facet_similarity`` (positive and negative) are the
    same regardless of which of the 13 content/hybrid algorithm variants ends
    up scoring a candidate with them (see ``recommendations/content/rank.py``
    and ``recommendations/content/signal_cache.py``). Each of those variants
    normally runs in its own dedicated worker container
    (``infra/compose.yaml``), so a same-process cache like the offline
    evaluation runner uses cannot be shared between them -- this table is the
    cross-process equivalent: the ``content-signals-v1`` job computes the
    O(candidates) loop exactly once per (user, collection revision,
    configuration) and every dependent worker reads this row instead of
    repeating it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendation_signal_caches"
    )
    requested_revision = models.PositiveBigIntegerField()
    configuration_fingerprint = models.CharField(max_length=64)
    corpus_version = models.CharField(max_length=64, null=True, blank=True)
    profile_inputs_json = models.JSONField()
    rating_term_json = models.JSONField()
    similarity_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "requested_revision", "configuration_fingerprint"),
                name="recommendations_unique_signal_cache",
            )
        ]


class RecommendationJobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    OBSOLETE = "obsolete", "Obsolete"


class RecommendationRefreshJob(models.Model):
    """One durable section calculation, coalesced by revision and configuration."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendation_refresh_jobs"
    )
    requested_revision = models.PositiveBigIntegerField()
    configuration_fingerprint = models.CharField(max_length=64, default="legacy-v1")
    algorithm_id = models.CharField(max_length=64, default="legacy-bundle-v1")
    status = models.CharField(
        max_length=16, choices=RecommendationJobStatus.choices, default=RecommendationJobStatus.QUEUED
    )
    attempts = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField()
    locked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    result_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("available_at", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "requested_revision", "configuration_fingerprint", "algorithm_id"),
                name="recommendations_unique_refresh_section",
            )
        ]
        indexes = [
            models.Index(fields=("status", "available_at")),
            models.Index(
                fields=("algorithm_id", "status", "available_at"),
                name="recommendat_algorit_d0ff28_idx",
            ),
        ]
