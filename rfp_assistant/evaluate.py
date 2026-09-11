"""Evaluation harness.

Retrieval evaluation costs nothing to run -- no model, no API key -- so it is
the first thing to measure and the thing to iterate against before spending
anything on classification.

The classification eval scores verdicts against the hand-labelled key. Its
headline number is deliberately not accuracy. For an RFP tool the errors are
not symmetric: answering `Partial` where the label says `Yes` costs a reviewer
a correction, while answering `Yes` where the label says `No` puts a
capability the product lacks into a document that becomes a contractual
commitment. So overstatements -- predicting something more favourable than the
truth -- are counted separately, and that is the number to drive to zero.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .classify import NEEDS_INPUT, classify_requirement
from .knowledge import INTERNAL, PUBLIC, load_knowledge_base
from .llm import LLMClient
from .parsers import parse
from .retrieval import BM25Retriever

ROLE_ALIASES = {"public": PUBLIC, "internal": INTERNAL}

# How favourable each verdict is to the vendor. Predicting a higher rank than
# the label is an overstatement.
OPTIMISM = {"Yes": 4, "Partial": 3, "Roadmap": 2, "No": 1, NEEDS_INPUT: 0}

VERDICT_ORDER = ["Yes", "Partial", "Roadmap", "No", NEEDS_INPUT]


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


@dataclass
class ClassificationScore:
    total: int = 0
    correct: int = 0
    wrong: list[tuple[str, str, str, str]] = field(default_factory=list)
    overstatements: list[tuple[str, str, str, str]] = field(default_factory=list)
    confusion: dict[str, Counter] = field(default_factory=dict)
    guardrail_total: int = 0
    guardrail_correct: int = 0
    leaks: list[str] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def overstatement_rate(self) -> float:
        return len(self.overstatements) / self.total if self.total else 0.0


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
            # undefined for them; they are scored by the guardrail instead.
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


def evaluate_classification(
    rfp_path: str | Path,
    kb_dir: str | Path,
    gold_path: str | Path,
    client: LLMClient,
    *,
    top_k: int = 6,
    limit: int | None = None,
) -> ClassificationScore:
    """Score predicted verdicts against the key, one entry per (id, role).

    Entries are labelled per role, so the pricing questions are scored twice:
    once as a `public` query that must not reach the internal document, and
    once as `internal` where it may.
    """
    requirements = {r.rid: r for r in parse(rfp_path)}
    chunks = load_knowledge_base(kb_dir)
    retriever = BM25Retriever(chunks)
    access = {c.doc: c.access for c in chunks}

    entries = load_gold(gold_path)
    if limit:
        entries = entries[:limit]

    score = ClassificationScore()
    for entry in entries:
        req = requirements.get(entry["id"])
        if req is None:
            continue
        role = ROLE_ALIASES.get(entry.get("role", "public"), PUBLIC)
        result, _usage = classify_requirement(
            req, retriever, client, role=role, top_k=top_k
        )
        expected, predicted = entry["verdict"], result.verdict

        score.total += 1
        score.confusion.setdefault(expected, Counter())[predicted] += 1
        if predicted == expected:
            score.correct += 1
        else:
            score.wrong.append((entry["id"], role, expected, predicted))
            if OPTIMISM.get(predicted, 0) > OPTIMISM.get(expected, 0):
                score.overstatements.append((entry["id"], role, expected, predicted))

        if expected == NEEDS_INPUT:
            score.guardrail_total += 1
            score.guardrail_correct += predicted == NEEDS_INPUT

        if role == PUBLIC and result.citation and access.get(result.citation) == INTERNAL:
            score.leaks.append(entry["id"])

    return score
