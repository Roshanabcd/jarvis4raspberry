"""
Credibility assessment and date disambiguation engine for JARVIS AI Research Assistant.
Evaluates source authority, categorizes evidence, scores reliability, and disambiguates
publication dates from event dates and retrieval dates.
"""

from __future__ import annotations

import datetime
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional

from apps.research.models import (
    ResearchSource,
    SourceCategory,
)

logger = logging.getLogger("JARVIS-RESEARCH-CREDIBILITY")

# Domain classification patterns
_GOV_DOMAINS = (".gov", ".mil", "who.int", "cdc.gov", "nasa.gov", "nih.gov", "un.org", "europa.eu")
_EDU_DOMAINS = (".edu", ".ac.", "stanford.edu", "mit.edu", "harvard.edu", "cam.ac.uk", "ox.ac.uk", "berkeley.edu")
_DOC_DOMAINS = ("docs.", "developer.", "github.com", "python.org", "w3.org", "kernel.org", "rust-lang.org", "gnu.org")
_NEWS_DOMAINS = ("reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com", "bloomberg.com", "wsj.com", "ft.com")
_ACADEMIC_DOMAINS = ("arxiv.org", "crossref.org", "openalex.org", "nature.com", "science.org", "ieee.org", "acm.org", "springer.com", "sciencedirect.com", "ncbi.nlm.nih.gov", "biorxiv.org", "medrxiv.org")
_COMMUNITY_DOMAINS = ("reddit.com", "stackoverflow.com", "medium.com", "dev.to", "quora.com", "wikipedia.org", "substack.com")

CATEGORY_BASE_WEIGHTS = {
    SourceCategory.GOVERNMENT_SOURCE: 0.95,
    SourceCategory.PEER_REVIEWED_PAPER: 0.95,
    SourceCategory.OFFICIAL_DOCUMENTATION: 0.90,
    SourceCategory.INSTITUTIONAL_SOURCE: 0.88,
    SourceCategory.PRIMARY_SOURCE: 0.92,
    SourceCategory.REPUTABLE_SECONDARY_SOURCE: 0.80,
    SourceCategory.NEWS_SOURCE: 0.75,
    SourceCategory.COMMUNITY_SOURCE: 0.55,
    SourceCategory.UNVERIFIED_SOURCE: 0.40,
}


def classify_category(url: str, title: str = "", metadata: Optional[Dict[str, Any]] = None) -> SourceCategory:
    """Classify the source into a formal SourceCategory."""
    if not url:
        return SourceCategory.UNVERIFIED_SOURCE

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    meta = metadata or {}

    if meta.get("doi") or any(d in domain for d in _ACADEMIC_DOMAINS):
        return SourceCategory.PEER_REVIEWED_PAPER
    if any(domain.endswith(d) or d in domain for d in _GOV_DOMAINS):
        return SourceCategory.GOVERNMENT_SOURCE
    if any(domain.endswith(d) or d in domain for d in _EDU_DOMAINS):
        return SourceCategory.INSTITUTIONAL_SOURCE
    if any(domain.startswith(d) or d in domain for d in _DOC_DOMAINS):
        return SourceCategory.OFFICIAL_DOCUMENTATION
    if any(domain.endswith(d) or d in domain for d in _NEWS_DOMAINS):
        return SourceCategory.NEWS_SOURCE
    if any(domain.endswith(d) or d in domain for d in _COMMUNITY_DOMAINS):
        return SourceCategory.COMMUNITY_SOURCE

    return SourceCategory.REPUTABLE_SECONDARY_SOURCE


def disambiguate_dates(source: ResearchSource) -> Dict[str, Any]:
    """
    Disambiguate publication date, retrieval date, and temporal recency tier.
    Returns:
        dict with publication_date, retrieval_date, recency_tier, and year.
    """
    retrieval_iso = datetime.datetime.fromtimestamp(
        source.retrieved_at, tz=datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%SZ")

    pub_date_str = source.published_date or ""
    parsed_year: Optional[int] = None

    if pub_date_str:
        # Match YYYY or YYYY-MM-DD
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", pub_date_str)
        if year_match:
            try:
                parsed_year = int(year_match.group(1))
            except ValueError:
                pass

    # Fallback: scan content for publication pattern if not set
    if not parsed_year and source.content:
        date_pattern = re.search(r"\b(?:published|posted|date)[:\s]+([A-Za-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})\b", source.content[:2000], re.IGNORECASE)
        if date_pattern:
            found_str = date_pattern.group(1)
            pub_date_str = found_str
            y_m = re.search(r"\b(20\d\d|19\d\d)\b", found_str)
            if y_m:
                parsed_year = int(y_m.group(1))

    current_year = datetime.datetime.now(datetime.timezone.utc).year
    if parsed_year:
        diff = current_year - parsed_year
        if diff <= 1:
            recency = "current"
        elif diff <= 3:
            recency = "recent"
        elif diff <= 7:
            recency = "moderate"
        else:
            recency = "archival"
    else:
        recency = "undated"

    return {
        "publication_date": pub_date_str or None,
        "publication_year": parsed_year,
        "retrieval_date": retrieval_iso,
        "recency_tier": recency,
    }


def assess_credibility(source: ResearchSource) -> Dict[str, Any]:
    """
    Perform deep credibility assessment on a research source.
    Returns credibility score (0.0 - 1.0), factors, and reliability flags.
    """
    cat = classify_category(source.url, source.title, source.raw_metadata)
    source.category = cat
    dates = disambiguate_dates(source)
    if dates["publication_date"] and not source.published_date:
        source.published_date = dates["publication_date"]

    base_score = CATEGORY_BASE_WEIGHTS.get(cat, 0.60)
    adjustments = 0.0
    flags: List[str] = []
    cautions: List[str] = []

    # Factor: Author Attribution
    if source.authors:
        adjustments += 0.05
        flags.append(f"Attributed to {len(source.authors)} author(s)")
    else:
        cautions.append("No named individual authors identified")

    # Factor: DOI / Peer review
    if source.doi:
        adjustments += 0.08
        flags.append(f"Registered persistent identifier (DOI: {source.doi})")

    # Factor: High Citation Count
    if source.citation_count > 50:
        adjustments += 0.07
        flags.append(f"Highly cited ({source.citation_count} citations)")
    elif source.citation_count > 5:
        adjustments += 0.03
        flags.append(f"Cited by {source.citation_count} external publications")

    # Factor: Abstract vs Full text
    if source.is_abstract_only:
        cautions.append("Abstract-only source; full methodology or data tables not retrieved")

    # Factor: Recency
    if dates["recency_tier"] in ("current", "recent"):
        adjustments += 0.03
        flags.append(f"Published recently ({dates.get('publication_year', '')})")
    elif dates["recency_tier"] == "archival":
        cautions.append(f"Historical / archival source ({dates.get('publication_year', '')})")
    elif dates["recency_tier"] == "undated":
        adjustments -= 0.05
        cautions.append("Undated publication; timeliness cannot be verified")

    final_score = min(0.99, max(0.10, base_score + adjustments))

    return {
        "credibility_score": round(final_score, 2),
        "category": cat.value,
        "dates": dates,
        "flags": flags,
        "cautions": cautions,
    }
