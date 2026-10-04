"""Spreadsheet (.xlsx) export of the caller's own collection.

One row per game in the owner's collection, with the columns the product asks
for: Juego, Estado, Rating IGDB, Rating usuario, Copia, Año, Plataforma,
Desarrollador, Género, Platino and DLC. It is separate from the versioned CSV
portability contract in ``library.export`` (which the import path depends on)
and never touches it.

The workbook is written with the standard library only (``zipfile`` plus a
minimal SpreadsheetML), so no new dependency is needed. Every text cell is a
string cell, so a game title that starts with ``=`` or ``@`` is shown as text
and never evaluated as a formula. The queryset is filtered by ``user=user``
and no other account's data enters it.
"""

from __future__ import annotations

import io
import re
import zipfile
from xml.sax.saxutils import escape

from catalogue.genre_labels_es import GENRE_LABELS_ES
from catalogue.models import RelatedContent
from library.models import BacklogStatus, LibraryEntry, OwnedCopy

EXPORT_XLSX_FILENAMES = {"es": "savepoint-coleccion.xlsx", "en": "savepoint-collection.xlsx"}
EXPORT_XLSX_FILENAME = EXPORT_XLSX_FILENAMES["es"]
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# The sheet follows the interface language the owner has selected: ``lang`` is
# "es" or "en" and anything else falls back to Spanish.
COLUMNS_BY_LANG = {
    "es": (
        "Juego", "Estado", "Rating IGDB", "Rating usuario", "Copia", "Año",
        "Plataforma", "Desarrollador", "Género", "Platino", "DLC",
    ),
    "en": (
        "Game", "Status", "IGDB rating", "User rating", "Copy", "Year",
        "Platform", "Developer", "Genre", "Platinum", "DLC",
    ),
}
COLUMNS = COLUMNS_BY_LANG["es"]
SHEET_NAMES = {"es": "Colección", "en": "Collection"}
_COLUMN_WIDTHS = (38, 14, 13, 15, 8, 8, 34, 30, 40, 9, 44)

_STATUS_LABELS = {
    "es": {
        BacklogStatus.PENDING: "Pendiente",
        BacklogStatus.PLAYING: "Jugando",
        BacklogStatus.COMPLETED: "Completado",
        BacklogStatus.ABANDONED: "Abandonado",
    },
    "en": {
        BacklogStatus.PENDING: "Pending",
        BacklogStatus.PLAYING: "Playing",
        BacklogStatus.COMPLETED: "Completed",
        BacklogStatus.ABANDONED: "Abandoned",
    },
}
_YES_NO = {"es": ("Sí", "No"), "en": ("Yes", "No")}


def normalize_lang(value: str | None) -> str:
    return "en" if value == "en" else "es"

_ILLEGAL_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _title(work, lang: str) -> str:  # noqa: ANN001
    if lang == "es":
        return work.title_es or work.title_en or work.original_title
    return work.title_en or work.original_title


def _yes_no(value: bool, lang: str) -> str:
    return _YES_NO[lang][0] if value else _YES_NO[lang][1]


def _genre_names(work, lang: str) -> list[str]:  # noqa: ANN001
    # Curated tags first (genre, subgenre, theme...); works that were never
    # curated fall back to their IGDB genres so the column is not left empty.
    labels = sorted(work.curated_labels.all(), key=lambda label: label.slug) or sorted(
        work.genres.all(), key=lambda genre: genre.slug
    )
    names = [GENRE_LABELS_ES.get(label.slug, label.name) if lang == "es" else label.name for label in labels]
    return sorted(set(names), key=str.casefold)


def collection_rows(user, lang: str = "es") -> list[list]:  # noqa: ANN001
    """The sheet rows (without the header) for one user's own collection."""
    lang = normalize_lang(lang)
    owned_work_ids = set(
        OwnedCopy.objects.filter(user=user).values_list("work_id", flat=True)
    )
    entries = (
        LibraryEntry.objects.filter(user=user)
        .select_related("work")
        .prefetch_related(
            "work__developers",
            "work__curated_labels",
            "work__genres",
            "work__releases__platform",
            "work__related_children__child_work",
        )
    )
    rows: list[list] = []
    for entry in entries:
        work = entry.work
        platforms = sorted(
            {release.platform.name for release in work.releases.all() if release.platform},
            key=str.casefold,
        )
        developers = sorted((developer.name for developer in work.developers.all()), key=str.casefold)
        dlc = sorted(
            {
                _title(related.child_work, lang)
                for related in work.related_children.all()
                if related.relation in (RelatedContent.Relation.DLC, RelatedContent.Relation.EXPANSION)
            },
            key=str.casefold,
        )
        rows.append(
            [
                _title(work, lang),
                _STATUS_LABELS[lang].get(entry.current_status, ""),
                round(work.total_rating, 1) if work.total_rating is not None else None,
                entry.rating_half_steps / 2 if entry.rating_half_steps is not None else None,
                _yes_no(work.id in owned_work_ids, lang),
                work.first_release_date.year if work.first_release_date else None,
                ", ".join(platforms),
                ", ".join(developers),
                ", ".join(_genre_names(work, lang)),
                _yes_no(entry.is_platinum, lang),
                ", ".join(dlc),
            ]
        )
    rows.sort(key=lambda row: row[0].casefold())
    return rows


def _column_letter(index: int) -> str:
    return chr(ord("A") + index)


def _cell_xml(reference: str, value, style: int = 0) -> str:  # noqa: ANN001
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{reference}" s="{style}"><v>{value}</v></c>'
    text = escape(_ILLEGAL_XML.sub("", str(value)))
    return f'<c r="{reference}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>'


def _sheet_xml(rows: list[list], lang: str) -> str:
    columns = COLUMNS_BY_LANG[lang]
    last_column = _column_letter(len(columns) - 1)
    last_row = len(rows) + 1
    cols = "".join(
        f'<col min="{i + 1}" max="{i + 1}" width="{width}" customWidth="1"/>'
        for i, width in enumerate(_COLUMN_WIDTHS)
    )
    header = "".join(_cell_xml(f"{_column_letter(i)}1", name, style=1) for i, name in enumerate(columns))
    body = []
    for row_index, row in enumerate(rows, start=2):
        cells = "".join(_cell_xml(f"{_column_letter(i)}{row_index}", value) for i, value in enumerate(row))
        body.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f"<cols>{cols}</cols>"
        f'<sheetData><row r="1">{header}</row>{"".join(body)}</sheetData>'
        f'<autoFilter ref="A1:{last_column}{last_row}"/>'
        "</worksheet>"
    )


_STYLES_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="2">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    "</cellXfs></styleSheet>"
)

_CONTENT_TYPES_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    "</Types>"
)

_ROOT_RELS_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="xl/workbook.xml"/></Relationships>'
)

def _workbook_xml(lang: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{SHEET_NAMES[lang]}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )


_WORKBOOK_RELS_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
    'Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
    'Target="styles.xml"/></Relationships>'
)


def render_collection_xlsx(user, lang: str = "es") -> bytes:  # noqa: ANN001
    """The complete workbook for one user's own collection, as bytes."""
    lang = normalize_lang(lang)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES_XML)
        archive.writestr("_rels/.rels", _ROOT_RELS_XML)
        archive.writestr("xl/workbook.xml", _workbook_xml(lang))
        archive.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS_XML)
        archive.writestr("xl/styles.xml", _STYLES_XML)
        archive.writestr("xl/worksheets/sheet1.xml", _sheet_xml(collection_rows(user, lang), lang))
    return buffer.getvalue()
