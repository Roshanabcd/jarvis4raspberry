"""Source-aware chunking and safe workspace directory crawler for unified indexing."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache"}
CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".bash", ".c", ".cpp", ".h", ".rs", ".go", ".sql", ".yaml", ".yml", ".json"}
LOG_EXTS = {".log", ".out", ".err"}
DOC_EXTS = {".md", ".markdown", ".txt", ".rst"}


def classify_file_source_type(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in CODE_EXTS:
        return "codebase"
    if ext in LOG_EXTS:
        return "terminal_log"
    if ext in DOC_EXTS:
        return "document"
    return None


def chunk_by_source_type(
    content: str,
    source_type: str,
    chunk_size: int = 540,
    chunk_overlap: int = 80,
) -> List[Dict[str, object]]:
    """Split content with source-specific location metadata (lines, log blocks, or sections)."""
    text = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    if source_type == "codebase":
        lines = text.split("\n")
        chunks: List[Dict[str, object]] = []
        buf: List[str] = []
        start_line = 1
        idx = 0
        for lineno, line in enumerate(lines, start=1):
            is_boundary = bool(re.match(r"^\s*(def |async def |class |function |export )", line))
            if buf and (is_boundary or sum(len(x) + 1 for x in buf) >= chunk_size):
                chunks.append(
                    {
                        "chunk_index": idx,
                        "location": f"lines {start_line}-{lineno - 1}",
                        "content": "\n".join(buf).strip(),
                    }
                )
                idx += 1
                buf = [line]
                start_line = lineno
            else:
                buf.append(line)
        if buf:
            chunks.append(
                {
                    "chunk_index": idx,
                    "location": f"lines {start_line}-{len(lines)}",
                    "content": "\n".join(buf).strip(),
                }
            )
        return [c for c in chunks if c["content"]]

    if source_type == "terminal_log":
        lines = [ln for ln in text.split("\n") if ln.strip()]
        chunks = []
        window = 12
        step = 10
        idx = 0
        for start in range(0, len(lines), step):
            block = lines[start : start + window]
            if not block:
                break
            joined = "\n".join(block)
            sev = "ERROR" if any(k in joined.upper() for k in ("ERROR", "TRACEBACK", "EXCEPTION", "FATAL")) else (
                "WARN" if "WARN" in joined.upper() else "INFO"
            )
            chunks.append(
                {
                    "chunk_index": idx,
                    "location": f"log lines {start + 1}-{start + len(block)} [{sev}]",
                    "content": joined,
                }
            )
            idx += 1
            if start + window >= len(lines):
                break
        return chunks

    # Default paragraph/section chunking for document and web_knowledge
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    section = "Main"
    buf_str = ""
    idx = 0
    for para in paragraphs:
        h_match = re.match(r"^(#{1,6})\s+(.+)$", para)
        if h_match:
            if buf_str.strip():
                chunks.append({"chunk_index": idx, "location": section, "content": buf_str.strip()})
                idx += 1
                buf_str = ""
            section = h_match.group(2).strip()[:100]
            continue
        candidate = f"{buf_str}\n\n{para}".strip() if buf_str else para
        if len(candidate) <= chunk_size:
            buf_str = candidate
        else:
            if buf_str.strip():
                chunks.append({"chunk_index": idx, "location": section, "content": buf_str.strip()})
                idx += 1
            tail = buf_str[-chunk_overlap:].strip() if chunk_overlap > 0 and len(buf_str) > chunk_overlap else ""
            buf_str = f"{tail}\n\n{para}".strip() if tail else para
    if buf_str.strip():
        chunks.append({"chunk_index": idx, "location": section, "content": buf_str.strip()})
    return chunks


def collect_directory_files(
    directory: str,
    allowed_roots: List[Path],
    max_files: int = 60,
    max_file_bytes: int = 512_000,
) -> Tuple[Path, List[Tuple[Path, str, str]], int]:
    """Safely crawl a directory within allowed_roots, returning (resolved_dir, files, skipped_count)."""
    target = Path(directory).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        raise ValueError(f"Directory does not exist: {directory}")

    permitted = False
    for root in allowed_roots:
        try:
            target.relative_to(root.resolve())
            permitted = True
            break
        except ValueError:
            continue
    if not permitted:
        raise PermissionError(
            f"Directory '{target}' is outside configured JARVIS_SEARCH_ALLOWED_ROOTS."
        )

    collected: List[Tuple[Path, str, str]] = []
    skipped = 0
    for root_dir, dirs, files in os.walk(target):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for fname in sorted(files):
            if len(collected) >= max_files:
                return target, collected, skipped
            fpath = Path(root_dir) / fname
            stype = classify_file_source_type(fpath)
            if not stype:
                skipped += 1
                continue
            try:
                if fpath.stat().st_size > max_file_bytes or fpath.stat().st_size == 0:
                    skipped += 1
                    continue
                text = fpath.read_text(encoding="utf-8", errors="ignore").strip()
                if len(text) < 5:
                    skipped += 1
                    continue
                collected.append((fpath, stype, text))
            except Exception:
                skipped += 1

    return target, collected, skipped
