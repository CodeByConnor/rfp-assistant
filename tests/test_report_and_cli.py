"""Gap report and CLI tests, including the spending safeguards.

The safeguard tests matter as much as the logic tests: a tool that can bill a
user's account should not be able to do so by accident, and "it defaults to
offline" is a claim worth holding to a test.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "fixtures"))

from rfp_assistant import cli  # noqa: E402
from rfp_assistant.classify import NEEDS_INPUT, Classification  # noqa: E402
from rfp_assistant.models import Requirement  # noqa: E402
from rfp_assistant.report import build_gaps, render_markdown, summarise  # noqa: E402

RFP = ROOT / "fixtures" / "rfp-alderwood-retail.xlsx"


def _req(rid, priority="Must", weight=5, text="A requirement."):
    return Requirement(
        rid=rid, text=text, priority=priority, weight=weight,
        section="4", section_title="Security", source_format="test", locator="-",
    )


def _cls(rid, verdict, **kw):
    return Classification(
        rid=rid, verdict=verdict, answer=kw.get("answer", "answer"),
        citation=kw.get("citation", "security-whitepaper.md"),
        supporting_quote="q", overridden_from=kw.get("overridden_from"),
        override_reason=kw.get("override_reason"),
    )


# ---------------------------------------------------------------- gap report

def test_yes_verdicts_are_not_gaps():
    reqs = {"1.1.1": _req("1.1.1")}
    assert build_gaps(reqs, [_cls("1.1.1", "Yes")]) == []


def test_blocking_requires_both_a_hard_no_and_a_must():
    reqs = {"1.1.1": _req("1.1.1", priority="Must"), "1.1.2": _req("1.1.2", priority="Nice")}
    gaps = build_gaps(reqs, [_cls("1.1.1", "No"), _cls("1.1.2", "No")])
    blocking = [g for g in gaps if g.is_blocking]
    assert [g.requirement.rid for g in blocking] == ["1.1.1"]


def test_gaps_sort_most_alarming_first():
    reqs = {
        "1.1.1": _req("1.1.1", priority="Nice", weight=1),
        "1.1.2": _req("1.1.2", priority="Must", weight=5),
        "1.1.3": _req("1.1.3", priority="Should", weight=3),
    }
    gaps = build_gaps(
        reqs,
        [_cls("1.1.1", "No"), _cls("1.1.2", "No"), _cls("1.1.3", "Partial")],
    )
    assert [g.requirement.rid for g in gaps] == ["1.1.2", "1.1.1", "1.1.3"]


def test_report_surfaces_blocking_and_escalations():
    reqs = {"1.1.1": _req("1.1.1"), "1.1.2": _req("1.1.2")}
    results = [
        _cls("1.1.1", "No"),
        _cls("1.1.2", NEEDS_INPUT, overridden_from="Yes",
             override_reason="cited evidence requires escalation"),
    ]
    md = render_markdown(reqs, results)
    assert "## Blocking (1)" in md
    assert "## Escalated by the guardrail (1)" in md
    assert "cited evidence requires escalation" in md
    assert "1.1.1" in md and "1.1.2" in md


def test_summarise_counts_verdicts():
    results = [_cls("a", "Yes"), _cls("b", "Yes"), _cls("c", "No")]
    assert summarise(results) == {"Yes": 2, "No": 1}


# --------------------------------------------------------- spending safety

def test_respond_defaults_to_offline_and_makes_no_network_call(monkeypatch, capsys):
    """The default path must not be able to bill anything. If it ever tries to
    construct the real client, this fails loudly."""
    def explode(*a, **kw):
        raise AssertionError("AnthropicClient constructed during a default run")

    monkeypatch.setattr(cli, "AnthropicClient", explode)
    assert cli.main(["respond", str(RFP), "--limit", "5"]) == 0
    assert "offline stub" in capsys.readouterr().out


def test_live_run_aborts_without_confirmation(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    monkeypatch.setattr(
        cli, "AnthropicClient",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("client built after abort")),
    )
    assert cli.main(["respond", str(RFP), "--live", "--limit", "3"]) == 1
    out = capsys.readouterr().out
    assert "nothing was sent, nothing was charged" in out


def test_live_run_shows_a_cost_estimate_before_asking(monkeypatch, capsys):
    """The estimate has to be on screen before the user is asked, or the
    confirmation is not informed consent."""
    asked: list[str] = []

    def fake_input(prompt=""):
        asked.append(capsys.readouterr().out)
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    assert cli.main(
        ["respond", str(RFP), "--live", "--limit", "10", "--model", "claude-haiku-4-5"]
    ) == 1
    assert asked, "the user was never prompted"
    shown_before_prompt = asked[0]
    assert "estimated cost" in shown_before_prompt
    assert "claude-haiku-4-5" in shown_before_prompt
    assert "10" in shown_before_prompt


def test_empty_answer_at_the_prompt_is_treated_as_no(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_: "")
    monkeypatch.setattr(
        cli, "AnthropicClient",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("built despite empty reply")),
    )
    assert cli.main(["respond", str(RFP), "--live", "--limit", "2"]) == 1


def test_limit_caps_how_many_requirements_are_processed(capsys):
    cli.main(["respond", str(RFP), "--limit", "7"])
    assert "7 requirements" in capsys.readouterr().out


def test_eval_retrieval_runs_offline(capsys):
    assert cli.main(["eval-retrieval"]) == 0
    assert "recall" in capsys.readouterr().out


def test_parse_command_reports_counts(capsys):
    assert cli.main(["parse", str(RFP)]) == 0
    assert "248 requirements" in capsys.readouterr().out


def test_missing_file_is_an_error(capsys):
    assert cli.main(["parse", "does-not-exist.xlsx"]) == 2


@pytest.mark.parametrize("model", ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"])
def test_every_selectable_model_has_a_price(model):
    from rfp_assistant.llm import PRICING

    assert model in PRICING
