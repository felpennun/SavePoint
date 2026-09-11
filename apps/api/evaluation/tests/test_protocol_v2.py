"""Additional guards for the additive Phase 3 protocol v3 contract."""

from __future__ import annotations

import copy

import pytest

from evaluation import protocol
from evaluation.protocol import ProtocolError


def test_checked_in_protocol_is_v2_and_hash_is_reproducible() -> None:
    first = protocol.load()
    second = protocol.load()

    assert first.protocol_version == 14
    assert first.frozen_hash() == second.frozen_hash()


def test_v3_cutoff_is_validated_without_changing_v1_loader() -> None:
    raw = copy.deepcopy(protocol.load().raw)
    raw["eligibility_cutoff_date"] = "2026-09-08"

    parsed = protocol.from_mapping(raw)

    assert parsed.eligibility_cutoff_date.isoformat() == "2026-09-08"
    assert protocol.from_mapping({**raw, "protocol_version": 1}).protocol_version == 1


def test_invalid_cutoff_is_rejected_before_a_run() -> None:
    raw = copy.deepcopy(protocol.load().raw)
    raw["eligibility_cutoff_date"] = "not-a-date"

    with pytest.raises(ProtocolError, match="eligibility_cutoff_date"):
        protocol.from_mapping(raw)


def test_service_version_guard_rejects_v1() -> None:
    raw = copy.deepcopy(protocol.load().raw)
    raw["protocol_version"] = 1
    parsed = protocol.from_mapping(raw)

    with pytest.raises(ProtocolError, match="expected protocol_version 6"):
        protocol.require_version(parsed, 6)


def test_incomplete_artifact_is_rejected_closed() -> None:
    raw = copy.deepcopy(protocol.load().raw)
    raw.pop("candidate_set")

    with pytest.raises(ProtocolError, match="missing required keys"):
        protocol.from_mapping(raw)
