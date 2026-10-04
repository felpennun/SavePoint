"""Owner-scoped CSV export contract (PORT-01/PORT-04, D-08/D-09).

Only CSV is implemented -- deliberately. JSON export, import preview, and
import conflict handling are out of scope by decision D-09 and are tracked
as pending in ``05-PORTABILITY-RECONCILIATION.md``; this module never grows
an import/parse path.

Every row is built from explicitly named fields taken directly from the
caller's own ``FavoriteSlot``/``LibraryEntry``/``OwnedCopy``/``GameComment``/
``CustomListItem`` rows -- never from a wide ``values()`` queryset, never
from ``__dict__``, and never from the public-profile projection. There is no
``password``, session, or internal-ID column, and no other user's data ever
enters the query (every queryset below is filtered by ``user=user`` or, for
list items, ``list__user=user``).
"""

from __future__ import annotations

import csv
import io
from typing import Any

from accounts.models import FavoriteSlot
from library.models import CustomListItem, GameComment, LibraryEntry, OwnedCopy

# Bumped whenever a column is added, removed, or renamed -- a consumer can
# detect a contract change by reading this single cell instead of guessing
# from the header shape.
CSV_SCHEMA_VERSION = 1

# Fixed, explicit column order (Pattern 5, 05-RESEARCH.md). Fields that do
# not apply to a given ``record_type`` are always emitted empty, never
# omitted -- every row has exactly this shape.
CSV_FIELDNAMES = [
    "schema_version",
    "record_type",
    "work_slug",
    "work_title",
    "status",
    "rating_half_steps",
    "copy_format",
    "purchase_date",
    "price",
    "currency",
    "store",
    "conservation_state",
    "storage_location",
    "comment",
    "list_name",
    "list_visibility",
    "list_position",
    "favorite_slot",
]

# A fixed, non-user-derived filename -- never built from the alias or any
# other caller-controlled text, so there is nothing here for a hostile
# username to inject into a response header.
EXPORT_FILENAME = "savepoint-collection-export.csv"

_FORMULA_PREFIXES = ("=", "+", "-", "@")


def neutralize_spreadsheet_formula(value: str) -> str:
    """OWASP CSV-injection mitigation: a cell whose first character could be
    interpreted as a spreadsheet formula (``=``, ``+``, ``-``, ``@``) is
    prefixed with a tab so a spreadsheet application opens it as inert text
    instead of executing it. Idempotent: a value that already carries the
    tab prefix is never prefixed a second time, so replaying the same export
    can never accumulate tabs or drift the output."""
    if value.startswith("\t"):
        return value
    if value[:1] in _FORMULA_PREFIXES:
        return "\t" + value
    return value


def _cell(value: Any) -> str:  # noqa: ANN401 - deliberately accepts any model field value
    """Stringifies and neutralizes one cell. Every column goes through this
    identical path -- there is no column exempt from the formula check,
    including ones that look purely numeric today."""
    if value is None:
        return ""
    return neutralize_spreadsheet_formula(str(value))


def _work_title(work) -> str:  # noqa: ANN001
    return work.title_en or work.original_title


def _base_row(record_type: str) -> dict:
    row: dict = dict.fromkeys(CSV_FIELDNAMES)
    row["schema_version"] = CSV_SCHEMA_VERSION
    row["record_type"] = record_type
    return row


def _favorite_rows(user) -> list[tuple[tuple, dict]]:  # noqa: ANN001
    """One row per occupied favorite slot (D-02). ``slot`` is unique per
    user by ``FavoriteSlot``'s own constraint, so it is already a total
    order on its own; the work id is kept as a stable secondary key only for
    consistency with the other sections."""
    rows = []
    for slot in FavoriteSlot.objects.filter(user=user).select_related("work"):
        row = _base_row("favorite")
        row["work_slug"] = slot.work.canonical_slug
        row["work_title"] = _work_title(slot.work)
        row["favorite_slot"] = slot.slot
        rows.append(((slot.slot, str(slot.work_id)), row))
    return rows


