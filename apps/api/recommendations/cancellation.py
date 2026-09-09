"""Cooperative cancellation primitives for personal recommendation workers."""

from __future__ import annotations


class RecommendationComputationCancelled(RuntimeError):
    """Raised when a newer collection revision supersedes a running calculation."""
