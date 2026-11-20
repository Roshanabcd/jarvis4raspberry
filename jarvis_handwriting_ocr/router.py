"""FastAPI APIRouter for JARVIS Handwritten to Text Converter."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import HandwritingOCRConfig
from .models import (
    ConversionRecord,
    ConvertImageRequest,
    DeleteConversionResponse,
    HealthResponse,
    HistoryListResponse,
)
from .ocr_engine import HandwritingOCREngine

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(config: Optional[HandwritingOCRConfig] = None) -> APIRouter:
    """Create a self-contained FastAPI router mountable into JARVIS OS."""
    engine = HandwritingOCREngine(config=config)
    router = APIRouter(tags=["JARVIS Handwritten to Text Converter"])

    @router.get("/handwriting-ocr", response_class=HTMLResponse, include_in_schema=False)
    def handwriting_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Handwriting OCR UI asset missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get("/api/handwriting-ocr/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return engine.health()

    @router.post("/api/handwriting-ocr/convert", response_model=ConversionRecord)
    def convert_image(req: ConvertImageRequest) -> ConversionRecord:
        try:
            return engine.convert(req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/api/handwriting-ocr/history", response_model=HistoryListResponse)
    def list_history(limit: int = Query(default=50, ge=1, le=200)) -> HistoryListResponse:
        return engine.list_history(limit=limit)

    @router.get("/api/handwriting-ocr/history/{conversion_id}/export", response_class=PlainTextResponse)
    def export_conversion(
        conversion_id: int,
        fmt: str = Query(default="txt"),
    ) -> PlainTextResponse:
        try:
            rec = engine.get_conversion(conversion_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        ext = "md" if fmt.lower() == "md" else "txt"
        body = (
            f"# {rec.filename}\n\n"
            f"- Engine: `{rec.engine_used}` | Confidence: `{rec.confidence}%` | Words: `{rec.word_count}`\n\n"
            f"{rec.cleaned_text}\n"
            if ext == "md"
            else rec.cleaned_text
        )
        return PlainTextResponse(
            content=body,
            headers={"Content-Disposition": f'attachment; filename="ocr_{rec.id}.{ext}"'},
        )

    @router.delete("/api/handwriting-ocr/history/{conversion_id}", response_model=DeleteConversionResponse)
    def delete_conversion(conversion_id: int) -> DeleteConversionResponse:
        try:
            return engine.delete_conversion(conversion_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
