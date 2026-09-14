"""Redacted operation logging contract (OPS-05, D-07-08)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from config.observability import SensitiveOperationData, emit_operation_event


def _event_kwargs() -> dict:
    return {
        "operation_ref": uuid.uuid4(),
        "actor": "technical-operator",
        "operation_type": "restore",
        "status": "failed",
        "started_at": datetime(2026, 9, 14, tzinfo=timezone.utc),
        "finished_at": datetime(2026, 9, 14, 0, 0, 1, tzinfo=timezone.utc),
        "duration_ms": 1000,
        "resource_type": "restore",
        "resource_id": "weekly-20260914",
    }


def test_operation_event_is_allowlisted_and_redacts_hostile_error(caplog: pytest.LogCaptureFixture) -> None:
    hostile = "Traceback in C:\\private\\dump.dump https://example.invalid?token=secret payload=private"
    with caplog.at_level("INFO", logger="savepoint.operations"):
        event = emit_operation_event(**_event_kwargs(), error=hostile)

    assert event["status"] == "failed"
    assert event["error_code"] == "operation_failed"
    assert hostile not in caplog.text
    assert "dump.dump" not in caplog.text
    assert "secret" not in caplog.text
    logged = json.loads(caplog.records[-1].message)
    assert logged == event
    assert set(event) <= {
        "operation_ref",
        "actor",
        "operation_type",
        "status",
        "started_at",
        "finished_at",
        "duration_ms",
        "resource_type",
        "resource_id",
        "error_code",
    }


@pytest.mark.parametrize("resource_id", ["C:\\private\\backup.dump", "https://example.invalid", "payload={}"])
def test_operation_event_rejects_paths_urls_and_payload_identifiers(resource_id: str) -> None:
    kwargs = _event_kwargs()
    kwargs["resource_id"] = resource_id
    with pytest.raises(SensitiveOperationData):
        emit_operation_event(**kwargs)


def test_operation_event_rejects_unknown_fields_and_states() -> None:
    kwargs = _event_kwargs()
    kwargs["status"] = "unknown"
    with pytest.raises(SensitiveOperationData):
        emit_operation_event(**kwargs)
    with pytest.raises(TypeError):
        emit_operation_event(**_event_kwargs(), password="never-accepted")
