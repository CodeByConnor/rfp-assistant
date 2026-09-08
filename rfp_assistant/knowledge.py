"""Load and chunk the product knowledge base.

Every chunk carries the access tag of the document it came from. Retrieval
filters on that tag *before* scoring, so an internal-only document is not
merely ranked low for a public-role query -- it is not in the candidate set at
all. Filtering after scoring would leave the pricing doc one bug away from
being quoted into a customer-facing response.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PUBLIC = "public"
INTERNAL = "internal-only"

DOC_TYPE_RE = re.compile(r"\*Doc type:\s*([a-z-]+)", re.I)
HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")

# Chunks below this many characters are merged into the next one; a heading
# with two lines under it retrieves poorly and pollutes the ranking.
MIN_CHUNK_CHARS = 200


@dataclass(frozen=True)
class Chunk:
    doc: str
    heading: str
    text: str
    access: str

    @property
    def citation(self) -> str:
        return self.doc

    @property
    def locator(self) -> str:
        return f"{self.doc}#{self.heading}" if self.heading else self.doc


def _access_of(text: str) -> str:
    """Read the access tag out of the document's front matter.

    Defaults to internal-only. An untagged document is treated as sensitive
    rather than public: the failure mode of wrongly withholding a document is
    a "Needs Input" a human resolves, while wrongly exposing one puts
    confidential material into a customer's hands.
    """
    m = DOC_TYPE_RE.search(text)
    if not m:
        return INTERNAL
    tag = m.group(1).strip().lower()
    return PUBLIC if tag == "public" else INTERNAL


def chunk_document(path: Path) -> list[Chunk]:
    text = path.read_text()
    access = _access_of(text)
    doc = path.name

    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in text.splitlines():
        if m := HEADING_RE.match(line):
            sections.append((m.group(2).strip(), []))
        else:
            sections[-1][1].append(line)

    chunks: list[Chunk] = []
    pending: list[tuple[str, str]] = []
    for heading, body in sections:
        body_text = "\n".join(body).strip()
        if not body_text:
            continue
        pending.append((heading, body_text))
        joined = "\n\n".join(f"{h}\n{b}" if h else b for h, b in pending)
        if len(joined) >= MIN_CHUNK_CHARS:
            chunks.append(
                Chunk(
                    doc=doc,
                    heading=pending[0][0],
                    text=joined,
                    access=access,
                )
            )
            pending = []

    if pending:
        joined = "\n\n".join(f"{h}\n{b}" if h else b for h, b in pending)
        if chunks:
            last = chunks[-1]
            chunks[-1] = Chunk(last.doc, last.heading, last.text + "\n\n" + joined, last.access)
        else:
            chunks.append(Chunk(doc, pending[0][0], joined, access))

    return chunks


def load_knowledge_base(directory: str | Path) -> list[Chunk]:
    directory = Path(directory)
    chunks: list[Chunk] = []
    for path in sorted(directory.glob("*.md")):
        chunks.extend(chunk_document(path))
    if not chunks:
        raise ValueError(f"no knowledge base documents found in {directory}")
    return chunks
