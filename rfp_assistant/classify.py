"""Classify each requirement against retrieved evidence, with the guardrail.

The guardrail is the reason this project exists. Its current shape is the
third design, and each change was forced by a measurement against the gold key
rather than by intuition (see README, "What the measurements changed").

1. A retrieval-score threshold does not work. Answerable and unanswerable
   requirements score in overlapping ranges, because relevance and
   answerability are different properties: the sustainability requirement
   retrieves a highly relevant chunk that says no company position exists.
2. Scanning the whole cited chunk for escalation language catches the right
   cases but over-fires. Chunks bundle neighbouring material, so the
   Washington health-data bullet that says "route to Legal" held the clean
   CCPA, GDPR, and model-training answers sharing its section -- 6 false holds
   among labelled answerable requirements.
3. Checking only the passage holding the model's quote fixes that, but is
   evadable: a model could quote a harmless sentence from the same chunk and
   step around the escalation beside it.

So escalation is checked in two places, and either one holds the answer:

- the passage containing the model's own quote, and
- the passage, across all supplied evidence, that best matches the
  requirement -- which depends on nothing the model chose.

Against the gold key this keeps every catch the whole-chunk rule made while
cutting false holds from 6 to 1. Before either check runs, the model must name
one supplied document and quote it verbatim, and a quote not found there
discards the verdict.

What this cannot catch, stated plainly: a model that answers confidently and
quotes a real but irrelevant sentence, where the evidence contains no
escalation language at all. The public-role pricing questions are the example:
no public document mentions pricing, so there is nothing lexical to trigger
on. That case rests on the model's own judgment, which is what the live eval
measures. `tests/test_pipeline.py` pins it as a known gap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .knowledge import PUBLIC, Chunk
from .llm import LLMClient, Usage
from .models import Requirement
from .retrieval import BM25Retriever, split_passages

NEEDS_INPUT = "Needs Input"

# Phrases a knowledge base uses to say "a person must handle this". Kept
# directive: an earlier bare "route to" also matched "no direct public route to
# the data tier" and held every network-security answer.
ESCALATION_RE = re.compile(
    r"no approved company position"
    r"|not previously answered"
    r"|not recorded here"
    r"|do not answer from precedent"
    r"|do not draft a position"
    r"|do not quote"
    r"|route\b[^.\n]{0,40}\bto legal"
    r"|before responding"
    r"|does not represent compliance",
    re.I,
)

SYSTEM_PROMPT = """\
You are assisting a solutions engineer in responding to an enterprise RFP.

For each requirement you are given evidence drawn from the vendor's own
documentation. Decide how the vendor's product measures against the
requirement and draft a short response.

Verdicts:
- Yes       the product fully meets the requirement today
- Partial   it meets the requirement only in part, or with a caveat such as a
            tier restriction, a beta status, or a scope limit
- No        it does not meet the requirement and there is no commitment to
- Roadmap   it does not meet it today, but the evidence shows a committed,
            dated plan to. A capability described as merely requested,
            evaluated, or considered is NOT Roadmap -- it is No.
- Needs Input  the evidence does not settle the question, or it indicates a
            human must answer

Rules you must follow:
- Cite exactly one source document, named exactly as it appears in the evidence.
- Quote one sentence from that document verbatim, character for character. Do
  not paraphrase, reformat, or repair the quote.
- If no provided evidence supports an answer, return the verdict "Needs Input"
  with an empty citation and an empty quote. Never infer an answer from
  adjacent or loosely related material.
- Prefer Partial over Yes when a limitation exists. An RFP answer becomes a
  contractual commitment, and overstating a capability is far more damaging
  than understating one.
"""


@dataclass
class Classification:
    rid: str
    verdict: str
    answer: str
    citation: str
    supporting_quote: str
    evidence: list[Chunk] = field(default_factory=list)
    overridden_from: str | None = None
    override_reason: str | None = None

    @property
    def was_overridden(self) -> bool:
        return self.overridden_from is not None


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _passage_containing(quote: str, text: str) -> str:
    target = _normalise(quote)
    for passage in split_passages(text):
        if target in _normalise(passage):
            return passage
    # A quote spanning passage boundaries falls back to the whole chunk, which
    # errs toward holding the answer rather than letting it through.
    return text


def build_user_prompt(requirement: Requirement, evidence: list[Chunk]) -> str:
    lines = [
        f"Requirement {requirement.rid}"
        + (f" [{requirement.priority}]" if requirement.priority else ""),
        requirement.text,
        "",
        "Evidence:",
    ]
    for i, chunk in enumerate(evidence, start=1):
        lines.append(f"[evidence {i}] {chunk.doc} | {chunk.heading}")
        lines.append(chunk.text)
        lines.append("")
    return "\n".join(lines)


def classify_requirement(
    requirement: Requirement,
    retriever: BM25Retriever,
    client: LLMClient,
    *,
    role: str = PUBLIC,
    top_k: int = 6,
) -> tuple[Classification, Usage]:
    hits = retriever.search(requirement.text, role=role, top_k=top_k)

    if not hits:
        # Nothing retrieved at all: there is no evidence to send, so no call.
        return (
            Classification(
                rid=requirement.rid,
                verdict=NEEDS_INPUT,
                answer="No supporting documentation was found for this requirement.",
                citation="",
                supporting_quote="",
                evidence=[],
                overridden_from=None,
                override_reason="no evidence retrieved",
            ),
            Usage(),
        )

    evidence = [h.chunk for h in hits]
    response = client.complete(SYSTEM_PROMPT, build_user_prompt(requirement, evidence))
    data = response.data

    verdict = data.get("verdict", NEEDS_INPUT)
    citation = (data.get("citation") or "").strip()
    quote = (data.get("supporting_quote") or "").strip()
    answer = (data.get("answer") or "").strip()

    result = Classification(
        rid=requirement.rid,
        verdict=verdict,
        answer=answer,
        citation=citation,
        supporting_quote=quote,
        evidence=evidence,
    )

    def override(reason: str, message: str) -> None:
        result.overridden_from = result.verdict
        result.override_reason = reason
        result.verdict = NEEDS_INPUT
        result.answer = message

    if verdict == NEEDS_INPUT:
        return result, response.usage

    cited = next((c for c in evidence if c.doc == citation), None)
    if cited is None:
        override(
            "citation not in evidence",
            "The cited source was not among the documents supplied, so the answer is unverified.",
        )
        return result, response.usage

    if not quote or _normalise(quote) not in _normalise(cited.text):
        override(
            "quote not found in cited document",
            "The supporting quote could not be located in the cited document, so the answer is unverified.",
        )
        return result, response.usage

    if ESCALATION_RE.search(_passage_containing(quote, cited.text)):
        override(
            "cited evidence requires escalation",
            "The passage this answer relies on says the question must be routed to a person before answering.",
        )
        return result, response.usage

    if ESCALATION_RE.search(retriever.best_passage(requirement.text, evidence)):
        override(
            "relevant evidence requires escalation",
            "The documentation that addresses this requirement says it must be routed to a person before answering.",
        )
        return result, response.usage

    return result, response.usage


def classify_all(
    requirements: list[Requirement],
    retriever: BM25Retriever,
    client: LLMClient,
    *,
    role: str = PUBLIC,
    top_k: int = 6,
) -> tuple[list[Classification], Usage]:
    results: list[Classification] = []
    total = Usage()
    for requirement in requirements:
        result, usage = classify_requirement(
            requirement, retriever, client, role=role, top_k=top_k
        )
        results.append(result)
        total.add(usage)
    return results, total
