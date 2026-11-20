"""FastAPI APIRouter for JARVIS Document Question Answering."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from .config import DocumentQAConfig
from .models import (
    AskRequest,
    AskResponse,
    DeleteDocumentResponse,
    DocumentIngestRequest,
    DocumentListResponse,
    DocumentRecord,
    HealthResponse,
    SearchRequest,
    SearchResponse,
)
from .qa_engine import DocumentQAEngine

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[DocumentQAConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = DocumentQAEngine(config=config)
    router = APIRouter(tags=["JARVIS Document QA"])

    @router.get("/doc-qa", response_class=HTMLResponse, include_in_schema=False)
    def doc_qa_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Document QA UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/doc-qa/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/doc-qa/documents", response_model=DocumentRecord)
    def ingest_document(req: DocumentIngestRequest) -> DocumentRecord:
        try:
            return engine.ingest_document(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/doc-qa/documents", response_model=DocumentListResponse)
    def list_documents() -> DocumentListResponse:
        return engine.list_documents()

    @router.delete("/api/doc-qa/documents/{doc_id}", response_model=DeleteDocumentResponse)
    def delete_document(doc_id: str) -> DeleteDocumentResponse:
        try:
            return engine.delete_document(doc_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api/doc-qa/search", response_model=SearchResponse)
    def search_documents(req: SearchRequest) -> SearchResponse:
        return engine.search(req)

    @router.post("/api/doc-qa/ask", response_model=AskResponse)
    def ask_question(req: AskRequest) -> AskResponse:
        return engine.ask(req)

    return router
