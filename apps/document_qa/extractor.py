"""
Document Text and Metadata Extraction Engine with Multi-Format Support and Security Hardening.

Supported formats:
- PDF: Page-aware extraction via pypdf with pdftotext CLI fallback.
- DOCX: Structured extraction via python-docx (paragraphs, headings, tables).
- Markdown / TXT: UTF-8 / Latin-1 encoding with heading detection.
- CSV: Tabular row-by-row structure with column headers.
"""
from __future__ import annotations

import csv
import hashlib
import io
import logging
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from .models import DocumentMetadata, DocumentType

logger = logging.getLogger("JARVIS.DocumentAI.Extractor")

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class ExtractedPage:
    def __init__(self, page_number: int, text: str, section_heading: Optional[str] = None):
        self.page_number = page_number
        self.text = text
        self.section_heading = section_heading


class ExtractedDocument:
    def __init__(
        self,
        filename: str,
        file_type: DocumentType,
        file_size_bytes: int,
        checksum: str,
        pages: List[ExtractedPage],
        title: Optional[str] = None,
        author: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ):
        self.filename = filename
        self.file_type = file_type
        self.file_size_bytes = file_size_bytes
        self.checksum = checksum
        self.pages = pages
        self.title = title
        self.author = author
        self.metadata_json = metadata_json or {}

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def total_words(self) -> int:
        return sum(len(p.text.split()) for p in self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and filesystem attacks."""
    base = os.path.basename(filename.replace("\\", "/"))
    clean = re.sub(r"[^a-zA-Z0-9_\-\.]+", "_", base)
    # Strip dangerous leading periods or multiple consecutive dots
    clean = re.sub(r"^\.+", "", clean)
    clean = re.sub(r"\.{2,}", ".", clean)
    return clean or "document"


def detect_file_type(filename: str, header_bytes: bytes) -> DocumentType:
    """Detect file type via extension and magic bytes verification."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext == "pdf" or header_bytes.startswith(b"%PDF-"):
        return DocumentType.PDF
    if ext == "docx" or (header_bytes.startswith(b"PK\x03\x04") and ext == "docx"):
        return DocumentType.DOCX
    if ext in ("md", "markdown"):
        return DocumentType.MARKDOWN
    if ext == "csv":
        return DocumentType.CSV
    if ext in ("txt", "text", "log"):
        return DocumentType.TXT
    return DocumentType.UNKNOWN


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class DocumentExtractor:
    """Extracts text, metadata, and structural layout from diverse document formats."""

    def extract(self, file_path: str, original_filename: Optional[str] = None) -> ExtractedDocument:
        """Extract content from document with format-specific parsing."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowable limit ({MAX_FILE_SIZE_BYTES} bytes)")

        # Verify header bytes
        with open(file_path, "rb") as f:
            header_bytes = f.read(1024)

        fname = sanitize_filename(original_filename or os.path.basename(file_path))
        file_type = detect_file_type(fname, header_bytes)
        if file_type == DocumentType.UNKNOWN:
            raise ValueError(f"Unsupported document format for '{fname}'. Supported: PDF, DOCX, TXT, MD, CSV.")

        checksum = compute_sha256(file_path)

        if file_type == DocumentType.PDF:
            return self._extract_pdf(file_path, fname, file_size, checksum)
        elif file_type == DocumentType.DOCX:
            return self._extract_docx(file_path, fname, file_size, checksum)
        elif file_type == DocumentType.CSV:
            return self._extract_csv(file_path, fname, file_size, checksum)
        elif file_type in (DocumentType.MARKDOWN, DocumentType.TXT):
            return self._extract_text(file_path, fname, file_type, file_size, checksum)
        else:
            raise ValueError(f"Unhandled document type: {file_type}")

    def _extract_pdf(self, path: str, filename: str, size: int, checksum: str) -> ExtractedDocument:
        """Extract PDF text page-by-page preserving page numbers."""
        pages: List[ExtractedPage] = []
        title = None
        author = None
        metadata = {}

        # 1. Primary engine: pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            meta = reader.metadata
            if meta:
                title = meta.get("/Title") or meta.get("title")
                author = meta.get("/Author") or meta.get("author")
                metadata = {k.lstrip("/"): str(v) for k, v in meta.items() if v}

            for idx, page in enumerate(reader.pages, start=1):
                txt = page.extract_text() or ""
                # Normalize line breaks and whitespace
                norm_txt = re.sub(r"[ \t]+", " ", txt).strip()
                pages.append(ExtractedPage(page_number=idx, text=norm_txt))
        except Exception as ex:
            logger.warning("pypdf extraction failed or incomplete for %s: %s; falling back to pdftotext", filename, ex)
            pages.clear()

        # 2. Fallback: native /usr/bin/pdftotext if pypdf was empty or failed
        if not pages or all(len(p.text) < 10 for p in pages):
            if os.path.exists("/usr/bin/pdftotext"):
                try:
                    res = subprocess.run(
                        ["/usr/bin/pdftotext", path, "-"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=30,
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        # Split by form-feed character (\x0c) which marks page boundaries in pdftotext
                        raw_pages = res.stdout.split("\x0c")
                        pages = [
                            ExtractedPage(page_number=i + 1, text=p.strip())
                            for i, p in enumerate(raw_pages)
                            if p.strip()
                        ]
                except Exception as p_ex:
                    logger.warning("pdftotext execution error: %s", p_ex)

        if not pages:
            # Empty or scanned PDF without OCR
            pages = [ExtractedPage(page_number=1, text="[No readable text found in PDF]")]

        return ExtractedDocument(
            filename=filename,
            file_type=DocumentType.PDF,
            file_size_bytes=size,
            checksum=checksum,
            pages=pages,
            title=str(title) if title else None,
            author=str(author) if author else None,
            metadata_json=metadata,
        )

    def _extract_docx(self, path: str, filename: str, size: int, checksum: str) -> ExtractedDocument:
        """Extract DOCX content preserving heading hierarchy and tabular content."""
        import docx

        doc = docx.Document(path)
        pages: List[ExtractedPage] = []
        current_heading: Optional[str] = None
        current_paragraphs: List[str] = []
        page_idx = 1

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style and p.style.name else ""
            if "heading" in style_name:
                # If we have accumulated text under previous heading, group into a page/section
                if current_paragraphs:
                    pages.append(
                        ExtractedPage(
                            page_number=page_idx,
                            text="\n\n".join(current_paragraphs),
                            section_heading=current_heading,
                        )
                    )
                    page_idx += 1
                    current_paragraphs = []
                current_heading = text
                current_paragraphs.append(f"# {text}")
            else:
                current_paragraphs.append(text)

        # Extract docx tables
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    table_rows.append(" | ".join(cells))
            if table_rows:
                current_paragraphs.append("[Table Content]:\n" + "\n".join(table_rows))

        if current_paragraphs:
            pages.append(
                ExtractedPage(
                    page_number=page_idx,
                    text="\n\n".join(current_paragraphs),
                    section_heading=current_heading,
                )
            )

        if not pages:
            pages = [ExtractedPage(page_number=1, text="")]

        # Core properties metadata
        title = None
        author = None
        try:
            cp = doc.core_properties
            title = cp.title
            author = cp.author
        except Exception:
            pass

        return ExtractedDocument(
            filename=filename,
            file_type=DocumentType.DOCX,
            file_size_bytes=size,
            checksum=checksum,
            pages=pages,
            title=title,
            author=author,
        )

    def _extract_csv(self, path: str, filename: str, size: int, checksum: str) -> ExtractedDocument:
        """Extract tabular CSV formatted into searchable key-value rows."""
        pages: List[ExtractedPage] = []
        rows_per_page = 50

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = None
            current_rows = []
            page_idx = 1

            for row in reader:
                if not any(c.strip() for c in row):
                    continue
                if header is None:
                    header = [h.strip() for h in row]
                    continue

                row_str = ", ".join(f"{h}: {v.strip()}" for h, v in zip(header, row) if v.strip())
                current_rows.append(row_str)

                if len(current_rows) >= rows_per_page:
                    pages.append(
                        ExtractedPage(
                            page_number=page_idx,
                            text=f"Table Header: {', '.join(header)}\n" + "\n".join(current_rows),
                            section_heading=f"Rows {(page_idx-1)*rows_per_page + 1}-{page_idx*rows_per_page}",
                        )
                    )
                    page_idx += 1
                    current_rows = []

            if current_rows:
                hdr_str = f"Table Header: {', '.join(header)}\n" if header else ""
                pages.append(
                    ExtractedPage(
                        page_number=page_idx,
                        text=hdr_str + "\n".join(current_rows),
                        section_heading=f"Rows {(page_idx-1)*rows_per_page + 1} to end",
                    )
                )

        if not pages:
            pages = [ExtractedPage(page_number=1, text="[Empty CSV]")]

        return ExtractedDocument(
            filename=filename,
            file_type=DocumentType.CSV,
            file_size_bytes=size,
            checksum=checksum,
            pages=pages,
        )

    def _extract_text(
        self, path: str, filename: str, file_type: DocumentType, size: int, checksum: str
    ) -> ExtractedDocument:
        """Extract Markdown or Plain Text with section heading detection."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1", errors="replace") as f:
                content = f.read()

        pages: List[ExtractedPage] = []
        # Split Markdown by H1/H2 headings if present
        heading_re = re.compile(r"^(#{1,3}\s+.+)$", re.MULTILINE)
        parts = heading_re.split(content)

        if len(parts) > 1 and file_type == DocumentType.MARKDOWN:
            page_idx = 1
            current_heading = None
            i = 0
            if parts[0].strip():
                pages.append(ExtractedPage(page_number=page_idx, text=parts[0].strip()))
                page_idx += 1
                i = 1

            while i < len(parts):
                current_heading = parts[i].lstrip("#").strip()
                body = parts[i + 1].strip() if i + 1 < len(parts) else ""
                full_sec = f"{parts[i]}\n\n{body}" if body else parts[i]
                pages.append(
                    ExtractedPage(
                        page_number=page_idx,
                        text=full_sec,
                        section_heading=current_heading,
                    )
                )
                page_idx += 1
                i += 2
        else:
            # Split plain text into ~400-word logical pages
            paragraphs = content.split("\n\n")
            current_page_paras = []
            current_words = 0
            page_idx = 1

            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue
                w_count = len(p_clean.split())
                if current_words + w_count > 400 and current_page_paras:
                    pages.append(
                        ExtractedPage(
                            page_number=page_idx,
                            text="\n\n".join(current_page_paras),
                        )
                    )
                    page_idx += 1
                    current_page_paras = []
                    current_words = 0

                current_page_paras.append(p_clean)
                current_words += w_count

            if current_page_paras:
                pages.append(
                    ExtractedPage(
                        page_number=page_idx,
                        text="\n\n".join(current_page_paras),
                    )
                )

        if not pages:
            pages = [ExtractedPage(page_number=1, text="")]

        return ExtractedDocument(
            filename=filename,
            file_type=file_type,
            file_size_bytes=size,
            checksum=checksum,
            pages=pages,
        )


extractor = DocumentExtractor()
