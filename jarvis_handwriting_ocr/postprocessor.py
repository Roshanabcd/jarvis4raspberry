"""Post-processing cleanup for OCR text extracted from handwritten notes."""

from __future__ import annotations

import re


def clean_ocr_text(raw_text: str) -> str:
    """Normalize linebreaks, repair hyphenated line wraps, and tidy whitespace."""
    if not raw_text:
        return ""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Rejoin words split across line breaks with a trailing hyphen
    text = re.sub(r"([A-Za-z])-\n([A-Za-z])", r"\1\2", text)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Clean per-line trailing/leading spaces while keeping paragraph structure
    lines = [re.sub(r"[ \t]{2,}", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(lines).strip()
