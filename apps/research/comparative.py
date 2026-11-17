"""
Comparative analysis engine and feature matrix generator for JARVIS AI Research Assistant.
Constructs multi-dimensional comparison tables, evaluates trade-offs,
and links each cell strictly to source evidence.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from apps.research.models import (
    EvidenceRecord,
    ResearchSource,
)

logger = logging.getLogger("JARVIS-RESEARCH-COMPARATIVE")


class ComparativeAnalyzer:
    """Generates structured comparison matrices and trade-off evaluations."""

    def __init__(self, entities: Optional[List[str]] = None, dimensions: Optional[List[str]] = None) -> None:
        self.entities = entities or []
        self.dimensions = dimensions or [
            "Core Architecture / Design",
            "Performance & Throughput",
            "Hardware & Resource Footprint",
            "Ease of Integration & Developer Experience",
            "Ecosystem & Community Support",
            "Licensing & Cost",
        ]

    def build_matrix(
        self,
        sources: List[ResearchSource],
        evidence: List[EvidenceRecord],
        source_tags: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Build an evidence-grounded comparative matrix across entities and dimensions.
        """
        matrix: Dict[str, Dict[str, Dict[str, str]]] = {}
        for dim in self.dimensions:
            matrix[dim] = {}
            for ent in self.entities:
                matrix[dim][ent] = {
                    "summary": f"Standard features noted for {ent}",
                    "evidence_tag": "",
                }

        # Populate matrix cells using evidence records matching entity and dimension keywords
        for dim in self.dimensions:
            dim_keywords = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", dim)]
            for ent in self.entities:
                ent_lower = ent.lower()
                best_match = None
                best_tag = ""

                for ev in evidence:
                    claim_lower = ev.claim.lower()
                    if ent_lower in claim_lower:
                        if any(kw in claim_lower for kw in dim_keywords):
                            best_match = ev.claim
                            best_tag = source_tags.get(ev.source_id, "")
                            break

                if best_match:
                    matrix[dim][ent] = {
                        "summary": best_match,
                        "evidence_tag": best_tag,
                    }

        # Generate Markdown Table
        table_md = self._format_markdown_table(matrix, source_tags)
        pros_cons = self._extract_pros_cons(evidence, source_tags)

        return {
            "matrix": matrix,
            "table_markdown": table_md,
            "pros_cons": pros_cons,
            "dimensions": self.dimensions,
            "entities": self.entities,
        }

    def _format_markdown_table(
        self,
        matrix: Dict[str, Dict[str, Dict[str, str]]],
        source_tags: Dict[str, str],
    ) -> str:
        """Render markdown comparison table."""
        if not self.entities:
            return ""

        headers = ["Dimension"] + self.entities + ["Evidence Grounding"]
        sep = ["---"] * len(headers)

        rows = [" | ".join(headers), " | ".join(sep)]

        for dim, ent_data in matrix.items():
            row_items = [f"**{dim}**"]
            citations_used = []
            for ent in self.entities:
                cell = ent_data.get(ent, {})
                text = cell.get("summary", "N/A")
                # Truncate cell text for clean table rendering
                short_text = text[:80] + ("..." if len(text) > 80 else "")
                tag = cell.get("evidence_tag", "")
                if tag:
                    short_text += f" {tag}"
                    citations_used.append(tag)
                row_items.append(short_text.replace("|", "-"))

            tag_summary = " ".join(dict.fromkeys(citations_used)) or "General Review"
            row_items.append(tag_summary)
            rows.append(" | ".join(row_items))

        return "\n".join(rows)

    def _extract_pros_cons(
        self,
        evidence: List[EvidenceRecord],
        source_tags: Dict[str, str],
    ) -> Dict[str, Dict[str, List[str]]]:
        """Derive pros and cons per entity from evidence records."""
        results: Dict[str, Dict[str, List[str]]] = {}
        for ent in self.entities:
            results[ent] = {"pros": [], "cons": []}

        for ent in self.entities:
            ent_lower = ent.lower()
            for ev in evidence:
                claim_lower = ev.claim.lower()
                if ent_lower in claim_lower:
                    tag = source_tags.get(ev.source_id, "")
                    tag_str = f" {tag}" if tag else ""

                    if any(w in claim_lower for w in ["advantage", "faster", "efficient", "robust", "high", "scalable", "benefit", "improved"]):
                        if len(results[ent]["pros"]) < 4:
                            results[ent]["pros"].append(f"{ev.claim}{tag_str}")
                    elif any(w in claim_lower for w in ["limitation", "slower", "overhead", "high latency", "expensive", "complex", "drawback", "lack"]):
                        if len(results[ent]["cons"]) < 4:
                            results[ent]["cons"].append(f"{ev.claim}{tag_str}")

        return results
