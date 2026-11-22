"""Real-Time Local OCR Engine using Tesseract & Pillow preprocessing (Module 43)."""

from __future__ import annotations

import io
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageOps


class LocalOCREngine:
    """
    Extracts normalized text, confidence scores, and word bounding boxes
    from in-memory PNG frames using local Tesseract OCR.
    """

    def __init__(self) -> None:
        self.tesseract_binary = shutil.which("tesseract")
        try:
            import pytesseract  # type: ignore
            self._pytesseract = pytesseract
        except Exception:
            self._pytesseract = None

    @property
    def is_available(self) -> bool:
        return bool(self.tesseract_binary and self._pytesseract is not None)

    @staticmethod
    def preprocess(img: Image.Image, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        work = img
        if region is not None:
            x, y, w, h = region
            work = work.crop((max(0, x), max(0, y), min(img.width, x + w), min(img.height, y + h)))
        gray = ImageOps.grayscale(work)
        # Upscale small UI/terminal fonts for crisp Tesseract accuracy
        if gray.width < 1000:
            gray = gray.resize((gray.width * 2, gray.height * 2), Image.Resampling.LANCZOS)
        return ImageOps.autocontrast(gray)

    @staticmethod
    def normalize_text(text: str) -> str:
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
        return "\n".join(ln for ln in lines if ln)

    def extract_text(
        self,
        png_bytes: bytes,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available:
            return {
                "engine": "tesseract_unavailable",
                "available": False,
                "text": "",
                "confidence": None,
                "boxes": [],
                "error": "Install tesseract-ocr and pytesseract for local OCR.",
            }

        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        pre = self.preprocess(img, region=region)
        assert self._pytesseract is not None

        raw_text = self._pytesseract.image_to_string(pre, config="--psm 6")
        data = self._pytesseract.image_to_data(pre, config="--psm 6", output_type=self._pytesseract.Output.DICT)

        boxes: List[Dict[str, Any]] = []
        confs: List[float] = []
        n = len(data.get("text", []))
        for i in range(n):
            word = (data["text"][i] or "").strip()
            try:
                conf = float(data["conf"][i])
            except Exception:
                conf = -1.0
            if word and conf >= 0:
                confs.append(conf)
                boxes.append(
                    {
                        "text": word,
                        "left": int(data["left"][i]),
                        "top": int(data["top"][i]),
                        "width": int(data["width"][i]),
                        "height": int(data["height"][i]),
                        "confidence": round(conf, 1),
                    }
                )

        avg_conf = round(sum(confs) / len(confs), 1) if confs else None
        return {
            "engine": "tesseract_local",
            "available": True,
            "text": self.normalize_text(raw_text),
            "confidence": avg_conf,
            "boxes": boxes[:200],
            "error": None,
        }
