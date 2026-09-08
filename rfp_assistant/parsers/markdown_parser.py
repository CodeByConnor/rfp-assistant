"""Parse requirements out of the Markdown control format.

This format is generated, so it is regular by construction. It exists as the
baseline: a parser bug that shows up here is a bug in the shared logic, not in
xlsx or pdf handling.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..models import Requirement

SECTION_RE = re.compile(r"^##\s+Section\s+(\d+)\s*[-–—]\s*(.+)$")
SUBSECTION_RE = re.compile(r"^###\s+(\d+\.\d+)\s+(.+)$")
REQ_RE = re.compile(r"^\*\*(\d+(?:\.\d+)*)\*\*(?:\s+_\[(\w+),\s*weight\s*(\d+)\]_)?\s*$")


def parse_markdown(path: str | Path) -> list[Requirement]:
    lines = Path(path).read_text().splitlines()
    out: list[Requirement] = []
    section = section_title = subsection = subsection_title = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if m := SECTION_RE.match(line):
            section, section_title = m.group(1), m.group(2).strip()
            subsection = subsection_title = ""
            i += 1
            continue

        if m := SUBSECTION_RE.match(line):
            subsection, subsection_title = m.group(1), m.group(2).strip()
            i += 1
            continue

        if m := REQ_RE.match(line):
            rid, priority, weight = m.group(1), m.group(2), m.group(3)
            body: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].strip():
                body.append(lines[j].strip())
                j += 1
            if body:
                out.append(
                    Requirement(
                        rid=rid,
                        text=" ".join(body),
                        section=rid.split(".")[0],
                        section_title=section_title,
                        subsection=subsection,
                        subsection_title=subsection_title,
                        priority=priority,
                        weight=int(weight) if weight else None,
                        source_format="md",
                        locator=f"line {i + 1}",
                    )
                )
            i = j
            continue

        i += 1

    return out
