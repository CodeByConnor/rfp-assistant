"""Classify each requirement against retrieved evidence, with the guardrail.

The guardrail is the reason this project exists, and its design is the result
of two measurements rather than intuition -- both run before any money was
spent (see README, "What the measurements changed").

The obvious design is a retrieval-score threshold: if nothing scores highly,
answer `Needs Input`. Measured against the gold key, that does not work. The
score distributions of answerable and unanswerable requirements overlap almost
entirely, because *relevance and answerability are different properties*. The
knowledge base discusses sustainability at length -- it says there is no
company position on it -- so the sustainability requirement retrieves a highly
relevant chunk that contains no answer. It scored above 75% of the
requirements that genuinely could be answered.

Scanning all retrieved chunks for escalation language does not work either: at
six chunks per query it fired on 42 of 113 answerable requirements, because a
marker anywhere in the candidate set says nothing about the chunk that
actually supports the answer.

So the guardrail runs *after* the model commits to its evidence:

1. The model must name one source document and quote it verbatim.
2. The quote is verified to actually appear in that document. A quote that
   does not is fabricated evidence, and the verdict is discarded.
3. Escalation markers are checked only in the *cited* chunk. If the evidence
   the model chose to rely on says "route to Legal", the answer is an
   escalation regardless of the verdict the model produced.

Only the degenerate case -- retrieval returned nothing at all -- is handled
before the call, because there is nothing to send.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .knowledge import PUBLIC, Chunk
from .llm import LLMClient, Usage
from .models import Requirement
from .retrieval import BM25Retriever

NEEDS_INPUT = "Needs Input"

# Phrases a knowledge base uses to say "a human must handle this". Checked only
# against the chunk the model cited.
ESCALATION_RE = re.compile(
    r"no approved company position"
    r"|not previously answered"
    r"|not recorded here"
    r"|do not answer from precedent"
    r"|do not draft a position"
    r"|route (?:to|any|all)"
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

    if ESCALATION_RE.search(cited.text):
        override(
            "cited evidence requires escalation",
            "The supporting documentation states that this question must be routed to a human before answering.",
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
