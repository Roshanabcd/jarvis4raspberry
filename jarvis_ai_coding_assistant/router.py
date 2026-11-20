"""FastAPI router for strictly additive integration into JARVIS OS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .analyzer import StaticCodeAnalyzer
from .config import CodingAssistantConfig
from .engine import CodingAssistantEngine
from .llm_provider import CodingLLMClient
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ApplyPatchRequest,
    ApplyPatchResponse,
    GenerateCodeRequest,
    GenerateCodeResponse,
    HealthResponse,
    HistoryRecord,
    HistoryResponse,
    RefactorRequest,
    RefactorResponse,
    TestSynthesisRequest,
    TestSynthesisResponse,
    WorkspaceFileContentResponse,
    WorkspaceFileEntry,
    WorkspaceFileListResponse,
)
from .storage import CodingAssistantStore
from .workspace import WorkspaceManager, WorkspaceSecurityError

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[CodingAssistantConfig] = None,
    prefix: str = "/api/coding-assistant",
    ui_route: str = "/coding-assistant",
) -> APIRouter:
    """Create a self-contained FastAPI APIRouter ready to mount inside JARVIS OS."""
    cfg = config or CodingAssistantConfig()
    workspace = WorkspaceManager(cfg)
    store = CodingAssistantStore(cfg.db_path)
    llm = CodingLLMClient(cfg)
    analyzer = StaticCodeAnalyzer()
    engine = CodingAssistantEngine(cfg, workspace, store, llm, analyzer)

    router = APIRouter(tags=["AI Coding Assistant"])

    @router.get(ui_route, response_class=HTMLResponse, include_in_schema=False)
    async def serve_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=404, detail="UI bundle not found.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get(f"{prefix}/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            provider=cfg.active_provider_label(),
            workspace_root=str(workspace.root),
            writes_enabled=cfg.allow_workspace_writes,
            history_records=store.count_sessions(),
        )

    @router.get(f"{prefix}/workspace/files", response_model=WorkspaceFileListResponse)
    async def list_workspace_files(subdir: Optional[str] = Query(default=None)) -> WorkspaceFileListResponse:
        try:
            raw_files = workspace.list_files(subdir=subdir)
        except WorkspaceSecurityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        entries = [WorkspaceFileEntry(**item) for item in raw_files]
        return WorkspaceFileListResponse(
            workspace_root=str(workspace.root),
            total_files=len(entries),
            files=entries,
        )

    @router.get(f"{prefix}/workspace/file", response_model=WorkspaceFileContentResponse)
    async def read_workspace_file(path: str = Query(..., min_length=1)) -> WorkspaceFileContentResponse:
        try:
            content, lang, size = workspace.read_file(path)
        except WorkspaceSecurityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return WorkspaceFileContentResponse(
            path=path,
            language=lang,
            size_bytes=size,
            line_count=len(content.splitlines()),
            content=content,
        )

    @router.post(f"{prefix}/generate", response_model=GenerateCodeResponse)
    async def generate_code(req: GenerateCodeRequest) -> GenerateCodeResponse:
        return await engine.generate_code(req)

    @router.post(f"{prefix}/refactor", response_model=RefactorResponse)
    async def refactor_code(req: RefactorRequest) -> RefactorResponse:
        try:
            return await engine.refactor_code(req)
        except WorkspaceSecurityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post(f"{prefix}/analyze", response_model=AnalyzeResponse)
    async def analyze_code(req: AnalyzeRequest) -> AnalyzeResponse:
        try:
            return engine.analyze_code(req)
        except WorkspaceSecurityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post(f"{prefix}/tests/synthesize", response_model=TestSynthesisResponse)
    async def synthesize_tests(req: TestSynthesisRequest) -> TestSynthesisResponse:
        try:
            return await engine.synthesize_tests(req)
        except WorkspaceSecurityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post(f"{prefix}/workspace/apply", response_model=ApplyPatchResponse)
    async def apply_workspace_patch(req: ApplyPatchRequest) -> ApplyPatchResponse:
        try:
            result = workspace.apply_patch(
                relative_path=req.file_path,
                new_content=req.new_content,
                dry_run=req.dry_run,
                create_backup=req.create_backup,
            )
        except WorkspaceSecurityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        store.record_workspace_audit(
            file_path=str(result["file_path"]),
            dry_run=bool(result["dry_run"]),
            bytes_written=int(result["bytes_written"]),
            backup_path=result["backup_path"],  # type: ignore[arg-type]
        )
        return ApplyPatchResponse(**result)  # type: ignore[arg-type]

    @router.get(f"{prefix}/history", response_model=HistoryResponse)
    async def get_history(limit: int = Query(default=30, ge=1, le=200)) -> HistoryResponse:
        rows = store.list_history(limit=limit)
        records = [HistoryRecord(**row) for row in rows]
        return HistoryResponse(total=len(records), records=records)

    return router
