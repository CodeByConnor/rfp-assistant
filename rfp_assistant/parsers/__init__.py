"""Format dispatch for RFP requirement extraction."""

from __future__ import annotations

from pathlib import Path

from ..models import Requirement
from .markdown_parser import parse_markdown
from .pdf_parser import PdfParseResult, parse_pdf, parse_pdf_detailed
from .xlsx_parser import parse_xlsx, requirement_tabs

_DISPATCH = {
    ".md": parse_markdown,
    ".markdown": parse_markdown,
    ".xlsx": parse_xlsx,
    ".xlsm": parse_xlsx,
    ".pdf": parse_pdf,
}


class UnsupportedFormat(ValueError):
    pass


def parse(path: str | Path) -> list[Requirement]:
    """Extract requirements from an RFP in any supported format."""
    suffix = Path(path).suffix.lower()
    try:
        parser = _DISPATCH[suffix]
    except KeyError:
        raise UnsupportedFormat(
            f"no parser for '{suffix}'; supported: {sorted(_DISPATCH)}"
        ) from None
    return parser(path)


__all__ = [
    "parse",
    "parse_markdown",
    "parse_pdf",
    "parse_pdf_detailed",
    "parse_xlsx",
    "requirement_tabs",
    "PdfParseResult",
    "UnsupportedFormat",
]
