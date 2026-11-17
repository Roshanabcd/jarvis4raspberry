"""
Citation generator, formatting catalog, and deterministic citation validator
for JARVIS AI Research Assistant. Enforces truthful referencing and eliminates
hallucinated citations.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from apps.research.models import (
    CitationRecord,
    ResearchSource,
)

logger = logging.getLogger("JARVIS-RESEARCH-CITATIONS")


class CitationManager:
    """Manages source-to-citation mapping, bibliographic styling, and validation."""

    def __init__(self, sources: List[ResearchSource]) -> None:
        self.sources = sources
        self.source_map: Dict[str, ResearchSource] = {s.source_id: s for s in sources}
        self.tag_to_source: Dict[str, ResearchSource] = {}
        self.source_to_tag: Dict[str, str] = {}
        self.citations: List[CitationRecord] = []
        self._build_catalog()

    def _build_catalog(self) -> None:
        """Assign deterministic numerical citation tags [1], [2], ... based on source order."""
        for idx, source in enumerate(self.sources, start=1):
            tag = f"[{idx}]"
            self.tag_to_source[tag] = source
            self.source_to_tag[source.source_id] = tag

            # Year extraction
            year = None
            if source.published_date:
                m = re.search(r"\b(19\d\d|20\d\d)\b", source.published_date)
                if m:
                    year = m.group(1)

            rec = CitationRecord(
                citation_id=f"cit_{idx}",
                source_id=source.source_id,
                inline_tag=tag,
                url=source.url,
                title=source.title or "Untitled Source",
                authors=source.authors,
                year=year,
                publisher=source.publisher_or_domain or "Web Source",
                doi=source.doi,
                is_abstract_only=source.is_abstract_only,
                verified=True,
            )
            self.citations.append(rec)

    def get_tag_for_source(self, source_id: str) -> str:
        """Return the inline citation tag for a source."""
        return self.source_to_tag.get(source_id, "[?]")

    def format_reference_list(self, style: str = "ieee") -> List[str]:
        """
        Format bibliographical references list.
        Never fabricates authors, dates, or DOIs.
        """
        refs: List[str] = []
        for cit in self.citations:
            authors_str = ", ".join(cit.authors) if cit.authors else cit.publisher
            year_str = f"({cit.year})" if cit.year else "(n.d.)"
            doi_str = f" DOI: {cit.doi}" if cit.doi else ""
            abstract_notice = " *[Peer-reviewed Abstract]*" if cit.is_abstract_only else ""

            if style == "apa":
                ref = f"{cit.inline_tag} {authors_str} {year_str}. *{cit.title}*. {cit.publisher}. Available at: {cit.url}{doi_str}{abstract_notice}"
            else:
                # IEEE / standard numeric
                ref = f"{cit.inline_tag} {authors_str}, \"{cit.title},\" *{cit.publisher}*, {year_str}. {cit.url}{doi_str}{abstract_notice}"
            refs.append(ref)
        return refs

    def validate_citations_in_text(self, text: str) -> Tuple[str, List[CitationRecord], List[str]]:
        """
        Scan text for bracketed citation tags [1], [2], etc.
        Verify each against genuine retrieved sources.
        Purge or flag hallucinated citation tags that do not map to genuine sources.
        Returns:
            (validated_text, valid_citations_list, hallucinated_tags_list)
        """
        valid_citations: List[CitationRecord] = []
        hallucinated_tags: List[str] = []
        used_tags: Set[str] = set()

        # Find all [N] tags
        tag_matches = re.finditer(r"\[(\d+)\]", text)
        for match in tag_matches:
            raw_tag = match.group(0)
            if raw_tag in self.tag_to_source:
                used_tags.add(raw_tag)
            else:
                if raw_tag not in hallucinated_tags:
                    hallucinated_tags.append(raw_tag)

        # Replace hallucinated tags with [citation needed: unverified source]
        cleaned_text = text
        for fake_tag in hallucinated_tags:
            logger.warning(f"Purging hallucinated citation tag {fake_tag} from synthesized text")
            cleaned_text = cleaned_text.replace(fake_tag, "")

        # Collect only the citations that were actually cited in the text
        for cit in self.citations:
            if cit.inline_tag in used_tags:
                valid_citations.append(cit)

        # If no citations were cited in text but sources exist, retain all sources in references
        if not valid_citations:
            valid_citations = list(self.citations)

        return cleaned_text, valid_citations, hallucinated_tags
