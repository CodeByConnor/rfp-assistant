"""Parse requirements out of a prose-style RFP PDF.

The dominant failure mode here is over-extraction, not under-extraction. RFP
front matter (submission instructions, terms, attestations) is written in the
same obligation register as the requirements themselves -- the Alderwood
fixture carries 188 "must"/"shall" occurrences, and four pages that are pure
obligation language containing no requirements at all. Anything keying on
those words pulls in the boilerplate.

What separates a requirement from boilerplate is not vocabulary but position:
requirements are introduced by a hierarchical identifier at the start of a
line. This parser keys on that, drops repeating page furniture, and stitches
wrapped continuation lines back onto the requirement they belong to.

Limitation worth stating plainly: this is a structural parser, and the fixture
it is tested against numbers every requirement as N.N.N. A real RFP may use
"REQ-4.2.3", "4.2.3)", or bare prose with no identifiers at all, and this
parser will find nothing in those. `parse_pdf` reports how much of the
document it accounted for so a caller can detect that case and escalate to an
LLM extraction pass rather than silently returning a short list.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from ..models import Requirement

# A requirement opener: "4.2.3  Describe ..." at the start of a line. Requires
# at least three levels, which is what separates a requirement from a section
# heading ("7. Information Security") or a TOC entry ("2.  Procurement
# Timeline").
REQ_RE = re.compile(r"^(\d+\.\d+\.\d+)\s+(.*)$")

SECTION_RE = re.compile(r"^(\d+)\.\s+(.{3,80})$")
SUBSECTION_RE = re.compile(r"^(\d+\.\d+)\s+(.{3,80})$")
APPENDIX_RE = re.compile(r"^Appendix\s+[A-Z]\.", re.I)

# Fraction of pages a line must appear on to be treated as page furniture.
FURNITURE_PAGE_RATIO = 0.6

# How many lines at the top and bottom of a page can be furniture.
EDGE_LINES = 2

PRIORITY_TAG_RE = re.compile(r"\s*\[(Must|Should|Nice)\]\s*$", re.I)


@dataclass
class PdfParseResult:
    requirements: list[Requirement]
    pages: int
    lines_total: int
    lines_consumed: int

    @property
    def coverage(self) -> float:
        """Share of body lines attributed to a requirement.

        Low coverage does not mean failure -- front matter is legitimately not
        a requirement -- but a sharp drop against a known-good document is a
        signal that the numbering scheme was not recognised.
        """
        return self.lines_consumed / self.lines_total if self.lines_total else 0.0


def _normalise(line: str) -> str:
    """Collapse digits so "Page 7" and "Page 8" compare equal."""
    return re.sub(r"\d+", "#", line).strip()


def _furniture(pages: list[list[str]]) -> set[str]:
    """Normalised lines that repeat at the edges of most pages.

    Detecting furniture by repetition rather than by pattern matters: header
    and footer text is document-specific, and extraction merges a left-aligned
    footer with a right-aligned page number into a single line, so the shape is
    not predictable in advance. Repetition is.

    Repetition alone is not sufficient, though. Short recurring body text
    repeats just as reliably: a priority tag that wraps onto a line of its own
    appears on nearly every page and is indistinguishable from a footer by
    frequency, so a frequency-only rule silently eats it. Furniture is defined
    by *position* -- it sits at the top or bottom of the page -- so only lines
    at the page edges are eligible.
    """
    if len(pages) < 3:
        return set()
    counts = Counter()
    for lines in pages:
        edge_lines = lines[:EDGE_LINES] + lines[-EDGE_LINES:]
        for line in {_normalise(ln) for ln in edge_lines}:
            counts[line] += 1
    threshold = max(2, int(len(pages) * FURNITURE_PAGE_RATIO))
    return {line for line, count in counts.items() if count >= threshold}


def _clean_pages(path: str | Path) -> list[list[str]]:
    with pdfplumber.open(path) as pdf:
        raw = [
            [ln.strip() for ln in (page.extract_text() or "").split("\n") if ln.strip()]
            for page in pdf.pages
        ]
    furniture = _furniture(raw)
    return [[ln for ln in lines if _normalise(ln) not in furniture] for lines in raw]


def parse_pdf_detailed(path: str | Path) -> PdfParseResult:
    pages = _clean_pages(path)

    out: list[Requirement] = []
    section = section_title = ""
    subsection = subsection_title = ""
    current: dict | None = None
    consumed = 0
    total = 0
    in_appendix = False

    def flush() -> None:
        nonlocal current
        if current is None:
            return
        text = " ".join(current["parts"]).strip()
        text = re.sub(r"\s+", " ", text)
        priority = None
        tag = PRIORITY_TAG_RE.search(text)
        if tag:
            priority = tag.group(1).title()
            text = PRIORITY_TAG_RE.sub("", text).strip()
        out.append(
            Requirement(
                rid=current["rid"],
                text=text,
                # The id is authoritative for section membership. Display
                # headings are not: this document numbers the requirement
                # sections 7-14 because front matter occupies 1-6, while the
                # ids inside them still begin 1.x.
                section=current["rid"].split(".")[0],
                section_title=current["section_title"],
                subsection=current["subsection"],
                subsection_title=current["subsection_title"],
                priority=priority,
                source_format="pdf",
                locator=f"p{current['page']}",
            )
        )
        current = None

    for page_no, lines in enumerate(pages, start=1):
        for line in lines:
            total += 1

            # Only a real appendix heading ends the requirement body. The same
            # string appears in the table of contents, which sits *before* any
            # requirement -- treating that as the appendix would discard every
            # continuation line in the document.
            if APPENDIX_RE.match(line) and out:
                flush()
                in_appendix = True
                continue

            m = REQ_RE.match(line)
            if m:
                flush()
                current = {
                    "rid": m.group(1),
                    "parts": [m.group(2)],
                    "section": section,
                    "section_title": section_title,
                    "subsection": subsection,
                    "subsection_title": subsection_title,
                    "page": page_no,
                }
                consumed += 1
                continue

            if in_appendix:
                continue

            sub = SUBSECTION_RE.match(line)
            if sub:
                flush()
                subsection, subsection_title = sub.group(1), sub.group(2).strip()
                continue

            sec = SECTION_RE.match(line)
            if sec:
                flush()
                section, section_title = sec.group(1), sec.group(2).strip()
                subsection = subsection_title = ""
                continue

            if current is not None:
                # Continuation of the requirement in progress.
                current["parts"].append(line)
                consumed += 1

    flush()
    return PdfParseResult(
        requirements=out,
        pages=len(pages),
        lines_total=total,
        lines_consumed=consumed,
    )


def parse_pdf(path: str | Path) -> list[Requirement]:
    return parse_pdf_detailed(path).requirements
