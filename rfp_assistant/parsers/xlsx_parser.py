"""Parse requirements out of an RFP response workbook.

The hard part is not reading cells, it is deciding which cells are
requirements. A real response workbook mixes requirement tables with
instructions, pricing models, scoring rollups, and exception logs, and puts a
metadata block above the header row so the table does not start at A1.

Rather than hardcode tab names, this finds requirement tables structurally: a
tab qualifies only if it contains a header row pairing an id-like column with
a requirement-like column. That generalises to workbooks whose tabs are named
differently, and it correctly rejects the pricing and scoring tabs, which have
neither.
"""

from __future__ import annotations

import re
from pathlib import Path

from openpyxl import load_workbook

from ..models import Requirement

ID_HEADERS = {"req id", "requirement id", "ref", "reference", "id", "item"}
TEXT_HEADERS = {"requirement", "question", "description", "requirement text"}
PRIORITY_HEADERS = {"priority", "criticality", "mandatory"}
WEIGHT_HEADERS = {"weight", "weighting", "score weight"}

# Rows whose id cell matches this are worked examples, not requirements.
EXAMPLE_RE = re.compile(r"^\s*(example|sample|e\.g\.)\b", re.I)

# A requirement id: 4, 4.2, or 4.2.3. Anything else in the id column
# (a banner, a stray note) is not a requirement.
RID_RE = re.compile(r"^\d+(?:\.\d+)*$")

HEADER_SEARCH_ROWS = 20


def _norm(value) -> str:
    return str(value).strip().lower() if value is not None else ""


def _find_header(ws) -> tuple[int, dict[str, int]] | None:
    """Locate the header row and map logical column -> column index."""
    for row in range(1, min(HEADER_SEARCH_ROWS, ws.max_row) + 1):
        labels = {
            _norm(ws.cell(row=row, column=col).value): col
            for col in range(1, min(ws.max_column, 40) + 1)
        }
        labels.pop("", None)
        id_col = next((labels[h] for h in labels if h in ID_HEADERS), None)
        text_col = next((labels[h] for h in labels if h in TEXT_HEADERS), None)
        if id_col is None or text_col is None:
            continue
        mapping = {"id": id_col, "text": text_col}
        for key, names in (("priority", PRIORITY_HEADERS), ("weight", WEIGHT_HEADERS)):
            col = next((labels[h] for h in labels if h in names), None)
            if col is not None:
                mapping[key] = col
        return row, mapping
    return None


def _coerce_weight(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_xlsx(path: str | Path) -> list[Requirement]:
    wb = load_workbook(path, data_only=True, read_only=False)
    out: list[Requirement] = []

    for ws in wb.worksheets:
        found = _find_header(ws)
        if not found:
            continue  # Instructions, Pricing Workbook, Scoring Summary, Exceptions Log
        header_row, cols = found

        section_title = ""
        first = ws.cell(row=1, column=1).value
        if isinstance(first, str) and first.strip():
            section_title = first.strip()
        if m := re.match(r"^Section\s+\d+\s*[-–—]\s*(.+)$", section_title):
            section_title = m.group(1).strip()

        subsection = subsection_title = ""

        for row in range(header_row + 1, ws.max_row + 1):
            raw_id = ws.cell(row=row, column=cols["id"]).value
            raw_text = ws.cell(row=row, column=cols["text"]).value
            id_str = str(raw_id).strip() if raw_id is not None else ""
            text_str = str(raw_text).strip() if raw_text is not None else ""

            if not id_str and not text_str:
                continue

            # Merged subsection banner: the merge anchor sits in the id column
            # and every other cell in the row is empty.
            if id_str and not text_str:
                banner = re.match(r"^(\d+(?:\.\d+)*)\s+(.*)$", id_str)
                if banner:
                    subsection, subsection_title = banner.group(1), banner.group(2).strip()
                continue

            if EXAMPLE_RE.match(id_str):
                continue
            if not RID_RE.match(id_str):
                continue

            out.append(
                Requirement(
                    rid=id_str,
                    text=text_str,
                    # Id is authoritative; see pdf_parser for why.
                    section=id_str.split(".")[0],
                    section_title=section_title,
                    subsection=subsection,
                    subsection_title=subsection_title,
                    priority=(
                        str(ws.cell(row=row, column=cols["priority"]).value).strip()
                        if "priority" in cols
                        and ws.cell(row=row, column=cols["priority"]).value is not None
                        else None
                    ),
                    weight=(
                        _coerce_weight(ws.cell(row=row, column=cols["weight"]).value)
                        if "weight" in cols
                        else None
                    ),
                    source_format="xlsx",
                    locator=f"{ws.title}!A{row}",
                )
            )

    wb.close()
    return out


def requirement_tabs(path: str | Path) -> list[str]:
    """Tabs that contain a requirement table. Useful for diagnostics."""
    wb = load_workbook(path, read_only=True)
    tabs = [ws.title for ws in wb.worksheets if _find_header(ws)]
    wb.close()
    return tabs
