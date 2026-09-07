"""The single, version-pinned candidate-set builder for evaluation (EVAL-01)."""

from __future__ import annotations

from evaluation.splits import leave_one_out


def build(user, protocol, corpus_version: str):
    """Return ``(candidate_ids, heldout_id, manifest_sha256)`` for ``user``.

    The leave-one-out implementation owns the exclusion rule.  Keeping this
    function deliberately small gives every algorithm in a run the exact same
    immutable candidate set and manifest rather than letting rankers rebuild it.
    """

    split = leave_one_out(
        user,
        seed=protocol.loo_seed,
        protocol=protocol,
        corpus_version=corpus_version,
    )
    if split is None:
        raise ValueError(f"user {user.pk} has no relevant-positive library entry")
    return split.candidate_ids, split.heldout_work_id, split.candidate_manifest_sha256
