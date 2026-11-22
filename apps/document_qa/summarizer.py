"""
Multi-Format Document Summarization Engine for JARVIS Document AI.

Supported summary formats:
- Executive Summary: High-level overview of objectives, findings, and conclusions.
- Key Takeaways: High-impact bulleted takeaways and actionable points.
- Comprehensive Summary: Detailed narrative covering core concepts and findings.
- Structured Outline: Hierarchical topical outline with headings and bullet points.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

from apps.apps_center.ai_service import SharedAIService
from .database import DocumentDatabase, db as default_db
from .models import DocumentChunk, DocumentMetadata, DocumentSummary, SummaryType

logger = logging.getLogger("JARVIS.DocumentAI.Summarizer")


class DocumentSummarizer:
    """Generates structured, grounded summaries across uploaded documents."""

    def __init__(
        self,
        database: Optional[DocumentDatabase] = None,
        ai_service: Optional[SharedAIService] = None,
    ):
        self.db = database or default_db
        self.ai = ai_service or SharedAIService()

    def summarize(
        self,
        doc_id: str,
        user_id: str = "default_user",
        summary_type: SummaryType = SummaryType.EXECUTIVE,
        provider: Optional[str] = None,
    ) -> DocumentSummary:
        """Generate a summary for a specific document."""
        t0 = time.perf_counter()
        meta = self.db.get_document(doc_id, user_id)
        if not meta:
            raise ValueError(f"Document with ID '{doc_id}' not found for user.")

        chunks = self.db.get_document_chunks(doc_id, user_id)
        if not chunks:
            return DocumentSummary(
                doc_id=doc_id,
                filename=meta.filename,
                summary_type=summary_type,
                summary_text="Document has no extracted text content to summarize.",
                grounded=False,
            )

        # Assemble full document text or representative chunks (capped at ~8000 words to respect token budgets)
        full_text = "\n\n".join(f"[{c.citation_label}]: {c.text}" for c in chunks[:40])

        system_prompt, user_prompt = self._build_summary_prompts(meta.filename, full_text, summary_type)

        summary_text = None
        key_topics = []

        try:
            if hasattr(self.ai, "chat") or hasattr(self.ai, "generate"):
                call_fn = getattr(self.ai, "chat", None) or getattr(self.ai, "generate", None)
                res = call_fn(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    provider=provider,
                    max_tokens=900,
                    temperature=0.3,
                )
                if isinstance(res, dict):
                    summary_text = res.get("text") or res.get("response")
                elif isinstance(res, str) and res.strip():
                    summary_text = res.strip()
        except Exception as ex:
            logger.warning("AI summarization failed: %s; using deterministic structured summarizer", ex)

        if not summary_text or not summary_text.strip():
            summary_text, key_topics = self._deterministic_summary(meta.filename, chunks, summary_type)
        else:
            # Extract key topics if formatted
            key_topics = self._extract_key_topics(chunks)

        dur_ms = (time.perf_counter() - t0) * 1000
        return DocumentSummary(
            doc_id=doc_id,
            filename=meta.filename,
            summary_type=summary_type,
            summary_text=summary_text.strip(),
            key_topics=key_topics,
            grounded=True,
            word_count=len(summary_text.split()),
            latency_ms=round(dur_ms, 2),
        )

    def _build_summary_prompts(
        self, filename: str, content: str, summary_type: SummaryType
    ) -> tuple[str, str]:
        format_instructions = {
            SummaryType.EXECUTIVE: "Provide a concise 2-3 paragraph Executive Summary highlighting document purpose, key findings, and core conclusions.",
            SummaryType.KEY_TAKEAWAYS: "Provide a bulleted list of 5 to 10 Key Takeaways and actionable points directly supported by the text.",
            SummaryType.COMPREHENSIVE: "Provide a Comprehensive, detailed section-by-section breakdown summarizing all major points and supporting arguments.",
            SummaryType.STRUCTURED_OUTLINE: "Provide a hierarchical Markdown outline (using #, ##, and bullet points) organizing the topics covered.",
        }.get(summary_type, "Provide a comprehensive summary.")

        system_prompt = (
            "You are JARVIS Document AI, a factual and precise document summarization engine.\n"
            "DIRECTIVES:\n"
            "1. Base your summary exclusively on the provided <document_content>.\n"
            "2. Do NOT invent or assume facts not present in the text.\n"
            "3. Format your output in clean Markdown.\n"
            f"4. Format Requirement: {format_instructions}"
        )

        user_prompt = (
            f"Document: {filename}\n\n"
            f"<document_content>\n{content}\n</document_content>\n\n"
            f"Generate the {summary_type.value} summary according to the directives."
        )

        return system_prompt, user_prompt

    def _deterministic_summary(
        self, filename: str, chunks: List[DocumentChunk], summary_type: SummaryType
    ) -> tuple[str, List[str]]:
        """Deterministic summary generator when external AI is offline."""
        topics = self._extract_key_topics(chunks)

        # Gather first sentences of major chunks
        representative_sentences = []
        for c in chunks:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", c.text) if len(s.split()) >= 6]
            if sentences:
                representative_sentences.append(f"- **{c.citation_label}:** {sentences[0]}")

        if summary_type == SummaryType.KEY_TAKEAWAYS:
            body = "### Key Takeaways\n\n" + "\n".join(representative_sentences[:8])
        elif summary_type == SummaryType.STRUCTURED_OUTLINE:
            body = f"# Outline: {filename}\n\n"
            for t in topics[:6]:
                body += f"## Topic: {t.title()}\n"
            body += "\n### Extracted Highlights\n" + "\n".join(representative_sentences[:6])
        else:
            highlights = " ".join(s.split(":** ")[-1] for s in representative_sentences[:5])
            body = (
                f"### Executive Summary — {filename}\n\n"
                f"This document spans {len(chunks)} recorded passage sections covering core themes including {', '.join(topics[:5])}.\n\n"
                f"{highlights}\n\n"
                f"*(Generated via local grounded extraction)*"
            )

        return body, topics

    def _extract_key_topics(self, chunks: List[DocumentChunk]) -> List[str]:
        """Extract high-frequency significant keywords as topics."""
        word_freq: Dict[str, int] = {}
        for c in chunks:
            for w in re.findall(r"\b[A-Za-z]{5,15}\b", c.text):
                w_lower = w.lower()
                word_freq[w_lower] = word_freq.get(w_lower, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:10]]
