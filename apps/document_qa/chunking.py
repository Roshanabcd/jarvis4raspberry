"""
Hierarchical Structure-Aware Document Chunking Engine.

Features:
- Respects page and section boundaries (chunks never span across disparate pages without explicit tag).
- Preserves exact page numbers (1-indexed) and section headings for precise citation grounding.
- Sentence-boundary preservation using smart punctuation boundaries.
- Configurable target chunk size (~250 words) with sliding window overlap (~40 words).
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional
import uuid

from .extractor import ExtractedDocument, ExtractedPage
from .models import DocumentChunk

logger = logging.getLogger("JARVIS.DocumentAI.Chunking")

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def split_sentences(text: str) -> List[str]:
    """Split text into sentences while keeping sentence terminators intact."""
    clean = text.strip()
    if not clean:
        return []
    # Split on sentence boundary
    sentences = _SENTENCE_SPLIT_RE.split(clean)
    return [s.strip() for s in sentences if s.strip()]


def chunk_document(
    extracted_doc: ExtractedDocument,
    doc_id: str,
    user_id: str = "default_user",
    target_words: int = 250,
    overlap_words: int = 40,
) -> List[DocumentChunk]:
    """Chunk extracted document pages into grounded, indexable DocumentChunks."""
    chunks: List[DocumentChunk] = []
    chunk_index = 0
    char_offset = 0

    for page in extracted_doc.pages:
        page_text = page.text.strip()
        if not page_text:
            continue

        sentences = split_sentences(page_text)
        if not sentences:
            sentences = [page_text]

        current_sentences: List[str] = []
        current_word_count = 0

        for sentence in sentences:
            words = sentence.split()
            word_count = len(words)

            if (current_word_count + word_count > target_words) and current_sentences:
                # Finalize chunk
                chunk_text = " ".join(current_sentences)
                c_len = len(chunk_text)
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"chk_{doc_id}_{chunk_index}_{uuid.uuid4().hex[:6]}",
                        doc_id=doc_id,
                        user_id=user_id,
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        section_heading=page.section_heading,
                        text=chunk_text,
                        char_start=char_offset,
                        char_end=char_offset + c_len,
                        word_count=len(chunk_text.split()),
                    )
                )
                chunk_index += 1
                char_offset += c_len + 1

                # Carry over overlap sentences
                overlap_sentences: List[str] = []
                overlap_count = 0
                for s in reversed(current_sentences):
                    s_words = len(s.split())
                    if overlap_count + s_words <= overlap_words:
                        overlap_sentences.insert(0, s)
                        overlap_count += s_words
                    else:
                        break

                current_sentences = overlap_sentences
                current_word_count = overlap_count

            current_sentences.append(sentence)
            current_word_count += word_count

        # Final chunk for the page
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            c_len = len(chunk_text)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chk_{doc_id}_{chunk_index}_{uuid.uuid4().hex[:6]}",
                    doc_id=doc_id,
                    user_id=user_id,
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                    section_heading=page.section_heading,
                    text=chunk_text,
                    char_start=char_offset,
                    char_end=char_offset + c_len,
                    word_count=len(chunk_text.split()),
                )
            )
            chunk_index += 1
            char_offset += c_len + 1

    logger.debug("Document '%s' produced %d chunks across %d pages", extracted_doc.filename, len(chunks), len(extracted_doc.pages))
    return chunks
