"""Document parser supporting PDF, Markdown, and plain text inputs."""

from __future__ import annotations

import base64
import io
import re
import zlib
from pathlib import Path
from typing import Optional, Tuple


def detect_doc_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in {".md", ".markdown"}:
        return "markdown"
    return "text"


def _extract_pdf_text_pypdf(raw_bytes: bytes) -> Optional[str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                pages.append(txt.strip())
        return "\n\n".join(pages).strip()
    except Exception:
        return None


def _extract_pdf_text_fallback(raw_bytes: bytes) -> str:
    """Lightweight pure-Python PDF text literal extractor for uncompressed or Flate streams."""
    chunks: list[str] = []

    def _scan_literals(data: bytes) -> None:
        text_str = data.decode("latin-1", errors="ignore")
        for match in re.findall(r"\(([^()]{2,500})\)\s*Tj", text_str):
            cleaned = (
                match.replace(r"\(", "(")
                .replace(r"\)", ")")
                .replace(r"\n", " ")
                .replace(r"\r", " ")
                .strip()
            )
            if cleaned:
                chunks.append(cleaned)
        for arr in re.findall(r"\[(.*?)\]\s*TJ", text_str, flags=re.DOTALL):
            parts = re.findall(r"\(([^()]+)\)", arr)
            joined = "".join(parts).strip()
            if joined:
                chunks.append(joined)

    _scan_literals(raw_bytes)
    for stream_match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw_bytes, flags=re.DOTALL):
        payload = stream_match.group(1)
        try:
            decompressed = zlib.decompress(payload)
            _scan_literals(decompressed)
        except Exception:
            continue

    return "\n".join(chunks).strip()


def extract_document_text(
    filename: str,
    content_text: Optional[str] = None,
    content_base64: Optional[str] = None,
) -> Tuple[str, str]:
    """Return (doc_type, extracted_text) from plain text or base64-encoded PDF/MD/TXT."""
    doc_type = detect_doc_type(filename)

    if content_text is not None and content_text.strip():
        return doc_type, content_text.strip()

    if not content_base64 or not content_base64.strip():
        raise ValueError("Provide either 'content_text' or 'content_base64'.")

    # Strip optional data URL prefix (e.g. data:application/pdf;base64,...)
    b64_data = content_base64.strip()
    if "," in b64_data and b64_data.lower().startswith("data:"):
        b64_data = b64_data.split(",", 1)[1]

    try:
        raw_bytes = base64.b64decode(b64_data)
    except Exception as exc:
        raise ValueError("Invalid base64 document payload.") from exc

    if doc_type == "pdf":
        text = _extract_pdf_text_pypdf(raw_bytes)
        if not text:
            text = _extract_pdf_text_fallback(raw_bytes)
        if not text:
            raise ValueError(
                "Could not extract text from PDF. Install 'pypdf' for complex PDFs or upload a text-based PDF."
            )
        return doc_type, text

    try:
        decoded = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        decoded = raw_bytes.decode("latin-1", errors="ignore")
    decoded = decoded.strip()
    if not decoded:
        raise ValueError("Uploaded document contains no readable text.")
    return doc_type, decoded
