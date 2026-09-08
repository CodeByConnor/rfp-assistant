"""Parser tests.

The fixtures are generated from `fixtures/requirements_data.py`, so that module
is the oracle: every parser must reproduce it exactly, from three very
different documents.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "fixtures"))

from requirements_data import SECTIONS, all_requirements  # noqa: E402

from rfp_assistant.parsers import (  # noqa: E402
    UnsupportedFormat,
    parse,
    parse_pdf_detailed,
    requirement_tabs,
)

FIXTURE = ROOT / "fixtures" / "rfp-alderwood-retail"
FORMATS = ["md", "xlsx", "pdf"]


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@pytest.fixture(scope="module")
def expected() -> dict[str, str]:
    return {r.rid: norm(r.text) for r in all_requirements()}


@pytest.fixture(scope="module", params=FORMATS)
def parsed(request) -> tuple[str, dict[str, object]]:
    fmt = request.param
    reqs = parse(f"{FIXTURE}.{fmt}")
    return fmt, {r.rid: r for r in reqs}


# --------------------------------------------------------------- core parity

def test_requirement_count(parsed, expected):
    fmt, got = parsed
    assert len(got) == len(expected), f"{fmt}: wrong requirement count"


def test_requirement_ids_match(parsed, expected):
    fmt, got = parsed
    assert set(got) == set(expected), f"{fmt}: requirement ids diverge from source"


def test_requirement_text_matches_exactly(parsed, expected):
    fmt, got = parsed
    mismatched = {rid for rid, text in expected.items() if norm(got[rid].text) != text}
    assert not mismatched, f"{fmt}: text differs for {sorted(mismatched)[:5]}"


def test_no_duplicate_ids(parsed):
    fmt, got = parsed
    reqs = parse(f"{FIXTURE}.{fmt}")
    assert len(reqs) == len(got), f"{fmt}: duplicate requirement ids emitted"


def test_all_formats_agree():
    texts = [
        {r.rid: norm(r.text) for r in parse(f"{FIXTURE}.{fmt}")} for fmt in FORMATS
    ]
    assert texts[0] == texts[1] == texts[2]


# ------------------------------------------------------------ over-extraction

BOILERPLATE = [
    "Proposals shall be submitted",
    "shall not be liable for any cost",
    "commercial general liability insurance",
    "The undersigned",
    "Late submissions shall not be considered",
    "must be renewed annually",
]


@pytest.mark.parametrize("phrase", BOILERPLATE)
def test_front_matter_is_not_extracted(phrase):
    """Obligation language outside the requirement body must not be picked up.

    This is the failure that scale makes invisible: 248 correct requirements
    plus 30 pieces of boilerplate still looks like a working parser.
    """
    for fmt in FORMATS:
        for req in parse(f"{FIXTURE}.{fmt}"):
            assert phrase.lower() not in req.text.lower(), (
                f"{fmt}: boilerplate leaked into {req.rid}"
            )


def test_pdf_page_furniture_is_stripped():
    """Regression: the footer merges into one line with the page number, so a
    pattern anchored on the date missed it and it was stitched onto whichever
    requirement ended the page."""
    for req in parse(f"{FIXTURE}.pdf"):
        assert "CONFIDENTIAL" not in req.text
        assert not re.search(r"\bPage\s+\d+\b", req.text)
        assert "Issued 1 July 2026" not in req.text


def test_pdf_toc_does_not_trigger_appendix_mode():
    """Regression: the table of contents contains "Appendix A. Terms and
    Conditions". Treating that as the start of the appendix put the parser into
    a mode that discarded every continuation line in the document, truncating
    106 requirements to their first line while still reporting 248 found."""
    got = {r.rid: r for r in parse(f"{FIXTURE}.pdf")}
    # A requirement whose text wraps across several lines, well after the TOC.
    long_req = got["4.2.5"]
    assert long_req.text.endswith("without vendor involvement.")
    assert len(long_req.text) > 120


def test_pdf_appendix_content_excluded():
    reqs = parse(f"{FIXTURE}.pdf")
    assert not any("indemnify" in r.text.lower() for r in reqs)


def test_pdf_recovers_priority_tags_that_wrap_onto_their_own_line():
    """Regression: furniture detection keyed on repetition alone.

    A "[Must]" tag that wraps onto a line by itself recurs on nearly every
    page, so a frequency-only rule classified it as a footer and stripped it,
    losing the priority on 21 requirements while leaving their text intact.
    Furniture is now required to sit at a page edge as well as repeat.
    """
    source = {r.rid: r.priority for r in all_requirements()}
    got = {r.rid: r.priority for r in parse(f"{FIXTURE}.pdf")}
    # The pdf renders a tag only for non-default priorities; Should is bare.
    for rid, priority in source.items():
        expected = None if priority == "Should" else priority
        assert got[rid] == expected, rid


# ------------------------------------------------------------------- xlsx

def test_xlsx_identifies_only_requirement_tabs():
    tabs = requirement_tabs(f"{FIXTURE}.xlsx")
    assert set(tabs) == {s.tab for s in SECTIONS}
    for excluded in ["Instructions", "Pricing Workbook", "Scoring Summary", "Exceptions Log"]:
        assert excluded not in tabs


def test_xlsx_skips_example_rows():
    reqs = parse(f"{FIXTURE}.xlsx")
    assert not any(r.rid.upper().startswith("EXAMPLE") for r in reqs)
    assert not any("do not submit a response" in r.text.lower() for r in reqs)


def test_xlsx_skips_subsection_banners():
    reqs = parse(f"{FIXTURE}.xlsx")
    banner_titles = {sub.title for s in SECTIONS for sub in s.subsections}
    assert not any(r.text in banner_titles for r in reqs)


def _vendor_profile_ids() -> set[str]:
    section = next(s for s in SECTIONS if s.tab == "Vendor Profile")
    return {r.rid for sub in section.subsections for r in sub.items}


def test_xlsx_captures_priority_and_weight():
    """Scored tabs carry Priority and Weight columns; the parser must read them."""
    got = {r.rid: r for r in parse(f"{FIXTURE}.xlsx")}
    source = {r.rid: r for r in all_requirements()}
    skip = _vendor_profile_ids()
    for rid, req in source.items():
        if rid in skip:
            continue
        assert got[rid].priority == req.priority, rid
        assert got[rid].weight == req.weight, rid


def test_xlsx_vendor_profile_has_no_priority_or_weight():
    """The Vendor Profile tab is narrative and has no Priority or Weight
    columns, so those fields must come back None rather than being invented.
    The source data carries values for them; the document does not."""
    got = {r.rid: r for r in parse(f"{FIXTURE}.xlsx")}
    for rid in _vendor_profile_ids():
        assert got[rid].priority is None, rid
        assert got[rid].weight is None, rid


# ---------------------------------------------------------------- metadata

def test_section_attribution(parsed):
    fmt, got = parsed
    source = {
        r.rid: s.number
        for s in SECTIONS
        for sub in s.subsections
        for r in sub.items
    }
    wrong = {rid for rid, sec in source.items() if got[rid].section != sec}
    assert not wrong, f"{fmt}: wrong section for {sorted(wrong)[:5]}"


def test_locators_are_populated(parsed):
    fmt, got = parsed
    assert all(r.locator for r in got.values()), f"{fmt}: missing source locators"


def test_pdf_coverage_is_reported():
    result = parse_pdf_detailed(f"{FIXTURE}.pdf")
    assert result.pages == 19
    # Front matter and appendices are legitimately not requirements, so full
    # coverage is not expected; a collapse toward zero would mean the numbering
    # scheme went unrecognised.
    assert 0.5 < result.coverage < 0.9


# ---------------------------------------------------------------- dispatch

def test_unsupported_format_raises():
    with pytest.raises(UnsupportedFormat):
        parse("something.docx")