def _collection_rows(user) -> list[tuple[tuple, dict]]:  # noqa: ANN001
    """One row per ``LibraryEntry`` (status/rating), sorted by
    ``work_slug``; ties (which cannot occur today, since ``work_slug`` is
    unique per work and a user has at most one entry per work, but are
    still guarded for future-proofing) are broken by the work's own stable
    UUID, never written to the CSV."""
    rows = []
    for entry in LibraryEntry.objects.filter(user=user).select_related("work"):
        row = _base_row("collection")
        row["work_slug"] = entry.work.canonical_slug
        row["work_title"] = _work_title(entry.work)
        row["status"] = entry.current_status
        row["rating_half_steps"] = entry.rating_half_steps
        rows.append(((entry.work.canonical_slug, str(entry.work_id)), row))
    return rows


def _copy_rows(user) -> list[tuple[tuple, dict]]:  # noqa: ANN001
    """One row per owned copy (INV-03/INV-04). A user can own several
    copies of the same work, so ties on ``work_slug`` are broken by the
    copy's own stable UUID -- never the incidental order the queryset
    happened to return."""
    rows = []
    for copy in OwnedCopy.objects.filter(user=user).select_related("work"):
        row = _base_row("copy")
        row["work_slug"] = copy.work.canonical_slug
        row["work_title"] = _work_title(copy.work)
        row["copy_format"] = copy.format
        row["purchase_date"] = copy.purchase_date.isoformat() if copy.purchase_date else None
        row["price"] = copy.price
        row["currency"] = copy.currency
        row["store"] = copy.store
        row["conservation_state"] = copy.conservation_state
        row["storage_location"] = copy.storage_location
        rows.append(((copy.work.canonical_slug, str(copy.work_id), str(copy.id)), row))
    return rows


def _comment_rows(user) -> list[tuple[tuple, dict]]:  # noqa: ANN001
    """One row per comment (LIB-03). A user may write several comments per
    work, so the comment's own UUID is the final tie-break."""
    rows = []
    for comment in GameComment.objects.filter(user=user).select_related("work"):
        row = _base_row("comment")
        row["work_slug"] = comment.work.canonical_slug
        row["work_title"] = _work_title(comment.work)
        row["comment"] = comment.text
        rows.append(((comment.work.canonical_slug, str(comment.work_id), str(comment.id)), row))
    return rows


def _list_item_rows(user) -> list[tuple[tuple, dict]]:  # noqa: ANN001
    """One row per item across all of the caller's own custom lists
    (LIB-04). Sorted by list name, then item position -- ties (two lists
    sharing a name, or -- impossible today but guarded -- two items sharing
    a position) are broken by the list's and the item's own stable UUIDs,
    never written to the CSV."""
    rows = []
    items = CustomListItem.objects.filter(list__user=user).select_related("list", "work")
    for item in items:
        row = _base_row("list_item")
        row["work_slug"] = item.work.canonical_slug
        row["work_title"] = _work_title(item.work)
        row["list_name"] = item.list.name
        row["list_visibility"] = item.list.visibility
        row["list_position"] = item.position
        rows.append(((item.list.name, str(item.list_id), item.position, str(item.id)), row))
    return rows


def build_export_rows(user) -> list[dict]:  # noqa: ANN001
    """The complete, deterministically-ordered set of export rows for one
    user's own data (PORT-01/PORT-04).

    Section order is fixed (favorites, collection, copies, comments, list
    items); within each section, rows are sorted by the columns actually
    exported (slot / work_slug / list_name+position), with internal stable
    UUIDs (never written to the CSV) as the final tie-break. The result
    never depends on a queryset's incidental iteration order, so two
    exports of unchanged data are byte-identical.
    """
    sections = [
        _favorite_rows(user),
        _collection_rows(user),
        _copy_rows(user),
        _comment_rows(user),
        _list_item_rows(user),
    ]
    ordered_rows: list[dict] = []
    for section in sections:
        for _, row in sorted(section, key=lambda pair: pair[0]):
            ordered_rows.append(row)
    return ordered_rows


def render_collection_csv(user) -> bytes:  # noqa: ANN001
    """Renders the complete CSV for one user's own data as UTF-8 bytes.

    Uses ``csv`` from the standard library (never manual comma/quote
    concatenation) with ``newline=""`` per the module's own documented
    requirement for correct line-ending handling. Every cell -- including
    ones that look purely numeric -- passes through ``neutralize_spreadsheet_
    formula`` before being written.
    """
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_FIELDNAMES)
    for row in build_export_rows(user):
        writer.writerow([_cell(row[field]) for field in CSV_FIELDNAMES])
    return buffer.getvalue().encode("utf-8")
