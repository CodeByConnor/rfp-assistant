"""Classification eval tests. Offline, no API key.

The eval exists to make a live run worth paying for: it reports accuracy, but
its headline is the overstatement count, because for an RFP the two error
directions are not equally bad.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "fixtures"))

from rfp_assistant import cli  # noqa: E402
from rfp_assistant.classify import NEEDS_INPUT  # noqa: E402
from rfp_assistant.evaluate import evaluate_classification  # noqa: E402
from rfp_assistant.knowledge import INTERNAL, PUBLIC  # noqa: E402
from rfp_assistant.llm import ReplayClient, StubClient  # noqa: E402

KB = ROOT / "docs" / "knowledge-base"
RFP = ROOT / "fixtures" / "rfp-alderwood-retail.xlsx"
GOLD = ROOT / "fixtures" / "gold-answers.json"


@pytest.fixture(scope="module")
def replay_score():
    return evaluate_classification(RFP, KB, GOLD, ReplayClient(GOLD))


def test_replay_reproduces_the_key_except_the_known_false_hold(replay_score):
    """Replay returns the labelled verdict, so anything wrong here is the
    guardrail changing an answer. Exactly one public-role answer is changed:
    5.1.1, the lexical tie between the CCPA and Washington bullets."""
    public_wrong = [w for w in replay_score.wrong if w[1] == PUBLIC]
    assert [w[0] for w in public_wrong] == ["5.1.1"]
    assert public_wrong[0][3] == NEEDS_INPUT, "the guardrail may only move an answer toward caution"


def test_replay_never_overstates_on_public_answers(replay_score):
    """The guardrail can only move an answer toward caution, so no public-role
    prediction may be more favourable than its label. Internal-role entries are
    exempt: the replay client only carries public labels and falls back to
    'Yes' for them, which is a limitation of the stand-in, not of the pipeline."""
    assert all(role == INTERNAL for _rid, role, _e, _p in replay_score.overstatements)


def test_every_unanswerable_item_is_held(replay_score):
    assert replay_score.guardrail_total == 11
    assert replay_score.guardrail_correct == replay_score.guardrail_total


def test_no_internal_citation_reaches_a_public_answer(replay_score):
    assert replay_score.leaks == []


def test_an_optimistic_model_is_caught_as_overstatement():
    """A model that answers Yes to everything scores badly on the metric that
    matters, not just on accuracy."""
    score = evaluate_classification(RFP, KB, GOLD, StubClient(verdict="Yes"))
    assert len(score.overstatements) >= 10
    assert score.overstatement_rate > 0.05
    assert score.accuracy < 0.9
    assert score.guardrail_correct < score.guardrail_total


def test_limit_caps_the_number_of_items_scored():
    score = evaluate_classification(RFP, KB, GOLD, ReplayClient(GOLD), limit=12)
    assert score.total <= 12


def test_confusion_matrix_is_keyed_by_expected_verdict(replay_score):
    assert set(replay_score.confusion) <= {"Yes", "Partial", "Roadmap", "No", NEEDS_INPUT}
    assert sum(sum(row.values()) for row in replay_score.confusion.values()) == replay_score.total


# ----------------------------------------------------------------------- cli

def test_eval_classify_runs_offline_and_reports(capsys):
    assert cli.main(["eval-classify", "--limit", "20"]) == 0
    out = capsys.readouterr().out
    assert "accuracy" in out and "overstatements" in out
    assert "guardrail changes, not how well a model classifies" in out


def test_eval_classify_live_aborts_without_confirmation(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    monkeypatch.setattr(
        cli, "AnthropicClient",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("client built after abort")),
    )
    assert cli.main(["eval-classify", "--live", "--limit", "5"]) == 1
    assert "nothing was sent, nothing was charged" in capsys.readouterr().out


def test_eval_classify_live_shows_cost_before_asking(monkeypatch, capsys):
    seen: list[str] = []

    def fake_input(prompt=""):
        seen.append(capsys.readouterr().out)
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    assert cli.main(
        ["eval-classify", "--live", "--limit", "30", "--model", "claude-haiku-4-5"]
    ) == 1
    assert "estimated cost" in seen[0]
    assert "claude-haiku-4-5" in seen[0]
