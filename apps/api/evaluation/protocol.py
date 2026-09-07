"""Loader and freeze guards for the frozen evaluation protocol (EVAL-03).

``docs/methodology/protocol.json`` is the evidence contract: it fixes relevance
(D-17), K and the headline metric (D-19), the leave-one-out split (D-18), the
candidate set and exclusions, the frozen metric list (D-22), the tuning grid
(D-21, capped at 24 configs), the disjoint train/validation/test user split, and
placeholders for ``corpus_version`` / ``snapshot_sha256`` that Plan 02-13 fills
in against the active ``CorpusVersion``.

The loader is fail-closed, mirroring
``accounts.management.commands.bootstrap_demo_accounts.parse_seed_contract``:
every structural problem raises :class:`ProtocolError` before any caller can run
a single variant. Two freeze invariants are enforced here:

* ``len(grid) > 24`` -> :class:`ProtocolError` (D-21 tuning budget).
* a test-split run marker that already records *this* protocol's hash ->
  :class:`ProtocolError`, unless the caller passes ``allow_consumed_test=True``
  (which is only legitimate when ``protocol_version`` has been bumped).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

MAX_GRID = 24

REQUIRED_KEYS = frozenset(
    {
        "protocol_version",
        "relevance",
        "k_values",
        "headline",
        "split",
        "candidate_set",
        "exclusions",
        "metrics",
        "tuning",
        "user_split",
        "corpus_version",
        "snapshot_sha256",
    }
)

COMBINE_MODES = frozenset({"weighted_sum", "multiplicative", "two_stage"})


class ProtocolError(RuntimeError):
    """A structural problem with ``protocol.json`` or a violated freeze invariant.

    Raised before any evaluation run so a malformed or tampered contract can
    never reach a scoring loop.
    """


@dataclass(frozen=True)
class Protocol:
    """A validated, typed view over ``protocol.json``."""

    protocol_version: int
    relevance: dict[str, Any]
    k_values: tuple[int, ...]
    headline: str
    split: dict[str, Any]
    candidate_set: str
    exclusions: str
    metrics: tuple[str, ...]
    tuning: dict[str, Any]
    user_split: dict[str, Any]
    corpus_version: str | None
    snapshot_sha256: str | None
    simulation: bool
    limitation: str
    raw: dict[str, Any]

    @property
    def grid(self) -> list[dict[str, Any]]:
        return list(self.tuning["grid"])

    @property
    def loo_seed(self) -> int:
        return int(self.split["seed"])

    @property
    def user_split_seed(self) -> int:
        return int(self.user_split["seed"])

    @property
    def relevance_rating_floor(self) -> int:
        return int(self.relevance["rating_half_steps_gte"])

    def frozen_hash(self) -> str:
        """SHA-256 over the canonical JSON of the whole contract.

        Whitespace / key-order changes to the file do not move the hash; any
        semantic change does. Plans 02-11/02-13 and the thesis tables reference
        the protocol by this value.
        """

        canonical = json.dumps(
            self.raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def default_protocol_path() -> Path:
    """``<repo>/docs/methodology/protocol.json`` resolved from Django settings."""

    return Path(settings.BASE_DIR).parent.parent / "docs" / "methodology" / "protocol.json"


def load(
    path: str | Path | None = None,
    *,
    test_run_marker: str | Path | None = None,
    allow_consumed_test: bool = False,
) -> Protocol:
    """Read, validate, and return the frozen protocol.

    ``test_run_marker`` is an optional path to the run marker written by
    :func:`record_test_run`; when it already records this protocol's hash the
    load fails closed unless ``allow_consumed_test`` is set.
    """

    resolved = Path(path) if path is not None else default_protocol_path()
    if not resolved.is_file():
        raise ProtocolError(f"protocol file not found: {resolved}")
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"protocol file is not valid JSON: {resolved}") from exc

    protocol = _build(raw)
    if test_run_marker is not None:
        _check_not_consumed(protocol, Path(test_run_marker), allow_consumed_test)
    return protocol


def loads(
    text: str,
    *,
    test_run_marker: str | Path | None = None,
    allow_consumed_test: bool = False,
) -> Protocol:
    """Validate a protocol from a JSON string (used by tests)."""

    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProtocolError("protocol text is not valid JSON") from exc
    protocol = _build(raw)
    if test_run_marker is not None:
        _check_not_consumed(protocol, Path(test_run_marker), allow_consumed_test)
    return protocol


def from_mapping(mapping: dict[str, Any]) -> Protocol:
    """Validate a protocol from an in-memory mapping (used by tests)."""

    return _build(dict(mapping))


def record_test_run(marker_path: str | Path, protocol: Protocol) -> None:
    """Write the run marker that marks this protocol's test split as consumed."""

    marker = Path(marker_path)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps(
            {
                "protocol_sha256": protocol.frozen_hash(),
                "protocol_version": protocol.protocol_version,
                "consumed_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- #
# Internals                                                                    #
# --------------------------------------------------------------------------- #
def _build(raw: Any) -> Protocol:
    if not isinstance(raw, dict):
        raise ProtocolError("protocol must be a JSON object.")

    missing = REQUIRED_KEYS - set(raw)
    if missing:
        raise ProtocolError(
            "protocol is missing required keys: " + ", ".join(sorted(missing))
        )

    protocol_version = _int(raw["protocol_version"], "protocol_version", minimum=1)

    relevance = raw["relevance"]
    if not isinstance(relevance, dict) or "completed" not in relevance or "rating_half_steps_gte" not in relevance:
        raise ProtocolError("protocol.relevance must set 'completed' and 'rating_half_steps_gte' (D-17).")
    if not isinstance(relevance["completed"], bool):
        raise ProtocolError("protocol.relevance.completed must be a boolean.")
    _int(relevance["rating_half_steps_gte"], "relevance.rating_half_steps_gte", minimum=1, maximum=10)

    k_values = raw["k_values"]
    if not isinstance(k_values, list) or not k_values:
        raise ProtocolError("protocol.k_values must be a non-empty list (D-19).")
    k_tuple = tuple(_int(k, "k_values[]", minimum=1) for k in k_values)

    headline = raw["headline"]
    if not isinstance(headline, str) or not headline.strip():
        raise ProtocolError("protocol.headline must be a non-empty string (D-19).")

    split = raw["split"]
    if not isinstance(split, dict) or not isinstance(split.get("strategy"), str):
        raise ProtocolError("protocol.split must be an object with a 'strategy' string (D-18).")
    _int(split.get("seed"), "split.seed")

    candidate_set = raw["candidate_set"]
    exclusions = raw["exclusions"]
    if not isinstance(candidate_set, str) or not candidate_set.strip():
        raise ProtocolError("protocol.candidate_set must be a non-empty string.")
    if not isinstance(exclusions, str) or not exclusions.strip():
        raise ProtocolError("protocol.exclusions must be a non-empty string (REC-07).")

    metrics = raw["metrics"]
    if not isinstance(metrics, list) or not metrics or not all(isinstance(m, str) and m.strip() for m in metrics):
        raise ProtocolError("protocol.metrics must be a non-empty list of strings (D-22).")

    tuning = raw["tuning"]
    if not isinstance(tuning, dict):
        raise ProtocolError("protocol.tuning must be an object (D-21).")
    for key in ("select_on", "select_split"):
        if not isinstance(tuning.get(key), str) or not tuning[key].strip():
            raise ProtocolError(f"protocol.tuning.{key} must be a non-empty string (D-21).")
    _int(tuning.get("test_runs"), "tuning.test_runs", minimum=1)
    grid = tuning.get("grid")
    if not isinstance(grid, list) or not grid:
        raise ProtocolError("protocol.tuning.grid must be a non-empty list (D-21).")
    if len(grid) > MAX_GRID:
        raise ProtocolError(
            f"protocol.tuning.grid declares {len(grid)} configs; the frozen budget is {MAX_GRID} (D-21)."
        )
    for index, entry in enumerate(grid):
        if not isinstance(entry, dict):
            raise ProtocolError(f"protocol.tuning.grid[{index}] must be an object.")
        if entry.get("combine_mode") not in COMBINE_MODES:
            raise ProtocolError(
                f"protocol.tuning.grid[{index}].combine_mode must be one of {sorted(COMBINE_MODES)}."
            )
        if not isinstance(entry.get("feature_set"), str) or not entry["feature_set"].strip():
            raise ProtocolError(f"protocol.tuning.grid[{index}].feature_set must be a non-empty string.")
        if not isinstance(entry.get("params"), dict):
            raise ProtocolError(f"protocol.tuning.grid[{index}].params must be an object.")

    user_split = raw["user_split"]
    if not isinstance(user_split, dict):
        raise ProtocolError("protocol.user_split must be an object (D-21).")
    for key in ("train", "validation", "test"):
        _int(user_split.get(key), f"user_split.{key}", minimum=0)
    _int(user_split.get("seed"), "user_split.seed")
    if user_split["train"] + user_split["validation"] + user_split["test"] <= 0:
        raise ProtocolError("protocol.user_split sizes must sum to a positive total (D-21).")

    corpus_version = raw["corpus_version"]
    snapshot_sha256 = raw["snapshot_sha256"]
    if corpus_version is not None and not isinstance(corpus_version, str):
        raise ProtocolError("protocol.corpus_version must be a string or null (resolved in 02-13).")
    if snapshot_sha256 is not None and not isinstance(snapshot_sha256, str):
        raise ProtocolError("protocol.snapshot_sha256 must be a string or null (resolved in 02-13).")

    simulation = raw.get("simulation")
    if simulation is not True:
        raise ProtocolError("protocol.simulation must be true — every harness artefact is simulation evidence (EVAL-10).")
    limitation = raw.get("limitation")
    if not isinstance(limitation, str) or not limitation.strip():
        raise ProtocolError("protocol.limitation must be a non-empty string (EVAL-10).")

    return Protocol(
        protocol_version=protocol_version,
        relevance=dict(relevance),
        k_values=k_tuple,
        headline=headline,
        split=dict(split),
        candidate_set=candidate_set,
        exclusions=exclusions,
        metrics=tuple(metrics),
        tuning=dict(tuning),
        user_split=dict(user_split),
        corpus_version=corpus_version,
        snapshot_sha256=snapshot_sha256,
        simulation=True,
        limitation=limitation,
        raw=raw,
    )


def _check_not_consumed(protocol: Protocol, marker: Path, allow: bool) -> None:
    if not marker.exists():
        return
    try:
        record = json.loads(marker.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        record = {}
    same_protocol = record.get("protocol_sha256") == protocol.frozen_hash()
    if same_protocol and not allow:
        raise ProtocolError(
            f"the test split for this protocol has already been consumed (marker: {marker}); "
            "bump protocol_version or pass allow_consumed_test=True."
        )


def _int(value: Any, name: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProtocolError(f"protocol.{name} must be an integer.")
    if minimum is not None and value < minimum:
        raise ProtocolError(f"protocol.{name} must be >= {minimum}.")
    if maximum is not None and value > maximum:
        raise ProtocolError(f"protocol.{name} must be <= {maximum}.")
    return value
