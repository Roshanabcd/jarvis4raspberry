"""Multi-tier Handwritten-to-Text OCR engine (OpenRouter Vision LLM, local Tesseract, and diagnostics)."""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

from .config import HandwritingOCRConfig
from .models import (
    ConversionRecord,
    ConvertImageRequest,
    DeleteConversionResponse,
    HealthResponse,
    HistoryListResponse,
)
from .postprocessor import clean_ocr_text
from .preprocessor import decode_base64_image, pillow_available, preprocess_handwriting_image
from .storage import HandwritingOCRStore


def tesseract_available() -> bool:
    return bool(shutil.which("tesseract"))


class HandwritingOCREngine:
    """Orchestrates preprocessing, multi-tier OCR extraction, cleanup, and history persistence."""

    def __init__(self, config: Optional[HandwritingOCRConfig] = None) -> None:
        self.config = config or HandwritingOCRConfig()
        self.store = HandwritingOCRStore(self.config.db_path)

    def health(self) -> HealthResponse:
        return HealthResponse(
            backends={
                "pillow_preprocessor": pillow_available(),
                "local_tesseract": tesseract_available(),
                "openrouter_vision_llm": bool(self.config.openrouter_api_key),
            },
            total_conversions=self.store.count(),
        )

    def _ocr_openrouter_vision(self, img_bytes: bytes, mime: str, language: str) -> Optional[Tuple[str, float]]:
        if not self.config.openrouter_api_key:
            return None
        b64 = base64.b64encode(img_bytes).decode("ascii")
        data_url = f"data:{mime};base64,{b64}"
        payload = json.dumps(
            {
                "model": self.config.openrouter_vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Transcribe all handwritten text in this image accurately (language hint: {language}). "
                                    "Preserve bullet points and paragraphs. Output ONLY the transcribed text."
                                ),
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                "temperature": 0.1,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = str(data["choices"][0]["message"]["content"]).strip()
            return (text, 92.0) if text else None
        except Exception:
            return None

    def _ocr_local_tesseract(self, png_bytes: bytes, language: str) -> Optional[Tuple[str, float]]:
        tess = shutil.which("tesseract")
        if not tess:
            return None
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "input.png"
            img_path.write_bytes(png_bytes)
            cmd = [
                tess,
                str(img_path),
                "stdout",
                "-l",
                language,
                "--psm",
                str(self.config.tesseract_psm),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
            if proc.returncode != 0:
                return None
            extracted = proc.stdout.strip()
            # Estimate rough confidence from non-empty alphanumeric density
            if not extracted:
                return "", 0.0
            alnum = sum(1 for c in extracted if c.isalnum())
            ratio = alnum / max(len(extracted), 1)
            conf = round(min(96.0, max(45.0, ratio * 105.0)), 1)
            return extracted, conf

    def convert(self, req: ConvertImageRequest) -> ConversionRecord:
        t0 = time.perf_counter()
        raw_bytes, mime = decode_base64_image(req.image_base64, max_bytes=self.config.max_image_bytes)
        processed_bytes, width, height = preprocess_handwriting_image(
            raw_bytes, enable_preprocess=req.preprocess
        )
        lang = req.language.strip() or self.config.default_language

        raw_text = ""
        confidence = 0.0
        engine_used = "unavailable"

        # Tier 1: Optional Vision LLM
        if req.use_vision_llm and self.config.openrouter_api_key:
            v_res = self._ocr_openrouter_vision(raw_bytes, mime=mime, language=lang)
            if v_res is not None:
                raw_text, confidence = v_res
                engine_used = "openrouter_vision_llm"

        # Tier 2: Local Tesseract OCR
        if engine_used == "unavailable" and tesseract_available():
            t_res = self._ocr_local_tesseract(processed_bytes, language=lang)
            if t_res is not None:
                raw_text, confidence = t_res
                engine_used = "local_tesseract"

        # Tier 3: Honest diagnostic fallback if no OCR backend is installed/configured
        if engine_used == "unavailable":
            engine_used = "diagnostic_no_ocr_backend"
            raw_text = (
                "No OCR backend detected on this host. Install local Tesseract on Raspberry Pi 5 "
                "('sudo apt install -y tesseract-ocr') or configure OPENROUTER_API_KEY with use_vision_llm=true."
            )
            confidence = 0.0

        cleaned = clean_ocr_text(raw_text) if req.cleanup_text else raw_text
        words = len(cleaned.split()) if cleaned else 0
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        saved = self.store.save_conversion(
            {
                "filename": req.filename.strip(),
                "width": width,
                "height": height,
                "engine_used": engine_used,
                "language": lang,
                "raw_text": raw_text,
                "cleaned_text": cleaned,
                "word_count": words,
                "char_count": len(cleaned),
                "confidence": confidence,
                "latency_ms": latency_ms,
            }
        )
        return ConversionRecord(**saved)

    def list_history(self, limit: int = 50) -> HistoryListResponse:
        rows = [ConversionRecord(**r) for r in self.store.list_conversions(limit=limit)]
        return HistoryListResponse(total=len(rows), items=rows)

    def get_conversion(self, conversion_id: int) -> ConversionRecord:
        row = self.store.get_conversion(conversion_id)
        if row is None:
            raise KeyError(f"Conversion #{conversion_id} not found.")
        return ConversionRecord(**row)

    def delete_conversion(self, conversion_id: int) -> DeleteConversionResponse:
        if not self.store.delete_conversion(conversion_id):
            raise KeyError(f"Conversion #{conversion_id} not found.")
        return DeleteConversionResponse(deleted=True, conversion_id=conversion_id)
