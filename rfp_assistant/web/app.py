"""Review app, in two modes.

**Local** (`serve`) keeps review runs on disk, so uploads and approvals survive
a restart. That is the real tool.

**Demo** (`serve --demo`, and the public deployment) keeps nothing. It serves a
precomputed run, the browser holds the review, and export takes the run back in
the request body. Three reasons it works that way:

- A serverless host has an ephemeral filesystem, so a run written by one
  request may not exist for the next.
- A public URL must never be able to spend anyone's API budget, so demo mode
  cannot reach a model at all.
- Replayed verdicts only mean anything for the bundled RFP. A stranger's RFP
  has no labels, so uploads in demo mode are **parse-only**: the parser runs on
  their real file and reports what it extracted, which needs no model and
  costs nothing.

The approval rules live in `review.update_row` in both modes. Demo mode calls
it through a stateless endpoint rather than reimplementing the rules in
JavaScript, because two copies of a rule become two different rules.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from ..classify import classify_all
from ..export import ExportError, export_markdown, export_xlsx
from ..knowledge import PUBLIC, load_knowledge_base
from ..llm import LLMClient
from ..parsers import UnsupportedFormat, parse
from ..retrieval import BM25Retriever
from ..review import (
    COMPLIANCE_LEVELS,
    NotFound,
    ReviewError,
    ReviewRow,
    Run,
    create_run,
    list_runs,
    load_run,
    save_run,
    source_path,
    update_row,
)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_ROWS = 2000
ALLOWED_SUFFIXES = {".md", ".xlsx", ".xlsm", ".pdf"}
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_RUN = ROOT / "fixtures" / "demo-run.json"


class RowUpdate(BaseModel):
    answer: str | None = None
    compliance_level: str | None = None
    status: str | None = None


class RowPatch(BaseModel):
    """A stateless edit: the row travels with the patch."""

    row: dict
    patch: RowUpdate


class RunPayload(BaseModel):
    rows: list[dict] = Field(default_factory=list)
    source_name: str = "rfp"
    role: str = PUBLIC


def _download_stem(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(name).stem).strip("-.")
    return stem or "rfp"


def _row_from(data: dict) -> ReviewRow:
    """Build a row from client-supplied JSON, ignoring anything unknown."""
    fields = ReviewRow.__dataclass_fields__
    try:
        return ReviewRow(**{k: v for k, v in data.items() if k in fields})
    except TypeError as exc:
        raise HTTPException(422, f"malformed row: {exc}") from None


def _run_from(payload: RunPayload, mode: str) -> Run:
    if not payload.rows:
        raise HTTPException(422, "no rows supplied")
    if len(payload.rows) > MAX_ROWS:
        raise HTTPException(413, f"at most {MAX_ROWS} rows")
    return Run(
        id="0" * 16,
        created_at="",
        source_name=payload.source_name,
        source_file="",
        source_format="xlsx",
        role=PUBLIC,  # demo export never runs with internal documents visible
        mode=mode,
        rows=[_row_from(r) for r in payload.rows],
    )


def create_app(
    *,
    kb_dir: str | Path | None = None,
    store_dir: str | Path | None = None,
    client_factory: Callable[[], LLMClient] | None = None,
    mode: str = "replay",
    model: str | None = None,
    live: bool = False,
    limit: int | None = None,
    role: str = PUBLIC,
    sample_path: str | Path | None = None,
    demo: bool = False,
    demo_run_path: str | Path = DEMO_RUN,
) -> FastAPI:
    index_html = (Path(__file__).parent / "static" / "index.html").read_text()
    sample = Path(sample_path) if sample_path else None
    demo_run_path = Path(demo_run_path)

    app = FastAPI(title="RFP Assistant", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return index_html

    @app.get("/api/config")
    def config() -> dict:
        return {
            "mode": mode,
            "model": model,
            "live": live and not demo,
            "limit": limit,
            "role": role if not demo else PUBLIC,
            "demo": demo,
            "sample": demo or sample is not None,
            "compliance_levels": COMPLIANCE_LEVELS,
        }

    # ----------------------------------------------------------------- demo

    if demo:

        @app.post("/api/sample", status_code=201)
        def demo_sample() -> dict:
            """Serve the precomputed run. No model, no index, no disk write."""
            if not demo_run_path.exists():
                raise HTTPException(
                    503,
                    "the demo run has not been generated; "
                    "run fixtures/build_demo_run.py",
                )
            data = json.loads(demo_run_path.read_text())
            rows = [ReviewRow(**row) for row in data.pop("rows")]
            return Run(**data, rows=rows).to_dict()

        @app.post("/api/runs", status_code=201)
        async def demo_upload(file: UploadFile = File(...)) -> dict:
            """Parse a visitor's own RFP. Extraction only: their document has no
            labels to replay and this deployment cannot reach a model."""
            data, name, suffix = await _read_upload(file)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"upload{suffix}"
                path.write_bytes(data)
                requirements = await run_in_threadpool(_parse_or_422, path)
            return {
                "parse_only": True,
                "source_name": name,
                "source_format": suffix.lstrip("."),
                "total": len(requirements),
                "sections": _section_summary(requirements),
                "requirements": [asdict(r) for r in requirements[:400]],
            }

        @app.post("/api/rows/apply")
        def demo_apply(payload: RowPatch) -> dict:
            """Apply one edit under the same rules the local app enforces."""
            row = _row_from(payload.row)
            run = Run(
                id="0" * 16, created_at="", source_name="", source_file="",
                source_format="", role=PUBLIC, mode=mode, rows=[row],
            )
            try:
                updated = update_row(
                    run, row.rid, **payload.patch.model_dump(exclude_none=True)
                )
            except NotFound as exc:
                raise HTTPException(404, str(exc)) from None
            except ReviewError as exc:
                raise HTTPException(400, str(exc)) from None
            return {"row": updated.to_dict()}

        @app.post("/api/export/workbook")
        def demo_export_workbook(payload: RunPayload) -> FileResponse:
            if sample is None or not sample.exists():
                raise HTTPException(503, "no source workbook is available")
            run = _run_from(payload, mode)
            out = Path(tempfile.mkdtemp()) / "export.xlsx"
            try:
                result = export_xlsx(run, sample, out)
            except ExportError as exc:
                raise HTTPException(400, str(exc)) from None
            return FileResponse(
                out,
                media_type=XLSX_MIME,
                filename=f"{_download_stem(run.source_name)}-response.xlsx",
                headers={
                    "X-Export-Written": str(result.written),
                    "X-Export-Pending": str(result.pending),
                    "X-Export-Citations-Withheld": str(result.citations_withheld),
                },
            )

        @app.post("/api/export/report")
        def demo_export_report(payload: RunPayload) -> Response:
            run = _run_from(payload, mode)
            return _markdown_response(run)

        return app

    # ---------------------------------------------------------------- local

    if store_dir is None or kb_dir is None or client_factory is None:
        raise ValueError("local mode needs store_dir, kb_dir and client_factory")

    store = Path(store_dir)
    store.mkdir(parents=True, exist_ok=True)
    retriever = BM25Retriever(load_knowledge_base(kb_dir))

    def load(run_id: str) -> Run:
        try:
            return load_run(store, run_id)
        except NotFound:
            raise HTTPException(404, "no such run") from None

    def process(path: Path, display_name: str) -> dict:
        requirements = _parse_or_422(path)
        capped = requirements[:limit] if limit else requirements
        results, _usage = classify_all(capped, retriever, client_factory(), role=role)
        run = create_run(
            store, path, display_name, capped, results, role=role, mode=mode
        )
        return run.to_dict()

    @app.get("/api/runs")
    def runs() -> list[dict]:
        return [run.summary() for run in list_runs(store)]

    @app.post("/api/runs", status_code=201)
    async def upload(file: UploadFile = File(...)) -> dict:
        data, name, suffix = await _read_upload(file)
        with tempfile.TemporaryDirectory() as tmp:
            # The user's filename is kept for display only and never becomes
            # part of a path.
            path = Path(tmp) / f"upload{suffix}"
            path.write_bytes(data)
            return await run_in_threadpool(process, path, name)

    @app.post("/api/sample", status_code=201)
    async def load_sample() -> dict:
        if sample is None or not sample.exists():
            raise HTTPException(404, "no sample RFP is configured")
        return await run_in_threadpool(process, sample, sample.name)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict:
        return load(run_id).to_dict()

    @app.patch("/api/runs/{run_id}/rows/{rid}")
    def patch_row(run_id: str, rid: str, update: RowUpdate) -> dict:
        run = load(run_id)
        try:
            row = update_row(run, rid, **update.model_dump(exclude_none=True))
        except NotFound as exc:
            raise HTTPException(404, str(exc)) from None
        except ReviewError as exc:
            raise HTTPException(400, str(exc)) from None
        save_run(store, run)
        return {"row": row.to_dict(), "counts": run.counts()}

    @app.get("/api/runs/{run_id}/export.xlsx")
    def export_workbook(run_id: str) -> FileResponse:
        run = load(run_id)
        out = source_path(store, run).with_name("export.xlsx")
        try:
            result = export_xlsx(run, source_path(store, run), out)
        except ExportError as exc:
            raise HTTPException(400, str(exc)) from None
        return FileResponse(
            out,
            media_type=XLSX_MIME,
            filename=f"{_download_stem(run.source_name)}-response.xlsx",
            headers={
                "X-Export-Written": str(result.written),
                "X-Export-Pending": str(result.pending),
                "X-Export-Citations-Withheld": str(result.citations_withheld),
            },
        )

    @app.get("/api/runs/{run_id}/report.md")
    def export_report(run_id: str) -> Response:
        return _markdown_response(load(run_id))

    return app


# ------------------------------------------------------------------ helpers


async def _read_upload(file: UploadFile) -> tuple[bytes, str, str]:
    name = Path(file.filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(415, f"upload a {', '.join(sorted(ALLOWED_SUFFIXES))} file")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "files are limited to 20 MB")
    if not data:
        raise HTTPException(400, "the file is empty")
    return data, name, suffix


def _parse_or_422(path: Path):
    try:
        requirements = parse(path)
    except UnsupportedFormat as exc:
        raise HTTPException(415, str(exc)) from None
    except Exception:
        raise HTTPException(422, "the file could not be read as an RFP") from None
    if not requirements:
        raise HTTPException(422, "no numbered requirements were found in this file")
    return requirements


def _section_summary(requirements) -> list[dict]:
    seen: dict[str, dict] = {}
    for req in requirements:
        entry = seen.setdefault(
            req.section, {"section": req.section, "title": req.section_title, "count": 0}
        )
        entry["count"] += 1
    return sorted(seen.values(), key=lambda s: (len(s["section"]), s["section"]))


def _markdown_response(run: Run) -> Response:
    return Response(
        export_markdown(run),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{_download_stem(run.source_name)}-gap-report.md"'
            )
        },
    )
