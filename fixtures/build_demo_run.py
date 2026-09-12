"""Precompute the review run that the public demo serves.

The deployed demo has to cost nothing to run and start fast, so the verdicts
are computed once here and committed as JSON. At request time the server reads
a file: it builds no retrieval index, loads no knowledge base, and calls no
model.

The verdicts come from the hand-labelled answer key by way of `ReplayClient`,
not from a model -- the demo says so in a banner on every page. Everything
downstream is the real pipeline: retrieval chose the evidence, and the
guardrail verified every citation and held what it holds.

Regenerate after changing the fixtures, knowledge base, or guardrail:

    .venv/bin/python fixtures/build_demo_run.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rfp_assistant.classify import classify_all  # noqa: E402
from rfp_assistant.knowledge import PUBLIC, load_knowledge_base  # noqa: E402
from rfp_assistant.llm import ReplayClient  # noqa: E402
from rfp_assistant.parsers import parse  # noqa: E402
from rfp_assistant.retrieval import BM25Retriever  # noqa: E402
from rfp_assistant.review import create_run  # noqa: E402

SOURCE = ROOT / "fixtures" / "rfp-alderwood-retail.xlsx"
GOLD = ROOT / "fixtures" / "gold-answers.json"
KB = ROOT / "docs" / "knowledge-base"
OUT = ROOT / "fixtures" / "demo-run.json"

# Fixed so regenerating produces a clean diff rather than a new id every time.
DEMO_RUN_ID = "0" * 16


def main() -> None:
    requirements = parse(SOURCE)
    retriever = BM25Retriever(load_knowledge_base(KB))
    results, _usage = classify_all(
        requirements, retriever, ReplayClient(GOLD), role=PUBLIC
    )

    with tempfile.TemporaryDirectory() as tmp:
        run = create_run(
            tmp, SOURCE, SOURCE.name, requirements, results,
            role=PUBLIC, mode="replay",
        )

    data = asdict(run)
    data["id"] = DEMO_RUN_ID
    data["created_at"] = ""  # the demo has no meaningful timestamp
    OUT.write_text(json.dumps(data, indent=2) + "\n")

    counts = run.counts()
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {counts['total']} rows, verdicts {counts['verdicts']}")
    print(f"  blocking {counts['blocking']}, held by guardrail {counts['escalated']}")
    print(f"  {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
