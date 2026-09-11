"""Review state for one RFP response run.

A run is the unit a solutions engineer works through: one uploaded RFP, one
classification pass, and a row per requirement that moves from pending to
approved as a person signs it off.

Two approval rules carry the design:

- A scored row cannot be approved without a compliance level. `Partial` and
  `Needs Input` rows arrive with none, because the model could not settle one,
  so they cannot be approved -- and cannot be exported to the customer --
  until a person picks it.
- A `Needs Input` row cannot be approved with the guardrail's placeholder text.
  Someone has to write the answer.
"""

from __future__ import annotations

import json
import re
import secrets
import shutil
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .classify import NEEDS_INPUT, Classification
from .knowledge import INTERNAL
from .models import Requirement
from .workbook import narrative_tabs

COMPLIANCE_LEVELS = [
    "Standard",
    "Configuration",
    "Customization",
    "Third-Party",
    "Roadmap",
    "Not Supported",
]

# Only verdicts that map unambiguously are pre-filled. `Partial` could be
# Configuration, Customization, or Third-Party, and that choice changes how the
# buyer scores the answer -- it is a human call.
VERDICT_TO_COMPLIANCE = {
    "Yes": "Standard",
    "Roadmap": "Roadmap",
    "No": "Not Supported",
}

PENDING = "pending"
APPROVED = "approved"

RUN_ID_RE = re.compile(r"^[0-9a-f]{16}$")
MAX_ANSWER_CHARS = 4000


class ReviewError(ValueError):
    pass


class NotFound(ReviewError):
    pass


@dataclass
class ReviewRow:
    rid: str
    text: str
    section: str
    section_title: str
    priority: str | None
    weight: int | None
    locator: str
    verdict: str
    answer: str
    citation: str
    citation_access: str
    supporting_quote: str
    overridden_from: str | None
    override_reason: str | None
    compliance_level: str | None
    narrative: bool = False
    status: str = PENDING
    edited: bool = False

    @property
    def is_blocking(self) -> bool:
        return self.verdict == "No" and self.priority == "Must"

    def to_dict(self) -> dict:
        return {**asdict(self), "is_blocking": self.is_blocking}


@dataclass
class Run:
    id: str
    created_at: str
    source_name: str
    source_file: str
    source_format: str
    role: str
    mode: str
    rows: list[ReviewRow] = field(default_factory=list)

    def row(self, rid: str) -> ReviewRow:
        for row in self.rows:
            if row.rid == rid:
                return row
        raise NotFound(f"no requirement {rid} in this run")

    def counts(self) -> dict:
        return {
            "total": len(self.rows),
            "verdicts": dict(Counter(r.verdict for r in self.rows)),
            "approved": sum(r.status == APPROVED for r in self.rows),
            "pending": sum(r.status == PENDING for r in self.rows),
            "blocking": sum(r.is_blocking for r in self.rows),
            "escalated": sum(r.overridden_from is not None for r in self.rows),
        }

    def summary(self) -> dict:
        counts = self.counts()
        return {
            "id": self.id,
            "created_at": self.created_at,
            "source_name": self.source_name,
            "mode": self.mode,
            "role": self.role,
            "total": counts["total"],
            "approved": counts["approved"],
        }

    def to_dict(self) -> dict:
        data = {k: v for k, v in asdict(self).items() if k != "rows"}
        data["counts"] = self.counts()
        data["rows"] = [r.to_dict() for r in self.rows]
        return data


def _run_dir(store: str | Path, run_id: str) -> Path:
    # Run ids reach this function from URLs. Anything but the exact generated
    # shape is rejected before it can become part of a filesystem path.
    if not RUN_ID_RE.match(run_id or ""):
        raise NotFound("no such run")
    return Path(store) / run_id


