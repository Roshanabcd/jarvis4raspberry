"""Environment-driven configuration for JARVIS Handwritten to Text Converter."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_OCR_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_handwriting_ocr" / "handwriting_ocr.db").resolve()


@dataclass(frozen=True)
class HandwritingOCRConfig:
    """Immutable runtime settings for handwritten-to-text OCR."""

    db_path: Path = field(default_factory=_default_db_path)
    default_language: str = field(
        default_factory=lambda: os.getenv("JARVIS_OCR_LANG", "eng")
    )
    tesseract_psm: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_OCR_PSM", "6"))
    )
    max_image_bytes: int = 10 * 1024 * 1024  # 10 MB
    openrouter_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    openrouter_vision_model: str = field(
        default_factory=lambda: os.getenv("JARVIS_OCR_VISION_MODEL", "openrouter/free")
    )
