"""
Verification, contradiction detection, and research limitations engine for JARVIS AI Research Assistant.
Cross-references claims across sources, identifies conflicting data points,
and compiles explicit research boundaries and uncertainties.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from apps.research.models import (
    ContradictionRecord,
    EvidenceRecord,
    ResearchPlan,
    ResearchSource,
    SourceCategory,
)

logger = logging.getLogger("JARVIS-RESEARCH-VERIFICATION")

# Words indicating conflict or opposing directions
_OPPOSING_PAIRS = [
    (r"\bincreased?\b", r"\bdecreased?\b"),
    (r"\bhigher\b", r"\blower\b"),
    (r"\bfaster\b", r"\bslower\b"),
    (r"\bsuccessful\b", r"\bfailed\b"),
    (r"\bsafe\b", r"\bunsafe|dangerous|harmful\b"),
    (r"\beffective\b", r"\bineffective\b"),
    (r"\bsupports?\b", r"\brejects?|refutes?|opposes?\b"),
    (r"\bcompatible\b", r"\bincompatible\b"),
]


class FactChecker:
    """Verifies evidence claims and computes corroboration across sources."""

    def __init__(self, sources: List[ResearchSource], evidence: List[EvidenceRecord]) -> None:
        self.sources = {s.source_id: s for s in sources}
        self.evidence = evidence

    def find_corroborations(self) -> List[Dict[str, Any]]:
        """Identify claims backed by multiple independent sources."""
        corroborations: List[Dict[str, Any]] = []

        # Group evidence by common key terms
        for i, ev_a in enumerate(self.evidence):
            src_a = self.sources.get(ev_a.source_id)
            if not src_a:
                continue

            matching_sources = [src_a.publisher_or_domain or src_a.url]
            supporting_ids = [ev_a.evidence_id]

            for j, ev_b in enumerate(self.evidence):
                if i >= j or ev_a.source_id == ev_b.source_id:
                    continue

                src_b = self.sources.get(ev_b.source_id)
                if not src_b:
                    continue

                if self._claims_overlap(ev_a.claim, ev_b.claim):
                    domain_b = src_b.publisher_or_domain or src_b.url
                    if domain_b not in matching_sources:
                        matching_sources.append(domain_b)
                        supporting_ids.append(ev_b.evidence_id)

            if len(matching_sources) >= 2:
                corroborations.append({
                    "topic": ev_a.claim[:80],
                    "claim": ev_a.claim,
                    "independent_sources_count": len(matching_sources),
                    "sources": matching_sources,
                    "evidence_ids": supporting_ids,
                })

        return corroborations

    @staticmethod
    def _claims_overlap(claim_a: str, claim_b: str) -> bool:
        """Check if two claims share significant non-stopword terminology."""
        words_a = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_a.lower()))
        words_b = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_b.lower()))
        common = words_a.intersection(words_b)
        # Avoid common filler words
        stopwords = {"this", "that", "with", "from", "have", "were", "been", "their", "which", "about", "study", "paper"}
        significant = common - stopwords
        return len(significant) >= 3


class ContradictionDetector:
    """Detects opposing statements or conflicting data points across sources."""

    def __init__(self, sources: List[ResearchSource], evidence: List[EvidenceRecord]) -> None:
        self.sources = {s.source_id: s for s in sources}
        self.evidence = evidence

    def detect_contradictions(self, task_id: str) -> List[ContradictionRecord]:
        """Find contradictory claims between independent sources."""
        contradictions: List[ContradictionRecord] = []
        seen_pairs = set()

        for i, ev_a in enumerate(self.evidence):
            for j, ev_b in enumerate(self.evidence):
                if i >= j or ev_a.source_id == ev_b.source_id:
                    continue

                pair_key = tuple(sorted([ev_a.evidence_id, ev_b.evidence_id]))
                if pair_key in seen_pairs:
                    continue

                conflict_analysis = self._check_conflict(ev_a.claim, ev_b.claim)
                if conflict_analysis:
                    seen_pairs.add(pair_key)
                    src_a = self.sources.get(ev_a.source_id)
                    src_b = self.sources.get(ev_b.source_id)

                    domain_a = src_a.publisher_or_domain if src_a else "Source A"
                    domain_b = src_b.publisher_or_domain if src_b else "Source B"

                    record = ContradictionRecord(
                        contradiction_id=f"contra_{uuid.uuid4().hex[:10]}",
                        task_id=task_id,
                        topic=self._extract_topic(ev_a.claim, ev_b.claim),
                        claim_a=ev_a.claim,
                        source_a_id=ev_a.source_id,
                        claim_b=ev_b.claim,
                        source_b_id=ev_b.source_id,
                        analysis=f"Discrepancy identified between {domain_a} and {domain_b}: {conflict_analysis}",
                        unresolved=True,
                    )
                    contradictions.append(record)

        return contradictions

    @staticmethod
    def _check_conflict(claim_a: str, claim_b: str) -> Optional[str]:
        """Test for polarity opposition or numeric mismatch on shared keywords."""
        words_a = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_a.lower()))
        words_b = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_b.lower()))
        common = (words_a & words_b) - {"this", "that", "with", "from", "have", "were", "been", "their"}

        if len(common) < 2:
            return None

        # Check opposing terminology pairs
        for p1, p2 in _OPPOSING_PAIRS:
            match_1a = re.search(p1, claim_a, re.IGNORECASE)
            match_2b = re.search(p2, claim_b, re.IGNORECASE)
            match_1b = re.search(p1, claim_b, re.IGNORECASE)
            match_2a = re.search(p2, claim_a, re.IGNORECASE)

            if (match_1a and match_2b) or (match_1b and match_2a):
                term1 = (match_1a or match_1b).group(0)
                term2 = (match_2b or match_2a).group(0)
                return f"Opposing claims regarding shared concepts ({', '.join(list(common)[:3])}): '{term1}' vs '{term2}'."

        # Check conflicting numbers (e.g., differing percentages or year metrics)
        nums_a = re.findall(r"\b\d+(?:\.\d+)?%?\b", claim_a)
        nums_b = re.findall(r"\b\d+(?:\.\d+)?%?\b", claim_b)
        if nums_a and nums_b and nums_a != nums_b and len(common) >= 3:
            return f"Conflicting numerical figures reported on {', '.join(list(common)[:3])}: [{', '.join(nums_a)}] vs [{', '.join(nums_b)}]."

        return None

    @staticmethod
    def _extract_topic(claim_a: str, claim_b: str) -> str:
        words_a = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_a.lower()))
        words_b = set(re.findall(r"\b[a-zA-Z]{4,}\b", claim_b.lower()))
        common = list((words_a & words_b) - {"this", "that", "with", "from", "have", "were", "been", "their"})
        if common:
            return f"Conflict on {', '.join(common[:3])}"
        return "Disputed Claim"


class LimitationsCompiler:
    """Compiles research boundaries, data coverage limitations, and uncertainties."""

    @staticmethod
    def compile_limitations(
        sources: List[ResearchSource],
        plan: Optional[ResearchPlan],
        contradictions: List[ContradictionRecord],
        unanswered_questions: Optional[List[str]] = None,
    ) -> List[str]:
        """Generate honest, transparent research limitations."""
        limitations: List[str] = []

        # 1. Abstract-only / blocked sources
        abstract_only_count = sum(1 for s in sources if s.is_abstract_only)
        if abstract_only_count > 0:
            limitations.append(
                f"{abstract_only_count} scholarly source(s) were analyzed from peer-reviewed abstracts only; "
                f"underlying raw datasets or supplementary methodology appendices were not accessible without institutional credentials."
            )

        # 2. Blocked or unavailable sources
        blocked_count = sum(1 for s in sources if s.extraction_status.value in ("ACCESS_BLOCKED", "SOURCE_UNAVAILABLE"))
        if blocked_count > 0:
            limitations.append(
                f"{blocked_count} candidate web source(s) could not be retrieved due to paywalls, authentication requirements, or connection timeouts."
            )

        # 3. Contradictions
        if contradictions:
            unresolved = [c for c in contradictions if c.unresolved]
            if unresolved:
                limitations.append(
                    f"{len(unresolved)} empirical disagreement(s) or divergent metrics were identified between sources and remain contested in the literature."
                )

        # 4. Temporal constraints
        dated_sources = [s for s in sources if s.published_date]
        if not dated_sources:
            limitations.append("Publication dates were unavailable for multiple sources; historical timeliness should be cross-verified.")

        # 5. Unanswered supporting questions
        if unanswered_questions:
            limitations.append(
                f"The following supporting questions could not be conclusively resolved from retrieved sources: {'; '.join(unanswered_questions)}."
            )

        # 6. Scope notice
        limitations.append(
            "Research synthesized autonomously using public open-access repositories and verified web documentation. "
            "No private corporate intranets or restricted commercial databases were accessed."
        )

        return limitations
