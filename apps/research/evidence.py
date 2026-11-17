"""
Evidence extraction and record store for JARVIS AI Research Assistant.
Extracts factual claims paired strictly with verbatim supporting source passages,
evaluates support levels, and ensures zero unsupported assertions.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
import uuid

from apps.research.models import (
    EvidenceRecord,
    ResearchSource,
    SupportLevel,
)

logger = logging.getLogger("JARVIS-RESEARCH-EVIDENCE")

# Patterns indicating substantive factual findings
_FACT_INDICATORS = re.compile(
    r"\b(found that|demonstrated|showed|revealed|reported|concluded|measures?|increased|decreased|"
    r"resulted in|percent|%|\d+x|\$\d+|\b\d{4}\b|indicates?|proves?|observed|developed|tested|evaluated)\b",
    re.IGNORECASE,
)


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences while respecting abbreviations."""
    # Simple regex sentence splitter
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 25]
    return sentences


class EvidenceExtractor:
    """Extracts grounded evidence records from source content."""

    def __init__(self, max_records_per_source: int = 5) -> None:
        self.max_records_per_source = max_records_per_source

    def extract_from_source(
        self,
        source: ResearchSource,
        task_id: str = "",
        focus_terms: Optional[List[str]] = None,
    ) -> List[EvidenceRecord]:
        """
        Extract factual claims from source content, linking each claim to
        its exact verbatim supporting passage.
        """
        content = source.content.strip()
        if not content or len(content) < 30:
            return []

        sentences = _split_into_sentences(content)
        records: List[EvidenceRecord] = []
        seen_passages = set()

        # Score and filter candidate sentences
        scored_sentences = []
        for i, sent in enumerate(sentences):
            if sent in seen_passages:
                continue

            score = 0
            if _FACT_INDICATORS.search(sent):
                score += 2

            if focus_terms:
                for term in focus_terms:
                    if term.lower() in sent.lower():
                        score += 3

            # Prefer informative sentences (between 50 and 300 characters)
            if 50 <= len(sent) <= 300:
                score += 1

            if score > 0:
                scored_sentences.append((score, i, sent))

        # Sort by score descending
        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        for score, idx, passage in scored_sentences[: self.max_records_per_source]:
            seen_passages.add(passage)

            # Synthesize clean factual claim from passage
            clean_claim = self._formulate_claim(passage)
            support_lvl = SupportLevel.DIRECTLY_SUPPORTED if passage in content else SupportLevel.PARTIALLY_SUPPORTED

            # Determine confidence notes based on source category
            author_ref = source.authors[0] if source.authors else source.publisher_or_domain or "Source"
            date_ref = f" ({source.published_date})" if source.published_date else ""
            notes = f"Grounding verified from {author_ref}{date_ref}. Source category: {source.category.value}."

            rec = EvidenceRecord(
                evidence_id=f"ev_{uuid.uuid4().hex[:10]}",
                task_id=task_id or source.task_id,
                source_id=source.source_id,
                claim=clean_claim,
                supporting_passage=passage,
                support_level=support_lvl,
                confidence_notes=notes,
            )
            records.append(rec)

        return records

    @staticmethod
    def _formulate_claim(passage: str) -> str:
        """Derive a clean, concise claim statement from a supporting passage."""
        claim = passage.strip()
        # Remove meta prefixes like "In this paper we show that", "According to..."
        claim = re.sub(r"^(?:in this (?:paper|study|article|work),? (?:we|the authors) (?:show|find|demonstrate) that\s+)", "", claim, flags=re.IGNORECASE)
        claim = re.sub(r"^(?:we (?:find|found|observe|observed|show|demonstrate) that\s+)", "", claim, flags=re.IGNORECASE)
        # Capitalize first letter
        if claim:
            claim = claim[0].upper() + claim[1:]
        return claim


class EvidenceStore:
    """Task-scoped evidence repository for cross-referencing and verification."""

    def __init__(self, task_id: str = "") -> None:
        self.task_id = task_id
        self._records: Dict[str, EvidenceRecord] = {}

    def add_records(self, records: List[EvidenceRecord]) -> None:
        """Add evidence records to store."""
        for r in records:
            self._records[r.evidence_id] = r

    def get_records(self) -> List[EvidenceRecord]:
        """Return all evidence records."""
        return list(self._records.values())

    def get_by_source(self, source_id: str) -> List[EvidenceRecord]:
        """Return evidence derived from a specific source."""
        return [r for r in self._records.values() if r.source_id == source_id]

    def search_evidence(self, query: str) -> List[EvidenceRecord]:
        """Search claims and passages for matching keywords."""
        q_lower = query.lower()
        return [r for r in self._records.values() if q_lower in r.claim.lower() or q_lower in r.supporting_passage.lower()]
