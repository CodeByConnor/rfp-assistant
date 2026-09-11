"""Local review app: upload an RFP, review each answer, export the workbook.

The browser has no way to switch the server into live mode. Whether uploads
call a real model is decided when the server starts (`serve --live`), which
prints the cost and asks first, so a click in the page can never be the thing
that starts billing.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel
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
    create_run,
    list_runs,
    load_run,
    save_run,
    source_path,
    update_row,
)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_SUFFIXES = {".md", ".xlsx", ".xlsm", ".pdf"}
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class RowUpdate(BaseModel):
    answer: str | None = None
    compliance_level: str | None = None
    status: str | None = None


def _download_stem(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(name).stem).strip("-.")
    return stem or "rfp"


def create_app(
    *,
    store_dir: str | Path,
    kb_dir: str | Path,
    client_factory: Callable[[], LLMClient],
    mode: str,
    model: str | None = None,
    live: bool = False,
    limit: int | None = None,
    role: str = PUBLIC,
    sample_path: str | Path | None = None,
) -> FastAPI:
    store = Path(store_dir)
    store.mkdir(parents=True, exist_ok=True)
    retriever = BM25Retriever(load_knowledge_base(kb_dir))
    index_html = (Path(__file__).parent / "static" / "index.html").read_text()
    sample = Path(sample_path) if sample_path else None

    app = FastAPI(title="RFP Assistant", docs_url=None, redoc_url=None, openapi_url=None)

    def load(run_id: str):
        try:
            return load_run(store, run_id)
        except NotFound:
            raise HTTPException(404, "no such run") from None

    def process(path: Path, display_name: str) -> dict:
        try:
            requirements = parse(path)
        except UnsupportedFormat as exc:
            raise HTTPException(415, str(exc)) from None
        except Exception:
            raise HTTPException(422, "the file could not be read as an RFP") from None
        if not requirements:
            raise HTTPException(422, "no numbered requirements were found in this file")
        if limit:
            requirements = requirements[:limit]
        results, _usage = classify_all(requirements, retriever, client_factory(), role=role)
        run = create_run(
            store, path, display_name, requirements, results, role=role, mode=mode
        )
        return run.to_dict()

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return index_html

    @app.get("/api/config")
    def config() -> dict:
        return {
            "mode": mode,
            "model": model,
            "live": live,
            "limit": limit,
            "role": role,
            "sample": sample is not None,
            "compliance_levels": COMPLIANCE_LEVELS,
        }

    @app.get("/api/runs")
    def runs() -> list[dict]:
        return [run.summary() for run in list_runs(store)]

    @app.post("/api/runs", status_code=201)
    async def upload(file: UploadFile = File(...)) -> dict:
        name = Path(file.filename or "").name
        suffix = Path(name).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(415, f"upload a {', '.join(sorted(ALLOWED_SUFFIXES))} file")
        data = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "files are limited to 20 MB")
        if not data:
            raise HTTPException(400, "the file is empty")
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
        run = load(run_id)
        return Response(
            export_markdown(run),
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{_download_stem(run.source_name)}-gap-report.md"'
                )
            },
        )

    return app
