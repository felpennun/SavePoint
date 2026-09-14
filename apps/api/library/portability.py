"""Validated, owner-scoped CSV collection import (PORT-02/PORT-03).

The export contract intentionally has no internal IDs or idempotency keys.  An
import therefore derives a stable logical key from the record type, work slug,
and the ordinal of that record type in the file.  Replaying an unchanged file
is a no-op; changing a row at the same logical position is a conflict.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction

from catalogue.models import GameRelease, GameWork
from library.export import CSV_FIELDNAMES, CSV_SCHEMA_VERSION
from library.models import BacklogStatus, LibraryEntry, OwnedCopy
from library.services import create_owned_copy

MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_IMPORT_ROWS = 5000
SUPPORTED_RECORD_TYPES = frozenset({"collection", "copy"})
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_COPY_FORMATS = frozenset({"physical", "digital"})
_CONSERVATION_STATES = frozenset({"new", "good", "fair", "poor", "damaged"})


@dataclass(frozen=True)
class ImportRow:
    row_number: int
    record_type: str
    work: GameWork
    logical_key: str
    values: dict[str, Any]


@dataclass(frozen=True)
class ImportReport:
    raw_bytes: bytes
    preview_sha256: str
    user: Any
    rows: tuple[ImportRow, ...]
    errors: tuple[dict[str, Any], ...]
    duplicates: int
    conflicts: int

    def as_dict(self) -> dict[str, Any]:
        creates = 0
        unchanged = self.duplicates
        for row in self.rows:
            if row.record_type == "collection":
                existing = LibraryEntry.objects.filter(user=self.user, work=row.work).first()
                if existing is None:
                    creates += 1
            else:
                existing = OwnedCopy.objects.filter(
                    user=self.user, idempotency_key=row.logical_key
                ).first()
                if existing is None:
                    creates += 1

        return {
            "preview_sha256": self.preview_sha256,
            "schema_version": CSV_SCHEMA_VERSION,
            "row_count": len(self.rows) + len(self.errors),
            "valid_row_count": len(self.rows),
            "error_count": len(self.errors),
            "errors": list(self.errors),
            "will_create": creates,
            "duplicates": self.duplicates,
            "conflicts": self.conflicts,
            "can_apply": not self.errors and not self.conflicts,
        }


def _error(row_number: int, code: str, message: str) -> dict[str, Any]:
    return {"row": row_number, "code": code, "message": message}


def _logical_key(record_type: str, work_slug: str, ordinal: int) -> str:
    material = f"savepoint-import-v1|{record_type}|{work_slug}|{ordinal}".encode("utf-8")
    return "import-v1-" + hashlib.sha256(material).hexdigest()[:80]


def _blank(value: str) -> bool:
    return value == ""


def _parse_date(value: str, row_number: int) -> date | None:
    if _blank(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("purchase_date must be an ISO date") from exc


def _parse_price(value: str, row_number: int) -> Decimal | None:
    if _blank(value):
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("price must be a decimal amount") from exc
    if parsed < 0 or parsed.as_tuple().exponent < -2 or len(parsed.as_tuple().digits) > 10:
        raise ValueError("price is outside the supported range")
    return parsed


def _parse_rating(value: str) -> int | None:
    if _blank(value):
        return None
    if not value.isdigit() or not 1 <= int(value) <= 10:
        raise ValueError("rating_half_steps must be an integer from 1 to 10")
    return int(value)


def _validate_common_row(row: dict[str, str], row_number: int, ordinal: int) -> ImportRow | None:
    record_type = row.get("record_type", "")
    if record_type not in SUPPORTED_RECORD_TYPES:
        raise ValueError("record_type is not importable")
    slug = row.get("work_slug", "").strip()
    if not slug:
        raise ValueError("work_slug is required")
    work = GameWork.objects.filter(canonical_slug=slug, is_dlc=False).first()
    if work is None:
        raise ValueError("work_slug does not identify a catalogue work")

    logical_key = _logical_key(record_type, slug, ordinal)
    if record_type == "collection":
        status = row.get("status", "") or None
        if status is not None and status not in {choice.value for choice in BacklogStatus}:
            raise ValueError("status is not supported")
        return ImportRow(
            row_number,
            record_type,
            work,
            logical_key,
            {"status": status, "rating_half_steps": _parse_rating(row.get("rating_half_steps", ""))},
        )

    copy_format = row.get("copy_format", "")
    if copy_format not in _COPY_FORMATS:
        raise ValueError("copy_format must be physical or digital")
    release = GameRelease.objects.filter(work=work).order_by("release_date", "release_name", "id").first()
    if release is None:
        raise ValueError("work has no importable release")
    currency = row.get("currency", "") or None
    if currency is not None:
        currency = currency.upper()
        if _CURRENCY_PATTERN.fullmatch(currency) is None:
            raise ValueError("currency must be exactly three letters")
    conservation_state = row.get("conservation_state", "") or None
    storage_location = row.get("storage_location", "") or None
    if conservation_state is not None and conservation_state not in _CONSERVATION_STATES:
        raise ValueError("conservation_state is not supported")
    if copy_format == "digital" and (conservation_state is not None or storage_location is not None):
        raise ValueError("digital copies cannot record physical metadata")
    store = row.get("store", "") or None
    if store is not None and len(store) > 120:
        raise ValueError("store exceeds the supported length")
    if storage_location is not None and len(storage_location) > 200:
        raise ValueError("storage_location exceeds the supported length")
    return ImportRow(
        row_number,
        record_type,
        work,
        logical_key,
        {
            "release_id": str(release.id),
            "format": copy_format,
            "purchase_date": _parse_date(row.get("purchase_date", ""), row_number),
            "price": _parse_price(row.get("price", ""), row_number),
            "currency": currency,
            "store": store,
            "conservation_state": conservation_state,
            "storage_location": storage_location,
        },
    )


def parse_import_csv(raw_bytes: bytes, *, user) -> ImportReport:
    """Parse and validate an upload without mutating the database."""
    digest = hashlib.sha256(raw_bytes).hexdigest()
    errors: list[dict[str, Any]] = []
    rows: list[ImportRow] = []
    if len(raw_bytes) > MAX_IMPORT_BYTES:
        return ImportReport(raw_bytes, digest, user, (), (_error(1, "file_too_large", "file exceeds the upload limit"),), 0, 0)
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return ImportReport(raw_bytes, digest, user, (), (_error(1, "invalid_encoding", "file must be valid UTF-8"),), 0, 0)

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != CSV_FIELDNAMES:
        return ImportReport(raw_bytes, digest, user, (), (_error(1, "invalid_header", "CSV header does not match schema version 1"),), 0, 0)

    ordinals: dict[str, int] = {}
    file_keys: dict[str, ImportRow] = {}
    for row_number, row in enumerate(reader, start=2):
        if row_number - 1 > MAX_IMPORT_ROWS:
            errors.append(_error(row_number, "too_many_rows", "file exceeds the row limit"))
            break
        if None in row:
            errors.append(_error(row_number, "malformed_row", "row has more cells than the fixed schema"))
            continue
        if row.get("schema_version") != str(CSV_SCHEMA_VERSION):
            errors.append(_error(row_number, "schema_version", "schema_version must be 1"))
            continue
        record_type = row.get("record_type", "")
        ordinals[record_type] = ordinals.get(record_type, 0) + 1
        try:
            parsed = _validate_common_row(row, row_number, ordinals[record_type])
        except (ValueError, TypeError):
            # Do not include raw cells or exception text in API responses.
            errors.append(_error(row_number, "invalid_row", "row contains invalid import data"))
            continue
        if parsed is None:
            continue
        prior = file_keys.get(parsed.logical_key)
        if prior is not None:
            if prior.values != parsed.values:
                errors.append(_error(row_number, "conflict", "row conflicts with another row in this file"))
            else:
                # Identical rows in the same file are deterministic no-ops.
                rows.append(parsed)
            continue
        file_keys[parsed.logical_key] = parsed
        rows.append(parsed)

    duplicates, conflicts = _existing_outcomes(user, rows)
    return ImportReport(raw_bytes, digest, user, tuple(rows), tuple(errors), duplicates, conflicts)


def _existing_outcomes(user, rows: list[ImportRow] | tuple[ImportRow, ...]) -> tuple[int, int]:
    duplicates = 0
    conflicts = 0
    for row in rows:
        if row.record_type == "collection":
            existing = LibraryEntry.objects.filter(user=user, work=row.work).first()
            if existing is None:
                continue
            expected = (existing.current_status, existing.rating_half_steps)
            actual = (row.values["status"], row.values["rating_half_steps"])
        else:
            existing = OwnedCopy.objects.filter(user=user, idempotency_key=row.logical_key).first()
            if existing is None:
                continue
            expected = {
                "release_id": str(existing.release_id),
                "format": existing.format,
                "purchase_date": existing.purchase_date,
                "price": existing.price,
                "currency": existing.currency,
                "store": existing.store,
                "conservation_state": existing.conservation_state,
                "storage_location": existing.storage_location,
            }
            actual = row.values
        if expected == actual:
            duplicates += 1
        else:
            conflicts += 1
    return duplicates, conflicts


def apply_import(report: ImportReport, *, user) -> dict[str, Any]:
    """Apply a previously validated report atomically after a second preflight."""
    if report.errors:
        return report.as_dict()
    with transaction.atomic():
        duplicates, conflicts = _existing_outcomes(user, report.rows)
        if conflicts:
            return {**report.as_dict(), "duplicates": duplicates, "conflicts": conflicts, "can_apply": False}
        created = 0
        unchanged = 0
        for row in report.rows:
            if row.record_type == "collection":
                entry, was_created = LibraryEntry.objects.get_or_create(
                    user=user,
                    work=row.work,
                    defaults={
                        "current_status": row.values["status"],
                        "rating_half_steps": row.values["rating_half_steps"],
                    },
                )
                if was_created:
                    created += 1
                else:
                    unchanged += 1
                continue
            copy, was_created = create_owned_copy(
                user=user,
                work=row.work,
                edition_id=None,
                idempotency_key=row.logical_key,
                **row.values,
            )
            del copy
            if was_created:
                created += 1
            else:
                unchanged += 1
        return {
            **report.as_dict(),
            "applied": True,
            "created": created,
            "unchanged": unchanged,
            "can_apply": True,
        }