def _rows(
    requirements: list[Requirement],
    classifications: list[Classification],
    narrative: set[str],
) -> list[ReviewRow]:
    by_id = {r.rid: r for r in requirements}
    rows = []
    for c in classifications:
        req = by_id[c.rid]
        if c.citation:
            # Unknown provenance fails closed: it is treated as internal, so
            # export will never write it into the customer's workbook.
            access = next(
                (chunk.access for chunk in c.evidence if chunk.doc == c.citation),
                INTERNAL,
            )
        else:
            access = ""
        is_narrative = req.locator.split("!", 1)[0] in narrative
        rows.append(
            ReviewRow(
                rid=req.rid,
                text=req.text,
                section=req.section,
                section_title=req.section_title,
                priority=req.priority,
                weight=req.weight,
                locator=req.locator,
                verdict=c.verdict,
                answer=c.answer,
                citation=c.citation,
                citation_access=access,
                supporting_quote=c.supporting_quote,
                overridden_from=c.overridden_from,
                override_reason=c.override_reason,
                compliance_level=None if is_narrative else VERDICT_TO_COMPLIANCE.get(c.verdict),
                narrative=is_narrative,
            )
        )
    return rows


def create_run(
    store: str | Path,
    source_path: str | Path,
    source_name: str,
    requirements: list[Requirement],
    classifications: list[Classification],
    *,
    role: str,
    mode: str,
) -> Run:
    run_id = secrets.token_hex(8)
    directory = Path(store) / run_id
    directory.mkdir(parents=True)

    suffix = Path(source_path).suffix.lower()
    source_file = f"source{suffix}"
    shutil.copyfile(source_path, directory / source_file)

    narrative = narrative_tabs(source_path) if suffix in {".xlsx", ".xlsm"} else set()

    run = Run(
        id=run_id,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source_name=source_name,
        source_file=source_file,
        source_format=suffix.lstrip("."),
        role=role,
        mode=mode,
        rows=_rows(requirements, classifications, narrative),
    )
    save_run(store, run)
    return run


def save_run(store: str | Path, run: Run) -> None:
    path = _run_dir(store, run.id) / "run.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(run), indent=2))
    tmp.replace(path)


def load_run(store: str | Path, run_id: str) -> Run:
    path = _run_dir(store, run_id) / "run.json"
    if not path.exists():
        raise NotFound("no such run")
    data = json.loads(path.read_text())
    rows = [ReviewRow(**row) for row in data.pop("rows")]
    return Run(**data, rows=rows)


def list_runs(store: str | Path) -> list[Run]:
    store = Path(store)
    if not store.exists():
        return []
    runs = []
    for directory in store.iterdir():
        if directory.is_dir() and RUN_ID_RE.match(directory.name):
            try:
                runs.append(load_run(store, directory.name))
            except (NotFound, json.JSONDecodeError, TypeError):
                continue
    runs.sort(key=lambda r: r.created_at, reverse=True)
    return runs


def source_path(store: str | Path, run: Run) -> Path:
    return _run_dir(store, run.id) / run.source_file


def update_row(
    run: Run,
    rid: str,
    *,
    answer: str | None = None,
    compliance_level: str | None = None,
    status: str | None = None,
) -> ReviewRow:
    """Apply a reviewer's edit. Content changes are applied before status, so a
    single request can edit and approve together."""
    row = run.row(rid)
    changed = False

    if answer is not None:
        answer = answer.strip()
        if not answer:
            raise ReviewError("the answer must not be empty")
        if len(answer) > MAX_ANSWER_CHARS:
            raise ReviewError(f"the answer is limited to {MAX_ANSWER_CHARS} characters")
        if answer != row.answer:
            row.answer = answer
            row.edited = True
            changed = True

    if compliance_level is not None:
        level = compliance_level or None
        if level is not None and level not in COMPLIANCE_LEVELS:
            raise ReviewError(f"unknown compliance level: {compliance_level}")
        if level is not None and row.narrative:
            raise ReviewError("this is a narrative question and takes no compliance level")
        if level != row.compliance_level:
            row.compliance_level = level
            changed = True

    # Changing an approved answer puts it back in the queue; the approval was
    # for the old text.
    if changed and row.status == APPROVED:
        row.status = PENDING

    if status is not None:
        if status not in (PENDING, APPROVED):
            raise ReviewError(f"unknown status: {status}")
        if status == APPROVED:
            if not row.narrative and not row.compliance_level:
                raise ReviewError("choose a compliance level before approving")
            if row.verdict == NEEDS_INPUT and not row.edited:
                raise ReviewError(
                    "this requirement needs a written answer before it can be approved"
                )
        row.status = status

    return row
