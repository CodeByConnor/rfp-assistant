"""Evaluation harness.

Retrieval evaluation costs nothing to run -- no model, no API key -- so it is
the first thing to measure and the thing to iterate against before spending
anything on classification.

The question it answers: for a requirement whose answer we know lives in
`security-whitepaper.md`, does retrieval actually surface that document? If it
does not, no amount of prompting downstream will save the answer, because the
evidence never reaches the model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .knowledge import INTERNAL, PUBLIC, load_knowledge_base
from .parsers import parse
from .retrieval import BM25Retriever

ROLE_ALIASES = {"public": PUBLIC, "internal": INTERNAL}


@dataclass
class RetrievalScore:
    total: int
    hit_at_k: int
    exact_sets: int
    misses: list[tuple[str, list[str], list[str]]]

    @property
    def recall(self) -> float:
        return self.hit_at_k / self.total if self.total else 0.0

    @property
    def exact_rate(self) -> float:
        return self.exact_sets / self.total if self.total else 0.0


def load_gold(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text())
    return data["requirements"]


def evaluate_retrieval(
    rfp_path: str | Path,
    kb_dir: str | Path,
    gold_path: str | Path,
    *,
    top_k: int = 4,
) -> RetrievalScore:
    requirements = {r.rid: r for r in parse(rfp_path)}
    retriever = BM25Retriever(load_knowledge_base(kb_dir))
    gold = load_gold(gold_path)

    total = hits = exact = 0
    misses: list[tuple[str, list[str], list[str]]] = []

    for entry in gold:
        expected = entry.get("citations") or []
        if not expected:
            # "Needs Input" cases have no expected citation. Retrieval recall is
            # undefined for them; they are scored by the guardrail test instead.
            continue
        req = requirements.get(entry["id"])
        if req is None:
            continue

        role = ROLE_ALIASES.get(entry.get("role", "public"), PUBLIC)
        got = retriever.documents_for(req.text, role=role, top_k=top_k)

        total += 1
        if set(expected) & set(got):
            hits += 1
        if set(expected) <= set(got):
            exact += 1
        else:
            misses.append((entry["id"], expected, got))

    return RetrievalScore(total=total, hit_at_k=hits, exact_sets=exact, misses=misses)
