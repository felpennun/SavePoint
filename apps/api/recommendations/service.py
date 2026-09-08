"""Versioned product recommendation service (Phase 3, D-01--D-09).

This module is the single bridge between the governed candidate universe, the
existing content ranker, and the authenticated API. Candidate construction is
deliberately independent of the selected algorithm so every variant receives
the same immutable manifest.
"""

from __future__ import annotations

from datetime import date

from django.contrib.auth.models import AbstractBaseUser

from catalogue.models import CorpusVersion, GameWork, Genre
from catalogue.serializers import _cover, _platform_summary, _release_year
from evaluation.candidates import CandidateManifest, build_common
from evaluation import protocol as evaluation_protocol
from library.models import LibraryEntry
from recommendations.content.rank import rank_content_v1
from recommendations.content.variants import ALGORITHM_REGISTRY


PROTOCOL_VERSION = 2
MIN_LIMIT = 1
MAX_LIMIT = 50


class RecommendationServiceError(RuntimeError):
    """Raised when a v2 recommendation contract cannot be trusted."""


def active_corpus_version() -> str | None:
    """Return the newest active corpus, or ``None`` for local fixture data."""

    return (
        CorpusVersion.objects.filter(is_active=True)
        .order_by("-created_at")
        .values_list("version", flat=True)
        .first()
    )


def _resolved_corpus_version(protocol: evaluation_protocol.Protocol, requested: str | None) -> str | None:
    if requested is not None:
        return requested
    active = active_corpus_version()
    if active is not None:
        return active
    # A test database or a freshly bootstrapped local install may not have a
    # CorpusVersion row yet. In that case keep the query usable rather than
    # silently filtering every fixture against the signed production version.
    return None


def build_candidate_manifest(
    user: AbstractBaseUser,
    protocol: evaluation_protocol.Protocol,
    *,
    corpus_version: str | None = None,
    eligibility_cutoff_date: date | None = None,
) -> CandidateManifest:
    """Build the common governed candidate set for one user.

    The explorable universe contains all governed, non-future primary works.
    The output universe additionally requires a counted rating or a valid
    external rating. Any library entry is excluded, including the user's
    unrated and pending entries.
    """

    resolved_corpus = _resolved_corpus_version(protocol, corpus_version)
    return build_common(
        user,
        protocol,
        corpus_version=resolved_corpus,
        eligibility_cutoff_date=eligibility_cutoff_date,
    )


def _reason(
    item: dict,
    *,
    genre_names: dict[str, str],
    platform_names: dict[str, str],
) -> dict | None:
    """Return bounded, signal-backed evidence; never manufacture an excuse."""

    signals = []
    for signal in item.get("reason_signals", []):
        kind = signal.get("kind")
        slug = signal.get("value")
        names = genre_names if kind == "genre" else platform_names if kind == "platform" else {}
        if slug in names:
            signals.append({"kind": kind, "slug": slug, "name": names[slug]})
        if len(signals) == 2:
            break
    if not signals:
        return None
    return {"kind": "signal_overlap", "signals": signals}


def _limit(value: int | None) -> int | None:
    if value is None:
        return None
    return max(MIN_LIMIT, min(MAX_LIMIT, int(value)))


def recommend_for_user(
    user: AbstractBaseUser,
    algorithm_id: str,
    *,
    limit: int | None = None,
    protocol: evaluation_protocol.Protocol | None = None,
    corpus_version: str | None = None,
    eligibility_cutoff_date: date | None = None,
) -> dict:
    """Rank one user's governed candidates and return the stable v2 DTO."""

    if algorithm_id not in ALGORITHM_REGISTRY:
        raise RecommendationServiceError("unknown algorithm_id")
    frozen = protocol or evaluation_protocol.load()
    evaluation_protocol.require_version(frozen, PROTOCOL_VERSION)
    manifest = build_candidate_manifest(
        user,
        frozen,
        corpus_version=corpus_version,
        eligibility_cutoff_date=eligibility_cutoff_date,
    )
    payload = rank_content_v1(
        user,
        algorithm_id,
        limit=_limit(limit),
        corpus_version=manifest.corpus_version,
        candidate_ids=manifest.candidate_ids,
        min_rating_count=None,
    )
    result_ids = {item["work_id"] for item in payload["results"]}
    manifest_ids = {str(work_id) for work_id in manifest.candidate_ids}
    if not result_ids <= manifest_ids:
        raise RecommendationServiceError("ranker returned a work outside the candidate manifest")
    if payload.get("algorithm_id") != algorithm_id:
        raise RecommendationServiceError("ranker returned an unexpected algorithm_id")

    seen_ids = {str(work_id) for work_id in LibraryEntry.objects.filter(user=user).values_list("work_id", flat=True)}
    if result_ids & seen_ids:
        raise RecommendationServiceError("ranker returned a work already present in the user's library")

    works = {
        str(work.id): work
        for work in GameWork.objects.filter(id__in=result_ids).prefetch_related(
            "genres", "assets", "releases__platform"
        )
    }
    genre_names = dict(Genre.objects.values_list("slug", "name"))
    results = []
    for item in payload["results"]:
        work = works.get(item["work_id"])
        if work is None:
            raise RecommendationServiceError("ranker returned an incomplete work payload")
        results.append(
            {
                **item,
                "year": _release_year(work),
                "platform_summary": _platform_summary(work),
                "cover": _cover(work),
                "reason": _reason(
                    item,
                    genre_names=genre_names,
                    platform_names={
                        release.platform.slug: release.platform.name
                        for release in work.releases.all()
                        if release.platform is not None
                    },
                ),
            }
        )

    return {
        "protocol_version": PROTOCOL_VERSION,
        "algorithm_id": payload["algorithm_id"],
        "generated_at": payload["generated_at"],
        "input_snapshot_sha256": payload["input_snapshot_sha256"],
        "feature_set_version": payload["feature_set_version"],
        "corpus_version": payload["corpus_version"],
        "snapshot_sha256": payload["snapshot_sha256"],
        "candidate_manifest_sha256": manifest.candidate_manifest_sha256,
        "candidate_count": len(manifest.candidate_ids),
        "explorable_count": len(manifest.explorable_ids),
        "eligibility_cutoff_date": manifest.eligibility_cutoff_date.isoformat(),
        "insufficient_history": payload["insufficient_history"],
        "limitation": payload["limitation"],
        "results": results,
    }
