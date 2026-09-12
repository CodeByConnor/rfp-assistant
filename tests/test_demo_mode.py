"""Demo-mode tests.

Demo mode is what a public URL serves, so the properties worth testing are not
only "does it work" but "can a visitor make this cost money or keep state".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "fixtures"))

from rfp_assistant.web import app as web  # noqa: E402

XLSX = ROOT / "fixtures" / "rfp-alderwood-retail.xlsx"
MD = ROOT / "fixtures" / "rfp-alderwood-retail.md"
DEMO_RUN = ROOT / "fixtures" / "demo-run.json"


@pytest.fixture(scope="module")
def client():
    app = web.create_app(
        demo=True, mode="replay", sample_path=XLSX, demo_run_path=DEMO_RUN
    )
    return TestClient(app)


@pytest.fixture(scope="module")
def run(client):
    return client.post("/api/sample").json()


# ------------------------------------------------------- cannot cost anything

def test_demo_needs_no_model_client_at_all():
    """Local mode refuses to start without a client factory. Demo mode must not
    need one: that is what makes a public URL unable to spend an API budget."""
    app = web.create_app(demo=True, sample_path=XLSX, demo_run_path=DEMO_RUN)
    assert app is not None
    with pytest.raises(ValueError):
        web.create_app(demo=False, sample_path=XLSX)


def test_config_reports_demo_and_never_live(client):
    config = client.get("/api/config").json()
    assert config["demo"] is True
    assert config["live"] is False


def test_stateful_endpoints_are_not_registered(client):
    paths = {getattr(r, "path", "") for r in client.app.routes}
    assert "/api/runs/{run_id}" not in paths
    assert "/api/runs/{run_id}/rows/{rid}" not in paths
    assert client.get("/api/runs/0123456789abcdef").status_code in (404, 405)


def test_sample_is_served_from_the_precomputed_file(client, run):
    """No retrieval index, no knowledge base, no model: the run is read from
    disk, which is why a cold start is fast and free."""
    assert run["counts"]["total"] == 248
    assert run["mode"] == "replay"
    stored = json.loads(DEMO_RUN.read_text())
    assert [r["rid"] for r in run["rows"]] == [r["rid"] for r in stored["rows"]]


def test_precomputed_run_matches_the_current_pipeline(run):
    """If the guardrail or fixtures change, the committed demo run goes stale.
    This fails until fixtures/build_demo_run.py is re-run."""
    from rfp_assistant.classify import classify_all
    from rfp_assistant.knowledge import PUBLIC, load_knowledge_base
    from rfp_assistant.llm import ReplayClient
    from rfp_assistant.parsers import parse
    from rfp_assistant.retrieval import BM25Retriever

    requirements = parse(XLSX)
    retriever = BM25Retriever(load_knowledge_base(ROOT / "docs" / "knowledge-base"))
    results, _ = classify_all(
        requirements, retriever, ReplayClient(ROOT / "fixtures" / "gold-answers.json"),
        role=PUBLIC,
    )
    fresh = {r.rid: r.verdict for r in results}
    served = {r["rid"]: r["verdict"] for r in run["rows"]}
    assert served == fresh, "demo-run.json is stale; re-run fixtures/build_demo_run.py"


# ------------------------------------------------------------- upload is parse-only

@pytest.mark.parametrize("source", [XLSX, MD])
def test_upload_parses_but_does_not_classify(client, source):
    result = client.post(
        "/api/runs", files={"file": (source.name, source.read_bytes())}
    ).json()
    assert result["parse_only"] is True
    assert result["total"] == 248
    assert "verdict" not in json.dumps(result["requirements"][:3])
    assert sum(s["count"] for s in result["sections"]) == 248


def test_bad_upload_is_still_rejected(client):
    assert client.post(
        "/api/runs", files={"file": ("x.exe", b"MZ")}
    ).status_code == 415


# --------------------------------------------------------------- stateless review

def _first(run, test):
    return next(r for r in run["rows"] if test(r))


def test_approval_rules_are_enforced_server_side(client, run):
    """The rules stay in review.update_row rather than being reimplemented in
    JavaScript, so demo mode cannot drift from the real tool."""
    row = _first(run, lambda r: r["verdict"] == "Partial" and not r["narrative"])

    res = client.post("/api/rows/apply", json={"row": row, "patch": {"status": "approved"}})
    assert res.status_code == 400
    assert "compliance level" in res.json()["detail"]

    res = client.post(
        "/api/rows/apply",
        json={"row": row, "patch": {"compliance_level": "Configuration", "status": "approved"}},
    )
    assert res.status_code == 200
    assert res.json()["row"]["status"] == "approved"


def test_needs_input_still_requires_a_written_answer(client, run):
    row = _first(run, lambda r: r["verdict"] == "Needs Input" and not r["narrative"])
    res = client.post(
        "/api/rows/apply",
        json={"row": row, "patch": {"compliance_level": "Not Supported", "status": "approved"}},
    )
    assert res.status_code == 400
    assert "written answer" in res.json()["detail"]


def test_apply_ignores_unknown_fields_from_the_client(client, run):
    row = dict(run["rows"][0], is_blocking=True, injected="ignored")
    res = client.post("/api/rows/apply", json={"row": row, "patch": {}})
    assert res.status_code == 200
    assert "injected" not in res.json()["row"]


def test_malformed_row_is_rejected(client):
    res = client.post("/api/rows/apply", json={"row": {"rid": "1.1.1"}, "patch": {}})
    assert res.status_code == 422


# --------------------------------------------------------------------- export

def test_export_takes_the_run_in_the_request_body(client, run):
    rows = [dict(r) for r in run["rows"]]
    approved = next(r for r in rows if r["verdict"] == "Yes" and not r["narrative"])
    approved["status"] = "approved"

    res = client.post(
        "/api/export/workbook", json={"rows": rows, "source_name": "demo.xlsx"}
    )
    assert res.status_code == 200
    assert res.headers["x-export-written"] == "1"
    assert res.headers["content-disposition"].endswith('demo-response.xlsx"')

    res = client.post("/api/export/report", json={"rows": rows, "source_name": "demo.xlsx"})
    assert res.status_code == 200
    assert res.text.startswith("# Gap Report")


def test_export_refuses_an_oversized_payload(client, run):
    rows = run["rows"] * 10
    res = client.post("/api/export/workbook", json={"rows": rows})
    assert res.status_code == 413


def test_export_refuses_an_empty_payload(client):
    assert client.post("/api/export/workbook", json={"rows": []}).status_code == 422
