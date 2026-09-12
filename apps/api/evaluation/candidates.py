"""The single, version-pinned candidate-set builder for evaluation (EVAL-01)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date

from catalogue.corpus import evaluation_candidate_works, governed_works
from library.models import LibraryEntry
from evaluation.protocol import require_version
from evaluation.splits import leave_fraction_out_dominant_tag, leave_one_out


@dataclass(frozen=True)
class CandidateManifest:
    """The governed candidate boundary shared by product and evaluation."""

    protocol_version: int
    corpus_version: str | None
    eligibility_cutoff_date: date
    explorable_ids: frozenset[object]
    candidate_ids: frozenset[object]
    explorable_manifest_sha256: str
    candidate_manifest_sha256: str

    def as_dict(self) -> dict:
        return {
            "protocol_version": self.protocol_version,
            "corpus_version": self.corpus_version,
            "eligibility_cutoff_date": self.eligibility_cutoff_date.isoformat(),
            "explorable_count": len(self.explorable_ids),
            "candidate_count": len(self.candidate_ids),
            "explorable_manifest_sha256": self.explorable_manifest_sha256,
            "candidate_manifest_sha256": self.candidate_manifest_sha256,
        }


def _manifest_hash(ids: frozenset[object]) -> str:
    canonical = json.dumps(sorted(str(value) for value in ids), separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_common(
    user,
    protocol,
    *,
    corpus_version: str | None = None,
    eligibility_cutoff_date: date | None = None,
) -> CandidateManifest:
    """Build the common non-future candidate universe for product requests."""

    require_version(protocol, 15)
    cutoff = eligibility_cutoff_date or protocol.eligibility_cutoff_date or date.today()
    governed = governed_works(
        corpus_version,
        eligibility_cutoff_date=cutoff,
    )
    explorable_ids = frozenset(governed.values_list("id", flat=True))
    eligible = evaluation_candidate_works(
        corpus_version,
        eligibility_cutoff_date=cutoff,
    )
    seen_ids = frozenset(
        LibraryEntry.objects.filter(user=user).values_list("work_id", flat=True)
    )
    candidate_ids = frozenset(set(eligible.values_list("id", flat=True)) - set(seen_ids))
    return CandidateManifest(
        protocol_version=protocol.protocol_version,
        corpus_version=corpus_version,
        eligibility_cutoff_date=cutoff,
        explorable_ids=explorable_ids,
        candidate_ids=candidate_ids,
        explorable_manifest_sha256=_manifest_hash(explorable_ids),
        candidate_manifest_sha256=_manifest_hash(candidate_ids),
    )


def build(user, protocol, corpus_version: str) -> tuple[frozenset, frozenset, str] | None:
    """Return the shared candidate tuple, or ``None`` when it is not evaluable.

    The leave-one-out (or, candidate protocol v15, leave-fraction-out)
    implementation owns the exclusion rule. Keeping this function
    deliberately small gives every algorithm in a run the exact same
    immutable candidate set and manifest rather than letting rankers rebuild
    it. The held-out set is always a ``frozenset`` -- one element under the
    frozen ``leave_one_out_per_user`` strategy, one or more under the
    candidate ``leave_fraction_out_dominant_tag_per_user`` strategy -- so a
    caller never needs to know which mechanism produced it.

    Under ``leave_fraction_out_dominant_tag_per_user``, a user for whom that
    mechanism specifically cannot be constructed (no content-tag signal at
    all, or their dominant tag's own pool never clears the external-rating
    floor) falls back to the plain single-item ``leave_one_out`` rather than
    being excluded outright -- author decision, 2026-09-12: only a user with
    zero eligible positives at all (excluded by both mechanisms alike) is
    actually left out of the study. See the 2026-09-12 vault note.
    """

    require_version(protocol, 15)
    cutoff = protocol.eligibility_cutoff_date or date.today()
    strategy = protocol.split.get("strategy")
    if strategy == "leave_fraction_out_dominant_tag_per_user":
        fraction_split = leave_fraction_out_dominant_tag(
            user,
            seed=protocol.loo_seed,
            protocol=protocol,
            corpus_version=corpus_version,
            eligibility_cutoff_date=cutoff,
        )
        if fraction_split is not None:
            return (
                fraction_split.candidate_ids,
                fraction_split.heldout_work_ids,
                fraction_split.candidate_manifest_sha256,
            )
        # Falls through to the plain leave_one_out fallback below.
    split = leave_one_out(
        user,
        seed=protocol.loo_seed,
        protocol=protocol,
        corpus_version=corpus_version,
        eligibility_cutoff_date=cutoff,
    )
    if split is None:
        return None
    return split.candidate_ids, frozenset({split.heldout_work_id}), split.candidate_manifest_sha256
