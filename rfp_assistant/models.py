"""Core types shared across parsing, retrieval, and classification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    """One discrete requirement lifted out of an RFP document.

    `locator` records where in the source document this came from, so a
    reviewer can jump back to it and so a disagreement between two parsers
    can be traced rather than guessed at. Its format is parser-specific:
    "Security!A23" for xlsx, "p12" for pdf, "line 412" for markdown.
    """

    rid: str
    text: str
    section: str = ""
    section_title: str = ""
    subsection: str = ""
    subsection_title: str = ""
    priority: str | None = None
    weight: int | None = None
    source_format: str = ""
    locator: str = ""

    def __post_init__(self) -> None:
        if not self.rid:
            raise ValueError("requirement id must not be empty")
        if not self.text.strip():
            raise ValueError(f"requirement {self.rid} has empty text")
