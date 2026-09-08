"""Retrieval, guardrail, and classification tests.

Every test here runs offline against the stub client. No API key, no cost.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "fixtures"))

from rfp_assistant.classify import (  # noqa: E402
    NEEDS_INPUT,
    build_user_prompt,
    classify_all,
    classify_requirement,
)
from rfp_assistant.evaluate import evaluate_retrieval  # noqa: E402
from rfp_assistant.knowledge import (  # noqa: E402
    INTERNAL,
    PUBLIC,
    load_knowledge_base,
)
from rfp_assistant.llm import StubClient  # noqa: E402
from rfp_assistant.parsers import parse  # noqa: E402
from rfp_assistant.retrieval import BM25Retriever  # noqa: E402

KB = ROOT / "docs" / "knowledge-base"
RFP = ROOT / "fixtures" / "rfp-alderwood-retail.xlsx"
GOLD = ROOT / "fixtures" / "gold-answers.json"


@pytest.fixture(scope="module")
def chunks():
    return load_knowledge_base(KB)


@pytest.fixture(scope="module")
def retriever(chunks):
    return BM25Retriever(chunks)


@pytest.fixture(scope="module")
def requirements():
    return {r.rid: r for r in parse(RFP)}


# ------------------------------------------------------------- knowledge base

def test_access_tags_are_read_from_front_matter(chunks):
    pricing = [c for c in chunks if c.doc == "pricing-packaging.md"]
    assert pricing and all(c.access == INTERNAL for c in pricing)
    security = [c for c in chunks if c.doc == "security-whitepaper.md"]
    assert security and all(c.access == PUBLIC for c in security)


def test_untagged_document_defaults_to_internal(tmp_path):
    """Failing closed matters: wrongly withholding a document costs a human
    review, wrongly exposing one puts confidential material in a customer's
    hands."""
    doc = tmp_path / "untagged.md"
    doc.write_text("# Untitled\n\n" + "Some content about pricing. " * 20)
    from rfp_assistant.knowledge import chunk_document

    assert all(c.access == INTERNAL for c in chunk_document(doc))


# ------------------------------------------------------------------ retrieval

def test_public_role_never_retrieves_internal_documents(retriever, requirements):
    """The RBAC property, checked across every requirement rather than the
    handful the gold key labels."""
    for req in requirements.values():
        docs = retriever.documents_for(req.text, role=PUBLIC, top_k=8)
        assert "pricing-packaging.md" not in docs, req.rid


def test_internal_role_can_reach_pricing(retriever, requirements):
    for rid in ("8.1.1", "8.1.2", "6.2.2"):
        docs = retriever.documents_for(requirements[rid].text, role=INTERNAL, top_k=6)
        assert "pricing-packaging.md" in docs, rid


def test_retrieval_recall_against_gold():
    score = evaluate_retrieval(RFP, KB, GOLD, top_k=6)
    assert score.total > 100
    assert score.recall >= 0.95, f"recall regressed to {score.recall:.1%}"


def test_empty_query_returns_nothing(retriever):
    assert retriever.search("the and of", role=PUBLIC) == []


# ------------------------------------------------------------------ guardrail

def test_fabricated_quote_is_rejected(retriever, requirements):
    """The model claiming support it cannot produce is the failure this whole
    project exists to prevent."""
    client = StubClient(verdict="Yes", fabricate_quote=True)
    for rid in ("4.2.1", "2.1.1", "7.1.1", "3.2.2"):
        result, _ = classify_requirement(requirements[rid], retriever, client)
        assert result.verdict == NEEDS_INPUT, rid
        assert result.override_reason == "quote not found in cited document"
        assert result.overridden_from == "Yes"


def test_citation_outside_evidence_is_rejected(retriever, requirements):
    class BadCitation(StubClient):
        def complete(self, system, user):
            response = super().complete(system, user)
            response.data["citation"] = "a-document-that-was-never-supplied.md"
            return response

    result, _ = classify_requirement(requirements["2.1.1"], retriever, BadCitation())
    assert result.verdict == NEEDS_INPUT
    assert result.override_reason == "citation not in evidence"


def test_escalation_marker_in_cited_chunk_overrides_a_confident_verdict(
    retriever, requirements
):
    """8.3.1 and 5.1.3 are the cases a similarity threshold cannot catch: the
    retrieved evidence is highly relevant and explicitly says a human must
    answer."""
    client = StubClient(verdict="Yes")
    for rid in ("8.3.1", "5.1.3"):
        result, _ = classify_requirement(requirements[rid], retriever, client)
        assert result.verdict == NEEDS_INPUT, rid
        assert result.override_reason == "cited evidence requires escalation"
        assert result.overridden_from == "Yes"


def test_no_evidence_means_no_model_call(retriever):
    from rfp_assistant.models import Requirement

    client = StubClient()
    empty = Requirement(rid="9.9.9", text="the and of it", source_format="test", locator="-")
    result, usage = classify_requirement(empty, retriever, client)
    assert result.verdict == NEEDS_INPUT
    assert result.override_reason == "no evidence retrieved"
    assert client.calls == [], "the model must not be called when there is nothing to send"
    assert usage.calls == 0


def test_model_needs_input_is_passed_through_unchanged(retriever, requirements):
    client = StubClient(verdict=NEEDS_INPUT)
    result, _ = classify_requirement(requirements["2.1.1"], retriever, client)
    assert result.verdict == NEEDS_INPUT
    assert not result.was_overridden


# ----------------------------------------------------------------- prompting

def test_prompt_contains_requirement_and_labelled_evidence(retriever, requirements):
    req = requirements["4.2.1"]
    evidence = [h.chunk for h in retriever.search(req.text, role=PUBLIC, top_k=4)]
    prompt = build_user_prompt(req, evidence)
    assert req.text in prompt
    assert "[evidence 1]" in prompt
    for chunk in evidence:
        assert chunk.doc in prompt


# The figures that actually live only in the internal pricing document. A
# public-role prompt containing any of these is a real leak. The *filename*
# is not on this list on purpose: a public document legitimately points at
# the internal one ("rates are commercially sensitive - see
# pricing-packaging.md"), which discloses nothing and doubles as an
# escalation signal.
INTERNAL_FIGURES = ["$0.005", "$285", "$240", "$195", "$2,500", "$7,500", "$14,000", "$45,000"]


def test_prompt_never_contains_internal_figures_for_public_role(
    retriever, requirements
):
    for rid in ("8.1.1", "8.1.2", "8.1.4", "8.1.5", "6.2.2"):
        req = requirements[rid]
        evidence = [h.chunk for h in retriever.search(req.text, role=PUBLIC, top_k=8)]
        prompt = build_user_prompt(req, evidence)
        for figure in INTERNAL_FIGURES:
            assert figure not in prompt, f"{rid} leaked {figure}"


def test_no_internal_chunk_reaches_a_public_prompt(retriever, requirements):
    """The structural invariant behind the figure check above: provenance, not
    string matching. No chunk sourced from an internal document may appear in
    a public-role prompt, whatever it happens to contain."""
    for req in requirements.values():
        evidence = [h.chunk for h in retriever.search(req.text, role=PUBLIC, top_k=8)]
        assert all(c.access == PUBLIC for c in evidence), req.rid


# ------------------------------------------------------------------ full run

def test_full_offline_run_costs_nothing_and_covers_every_requirement(
    retriever, requirements
):
    client = StubClient(verdict="Yes")
    results, usage = classify_all(list(requirements.values()), retriever, client)
    assert len(results) == 248
    assert {r.rid for r in results} == set(requirements)
    assert usage.calls == len([r for r in results if r.evidence])
    # An always-optimistic model still gets overridden wherever the cited
    # evidence says a human must answer.
    assert any(r.was_overridden for r in results)


def test_usage_cost_scales_with_model():
    from rfp_assistant.llm import Usage

    usage = Usage(input_tokens=1_000_000, output_tokens=100_000, calls=1)
    assert usage.cost("claude-opus-5") == pytest.approx(5.0 + 2.5)
    assert usage.cost("claude-haiku-4-5") == pytest.approx(1.0 + 0.5)
    assert usage.cost("claude-haiku-4-5") < usage.cost("claude-opus-5")


def test_gold_key_ids_all_exist_in_the_fixture(requirements):
    gold = json.loads(GOLD.read_text())["requirements"]
    assert {g["id"] for g in gold} <= set(requirements)
