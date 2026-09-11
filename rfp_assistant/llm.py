"""LLM client boundary.

Two implementations behind one protocol. `StubClient` makes no network call and
costs nothing, so every code path around the model -- prompt assembly, response
parsing, citation verification, the guardrail, the gap report -- is testable
without an API key. `AnthropicClient` is the real one and is the only place in
this project that can spend money.

Nothing constructs `AnthropicClient` implicitly. The CLI defaults to the stub
and requires an explicit flag to use the real client, so an accidental run
cannot bill anything.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Protocol

from .retrieval import split_passages, tokenize

DEFAULT_MODEL = "claude-opus-5"

# Rough pre-flight estimate. Deliberately not `count_tokens`, which is an API
# call and would require a key just to find out what a run would cost.
CHARS_PER_TOKEN = 3.7

# USD per million tokens.
PRICING = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["Yes", "Partial", "No", "Roadmap", "Needs Input"],
        },
        "citation": {
            "type": "string",
            "description": "Filename of the single source document that best supports the verdict, exactly as labelled in the evidence. Empty string if no provided evidence supports an answer.",
        },
        "supporting_quote": {
            "type": "string",
            "description": "A verbatim sentence copied from that document supporting the verdict. Must appear in the evidence character for character. Empty string if none does.",
        },
        "answer": {
            "type": "string",
            "description": "Draft response to the requirement, 1-3 sentences, stating the capability plainly including any limitation.",
        },
    },
    "required": ["verdict", "citation", "supporting_quote", "answer"],
    "additionalProperties": False,
}


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.calls += other.calls

    def cost(self, model: str) -> float:
        rate_in, rate_out = PRICING.get(model, PRICING[DEFAULT_MODEL])
        return (self.input_tokens / 1e6) * rate_in + (self.output_tokens / 1e6) * rate_out


@dataclass
class LLMResponse:
    data: dict
    usage: Usage = field(default_factory=Usage)


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, user: str) -> LLMResponse: ...


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / CHARS_PER_TOKEN))


EVIDENCE_RE = re.compile(r"^\[evidence \d+\] ([^\s|]+)[^\n]*\n", re.M)


def _evidence_blocks(user: str) -> list[tuple[str, str]]:
    """Split a classification prompt into (document, text) evidence blocks."""
    matches = list(EVIDENCE_RE.finditer(user))
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(user)
        blocks.append((m.group(1), user[m.end():end]))
    return blocks


def _requirement_id(user: str) -> str:
    m = re.match(r"Requirement (\S+)", user)
    return m.group(1) if m else ""


def _requirement_text(user: str) -> str:
    lines = user.splitlines()
    return lines[1] if len(lines) > 1 else ""


def _plain(text: str) -> str:
    """Strip markdown emphasis and list/table markers so a passage reads as prose."""
    text = re.sub(r"\*\*|__|`", "", text)
    text = re.sub(r"^\s*[-*|]\s*", "", text)
    text = text.replace(" | ", "; ").strip(" |")
    return re.sub(r"\s+", " ", text).strip()


def _first_substantive_passage(text: str) -> str:
    """The whole passage around the first line with real content.

    Quoting the full passage rather than a single wrapped line keeps sentences
    intact, and it leaves the guardrail's view unchanged: the guardrail checks
    the passage containing the quote, which is this same passage.
    """
    for passage in split_passages(text):
        for line in passage.splitlines():
            if len(line.strip("- *#|").strip()) > 40:
                return re.sub(r"\s+", " ", passage).strip()
    return ""


class StubClient:
    """Deterministic offline client. Never makes a network call.

    It answers from the evidence it is given using a crude lexical rule. That
    is enough to exercise every downstream path -- including the failure paths,
    since `fabricate_quote` makes it return a quote that is not in the evidence
    so citation verification can be tested.
    """

    def __init__(self, *, verdict: str = "Yes", fabricate_quote: bool = False) -> None:
        self.model = "stub"
        self.verdict = verdict
        self.fabricate_quote = fabricate_quote
        self.calls: list[tuple[str, str]] = []

    def _pick(self, blocks: list[tuple[str, str]], user: str) -> int:
        """Which evidence block to cite. The plain stub always cites the first."""
        return 0

    def _quote(self, text: str, user: str) -> str:
        """What to quote from the chosen block. The plain stub quotes the first
        substantive passage, relevant or not -- the careless-model case."""
        return _first_substantive_passage(text)

    def complete(self, system: str, user: str) -> LLMResponse:
        self.calls.append((system, user))

        citation = quote = ""
        blocks = _evidence_blocks(user)
        if blocks:
            citation, text = blocks[self._pick(blocks, user)]
            if self.fabricate_quote:
                quote = "This sentence does not appear anywhere in the evidence."
            else:
                quote = self._quote(text, user)

        return LLMResponse(
            data={
                "verdict": self.verdict,
                "citation": citation,
                "supporting_quote": quote,
                "answer": f"[stub answer] {self.verdict}.",
            },
            usage=Usage(
                input_tokens=estimate_tokens(system + user),
                output_tokens=60,
                calls=1,
            ),
        )


class AnthropicClient:
    """Real client. The only thing here that costs money."""

    def __init__(self, model: str = DEFAULT_MODEL, *, api_key: str | None = None) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "the 'anthropic' package is required for live runs: pip install anthropic"
            ) from exc

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "no credentials found. Set ANTHROPIC_API_KEY, or run without "
                "--live to use the offline stub."
            )
        self.model = model
        self._client = anthropic.Anthropic(api_key=key)

    def complete(self, system: str, user: str) -> LLMResponse:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": RESPONSE_SCHEMA,
                }
            },
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        return LLMResponse(
            data=json.loads(text),
            usage=Usage(
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                calls=1,
            ),
        )


class ReplayClient(StubClient):
    """Offline demo client that replays hand-labelled verdicts.

    Exists so the review workflow can be shown without an API key. The verdicts
    come from the gold answer key, not from a model, and the UI says so in a
    banner on every page. Where the key names the document an answer should
    cite and retrieval surfaced it, that document is cited; otherwise the first
    evidence block is. Everything downstream -- including the guardrail's
    citation and escalation checks -- runs over these responses exactly as it
    would over a real model's, so a replayed "Yes" can still be held.
    """

    def __init__(self, gold_path, *, default: str = "Yes") -> None:
        super().__init__(verdict=default)
        self.model = "replay"
        self._default = default
        with open(gold_path) as fh:
            gold = json.load(fh)["requirements"]
        public = [g for g in gold if g.get("role", "public") == "public"]
        self.verdicts = {g["id"]: g["verdict"] for g in public}
        self.citations = {g["id"]: g.get("citations") or [] for g in public}

    def _pick(self, blocks: list[tuple[str, str]], user: str) -> int:
        wanted = self.citations.get(_requirement_id(user), [])
        return next((i for i, (doc, _) in enumerate(blocks) if doc in wanted), 0)

    def _quote(self, text: str, user: str) -> str:
        """Quote the passage in the block that best matches the requirement,
        as a careful model would, instead of whatever comes first."""
        wanted = set(tokenize(_requirement_text(user)))
        best, best_score = "", 0
        for passage in split_passages(text):
            # A table header row or a document's front matter shares vocabulary
            # with the question ("Uptime SLA", "Uptime commitment") but answers
            # nothing, so neither is quoted.
            if len(_plain(passage)) <= 40 or "|---" in passage or "Doc type:" in passage:
                continue
            score = len(wanted & set(tokenize(passage)))
            if score > best_score:
                best, best_score = passage, score
        return re.sub(r"\s+", " ", best).strip() if best else _first_substantive_passage(text)

    def complete(self, system: str, user: str) -> LLMResponse:
        self.verdict = self.verdicts.get(_requirement_id(user), self._default)
        response = super().complete(system, user)
        data = response.data
        if data["verdict"] == "Needs Input":
            data.update(
                citation="",
                supporting_quote="",
                answer="The documentation does not settle this requirement. It needs an answer from the account team.",
            )
        else:
            data["answer"] = _plain(data["supporting_quote"]) or data["answer"]
        return response


def estimate_run_cost(
    requirements: int, model: str, *, top_k: int = 6, avg_requirement_chars: int = 180
) -> float:
    """Pre-flight cost estimate for `requirements` classifications."""
    tokens_in = requirements * (
        int(avg_requirement_chars / CHARS_PER_TOKEN) + top_k * 220 + 260
    )
    tokens_out = requirements * 160
    rate_in, rate_out = PRICING.get(model, PRICING[DEFAULT_MODEL])
    return (tokens_in / 1e6) * rate_in + (tokens_out / 1e6) * rate_out
