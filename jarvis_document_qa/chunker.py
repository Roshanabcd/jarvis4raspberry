"""Section-aware overlapping text chunker for Markdown, PDF, and plain text."""

from __future__ import annotations

import re
from typing import Dict, List


def chunk_document(
    text: str,
    doc_type: str = "text",
    chunk_size: int = 520,
    chunk_overlap: int = 90,
) -> List[Dict[str, object]]:
    """Split text into overlapping chunks while preserving Markdown heading context."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
    chunks: List[Dict[str, object]] = []
    current_section = "Overview"
    buffer = ""
    chunk_index = 0

    def _flush(buf: str, section: str) -> None:
        nonlocal chunk_index
        cleaned = buf.strip()
        if not cleaned:
            return
        chunks.append(
            {
                "chunk_index": chunk_index,
                "section": section,
                "content": cleaned,
            }
        )
        chunk_index += 1

    for para in paragraphs:
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", para)
        if doc_type == "markdown" and heading_match:
            if buffer.strip():
                _flush(buffer, current_section)
                buffer = ""
            current_section = heading_match.group(2).strip()[:120]
            continue

        if len(para) > chunk_size:
            if buffer.strip():
                _flush(buffer, current_section)
                buffer = ""
            start = 0
            step = max(120, chunk_size - chunk_overlap)
            while start < len(para):
                piece = para[start : start + chunk_size].strip()
                if piece:
                    _flush(piece, current_section)
                if start + chunk_size >= len(para):
                    break
                start += step
            continue

        candidate = f"{buffer}\n\n{para}".strip() if buffer else para
        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            _flush(buffer, current_section)
            tail = buffer[-chunk_overlap:].strip() if chunk_overlap > 0 and len(buffer) > chunk_overlap else ""
            buffer = f"{tail}\n\n{para}".strip() if tail else para

    if buffer.strip():
        _flush(buffer, current_section)

    return chunks
