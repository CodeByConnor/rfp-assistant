"""Gap report.

A flat list of 248 answers is not useful to a solutions engineer. What matters
is which answers threaten the deal, and those need to sort to the top rather
than be found by scrolling. A `No` against a requirement the buyer marked
mandatory is a different object from a `No` against a nice-to-have, and burying
the first among 247 others is how it reaches the customer unnoticed.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .classify import NEEDS_INPUT, Classification
from .models import Requirement

# Higher is more alarming.
VERDICT_RISK = {"No": 3, NEEDS_INPUT: 2, "Roadmap": 2, "Partial": 1, "Yes": 0}
PRIORITY_RISK = {"Must": 3, "Should": 1, "Nice": 0, None: 1}


@dataclass
class Gap:
    requirement: Requirement
    classification: Classification

    @property
    def risk(self) -> int:
        return (
            VERDICT_RISK.get(self.classification.verdict, 0) * 10
            + PRIORITY_RISK.get(self.requirement.priority, 1) * 3
            + (self.requirement.weight or 0)
        )

    @property
    def is_blocking(self) -> bool:
        """A hard No against a requirement the buyer called mandatory."""
        return (
            self.classification.verdict == "No"
            and self.requirement.priority == "Must"
        )


def build_gaps(
    requirements: dict[str, Requirement], results: list[Classification]
) -> list[Gap]:
    gaps = [
        Gap(requirement=requirements[r.rid], classification=r)
        for r in results
        if r.verdict != "Yes" and r.rid in requirements
    ]
    gaps.sort(key=lambda g: (-g.risk, g.requirement.rid))
    return gaps


def summarise(results: list[Classification]) -> dict[str, int]:
    return dict(Counter(r.verdict for r in results))


def render_markdown(
    requirements: dict[str, Requirement],
    results: list[Classification],
    *,
    title: str = "RFP Response — Gap Report",
) -> str:
    gaps = build_gaps(requirements, results)
    counts = summarise(results)
    blocking = [g for g in gaps if g.is_blocking]
    overridden = [r for r in results if r.was_overridden]

    lines = [f"# {title}", ""]
    lines.append(f"{len(results)} requirements answered.")
    lines.append("")

    lines.append("| Verdict | Count |")
    lines.append("|---|---|")
    for verdict in ("Yes", "Partial", "Roadmap", "No", NEEDS_INPUT):
        if verdict in counts:
            lines.append(f"| {verdict} | {counts[verdict]} |")
    lines.append("")

    if blocking:
        lines.append(f"## Blocking ({len(blocking)})")
        lines.append("")
        lines.append(
            "Mandatory requirements the product does not meet. These decide "
            "whether the deal is winnable and should be reviewed first."
        )
        lines.append("")
        for gap in blocking:
            req = gap.requirement
            lines.append(f"- **{req.rid}** ({req.section_title}) — {req.text}")
            lines.append(f"  - {gap.classification.answer}")
            if gap.classification.citation:
                lines.append(f"  - Source: `{gap.classification.citation}`")
        lines.append("")

    if overridden:
        lines.append(f"## Escalated by the guardrail ({len(overridden)})")
        lines.append("")
        lines.append(
            "The model produced a verdict that could not be verified against "
            "its own cited evidence, so it was replaced with Needs Input. "
            "Each of these needs a human answer."
        )
        lines.append("")
        reasons = Counter(r.override_reason for r in overridden)
        for reason, count in reasons.most_common():
            lines.append(f"- {reason}: {count}")
        lines.append("")
        for result in overridden[:25]:
            req = requirements.get(result.rid)
            if req is None:
                continue
            lines.append(
                f"- **{result.rid}** — claimed *{result.overridden_from}*, "
                f"held for review ({result.override_reason})"
            )
        lines.append("")

    other = [g for g in gaps if not g.is_blocking]
    if other:
        lines.append(f"## Remaining gaps ({len(other)})")
        lines.append("")
        lines.append("| Req | Priority | Verdict | Source | Summary |")
        lines.append("|---|---|---|---|---|")
        for gap in other[:60]:
            req = gap.requirement
            cls = gap.classification
            summary = cls.answer.replace("|", "\\|")[:110]
            lines.append(
                f"| {req.rid} | {req.priority or '—'} | {cls.verdict} | "
                f"`{cls.citation or '—'}` | {summary} |"
            )
        if len(other) > 60:
            lines.append("")
            lines.append(f"_{len(other) - 60} further gaps omitted._")
        lines.append("")

    return "\n".join(lines)
