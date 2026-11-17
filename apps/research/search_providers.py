"""
Multi-provider search and academic integrations for JARVIS AI Research Assistant.
Integrates DuckDuckGo, arXiv, Crossref, OpenAlex, and Europe PMC with deduplication,
timeouts, and robust error handling. Never fabricates sources.
"""

from __future__ import annotations

import abc
import html
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional
import uuid
import xml.etree.ElementTree as ET
import requests

from apps.research.models import (
    ExtractionStatus,
    ResearchPlan,
    ResearchQuery,
    ResearchSource,
    ResearchTask,
    SourceCategory,
)

logger = logging.getLogger("JARVIS-RESEARCH-SEARCH")
USER_AGENT = "JARVIS-OS/0.1.0 (Raspberry Pi 5; ARM64 Linux; ResearchAssistant/1.0; mailto:jarvis@local)"


def _clean_text(val: Optional[str]) -> str:
    """Unescape HTML and collapse whitespace."""
    if not val:
        return ""
    text = html.unescape(str(val))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("http://"):
        url = "https://" + url[7:]
    # Remove tracking parameters
    try:
        parsed = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(parsed.query)
        filtered_q = {k: v for k, v in q.items() if not k.startswith("utm_")}
        new_query = urllib.parse.urlencode(filtered_q, doseq=True)
        url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.params,
            new_query,
            "",  # strip fragment
        ))
    except Exception:
        pass
    return url


class BaseSearchProvider(abc.ABC):
    """Abstract base class for all search and discovery providers."""

    def __init__(self, name: str, timeout: int = 8) -> None:
        self.name = name
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    @abc.abstractmethod
    def search(self, query: str, max_results: int = 5, task_id: str = "") -> List[ResearchSource]:
        """Execute search for the given query and return a list of sources."""
        pass


class DuckDuckGoProvider(BaseSearchProvider):
    """Web search provider using DuckDuckGo Instant Answer API and web scrape fallback."""

    DDG_API_URL = "https://api.duckduckgo.com/"
    DDG_HTML_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, timeout: int = 8) -> None:
        super().__init__("web", timeout=timeout)

    def search(self, query: str, max_results: int = 5, task_id: str = "") -> List[ResearchSource]:
        clean_q = _clean_text(query)
        if not clean_q:
            return []

        sources: List[ResearchSource] = []
        seen_urls = set()

        # 1. Query DuckDuckGo Instant Answer API
        try:
            params = {
                "q": clean_q,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "0",
            }
            resp = self.session.get(self.DDG_API_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                abstract_text = _clean_text(data.get("AbstractText", ""))
                abstract_url = data.get("AbstractURL", "").strip()
                heading = _clean_text(data.get("Heading", clean_q))

                if abstract_text and abstract_url and abstract_url not in seen_urls:
                    seen_urls.add(abstract_url)
                    cat = self._categorize_domain(abstract_url)
                    src = ResearchSource(
                        source_id=f"src_{uuid.uuid4().hex[:10]}",
                        task_id=task_id,
                        url=abstract_url,
                        title=heading,
                        authors=[],
                        publisher_or_domain=urllib.parse.urlparse(abstract_url).netloc,
                        category=cat,
                        extraction_status=ExtractionStatus.PARTIAL_CONTENT_RETRIEVED,
                        content=abstract_text,
                        summary=abstract_text[:400],
                        raw_metadata={"provider": "duckduckgo_api", "type": "abstract"},
                    )
                    sources.append(src)

                # Check RelatedTopics
                def parse_topics(topics: List[Any]):
                    for item in topics:
                        if len(sources) >= max_results:
                            return
                        if not isinstance(item, dict):
                            continue
                        if "Topics" in item and isinstance(item["Topics"], list):
                            parse_topics(item["Topics"])
                        else:
                            text = _clean_text(item.get("Text", ""))
                            first_url = item.get("FirstURL", "").strip()
                            if text and first_url and first_url not in seen_urls:
                                seen_urls.add(first_url)
                                parts = text.split(" - ", 1)
                                item_title = parts[0] if len(parts) > 1 else text[:60]
                                item_summary = parts[1] if len(parts) > 1 else text
                                cat = self._categorize_domain(first_url)
                                src = ResearchSource(
                                    source_id=f"src_{uuid.uuid4().hex[:10]}",
                                    task_id=task_id,
                                    url=first_url,
                                    title=item_title,
                                    authors=[],
                                    publisher_or_domain=urllib.parse.urlparse(first_url).netloc,
                                    category=cat,
                                    extraction_status=ExtractionStatus.METADATA_ONLY,
                                    content=item_summary,
                                    summary=item_summary[:400],
                                    raw_metadata={"provider": "duckduckgo_api", "type": "related_topic"},
                                )
                                sources.append(src)

                parse_topics(data.get("RelatedTopics", []))
        except Exception as exc:
            logger.warning(f"DuckDuckGo API search error for '{clean_q}': {exc}")

        # 2. If results < max_results, query DuckDuckGo HTML Lite
        if len(sources) < max_results:
            try:
                html_resp = self.session.post(
                    self.DDG_HTML_URL,
                    data={"q": clean_q, "b": ""},
                    timeout=self.timeout,
                    headers={"User-Agent": USER_AGENT, "Referer": "https://html.duckduckgo.com/"},
                )
                if html_resp.status_code == 200:
                    html_sources = self._parse_ddg_html(html_resp.text, task_id, seen_urls, max_results - len(sources))
                    sources.extend(html_sources)
            except Exception as exc:
                logger.warning(f"DuckDuckGo HTML search error for '{clean_q}': {exc}")

        return sources[:max_results]

    def _parse_ddg_html(self, html_text: str, task_id: str, seen_urls: set, limit: int) -> List[ResearchSource]:
        """Extract links, titles and snippets from DDG HTML results."""
        results: List[ResearchSource] = []
        # Pattern for search results: class="result__title"> <a ... href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>
        pattern = re.compile(
            r'<a[^>]+class="result__url"[^>]+href="(?P<raw_url>[^"]+)"[^>]*>.*?</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )
        # Also try title + snippet regex
        title_snippet_pattern = re.compile(
            r'<h2 class="result__title">\s*<a[^>]+href="(?P<raw_url>[^"]+)"[^>]*>(?P<title>.*?)</a>\s*</h2>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in title_snippet_pattern.finditer(html_text):
            if len(results) >= limit:
                break
            raw_url = match.group("raw_url")
            raw_title = match.group("title")
            raw_snippet = match.group("snippet")

            # Extract actual URL from DDG redirect: /l/?kh=-1&uddg=https%3A%2F%2F...
            clean_url = self._decode_ddg_url(raw_url)
            clean_title = _clean_text(re.sub(r"<[^>]+>", "", raw_title))
            clean_snippet = _clean_text(re.sub(r"<[^>]+>", "", raw_snippet))

            if clean_url and clean_url not in seen_urls and clean_url.startswith("http"):
                seen_urls.add(clean_url)
                cat = self._categorize_domain(clean_url)
                src = ResearchSource(
                    source_id=f"src_{uuid.uuid4().hex[:10]}",
                    task_id=task_id,
                    url=clean_url,
                    title=clean_title or clean_url,
                    authors=[],
                    publisher_or_domain=urllib.parse.urlparse(clean_url).netloc,
                    category=cat,
                    extraction_status=ExtractionStatus.METADATA_ONLY,
                    content=clean_snippet,
                    summary=clean_snippet[:400],
                    raw_metadata={"provider": "duckduckgo_html"},
                )
                results.append(src)

        return results

    @staticmethod
    def _decode_ddg_url(raw_url: str) -> str:
        """Decode DuckDuckGo redirect link."""
        if "uddg=" in raw_url:
            match = re.search(r"uddg=([^&]+)", raw_url)
            if match:
                return urllib.parse.unquote(match.group(1))
        return raw_url

    @staticmethod
    def _categorize_domain(url: str) -> SourceCategory:
        """Categorize source by domain heuristic."""
        domain = urllib.parse.urlparse(url).netloc.lower()
        if any(d in domain for d in [".gov", ".mil", "who.int", "cdc.gov", "nasa.gov", "nih.gov"]):
            return SourceCategory.GOVERNMENT_SOURCE
        if any(d in domain for d in [".edu", ".ac.", "stanford.edu", "mit.edu", "ox.ac.uk", "cam.ac.uk"]):
            return SourceCategory.INSTITUTIONAL_SOURCE
        if any(d in domain for d in ["docs.", "developer.", "github.com", "python.org", "w3.org", "kernel.org"]):
            return SourceCategory.OFFICIAL_DOCUMENTATION
        if any(d in domain for d in ["reuters.com", "apnews.com", "bbc.com", "nytimes.com", "bloomberg.com", "nature.com"]):
            return SourceCategory.NEWS_SOURCE
        if any(d in domain for d in ["reddit.com", "stackoverflow.com", "medium.com", "dev.to", "quora.com", "wikipedia.org"]):
            return SourceCategory.COMMUNITY_SOURCE
        return SourceCategory.REPUTABLE_SECONDARY_SOURCE


class ArxivProvider(BaseSearchProvider):
    """Academic paper search provider using arXiv REST API."""

    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    def __init__(self, timeout: int = 8) -> None:
        super().__init__("arxiv", timeout=timeout)

    def search(self, query: str, max_results: int = 5, task_id: str = "") -> List[ResearchSource]:
        clean_q = _clean_text(query)
        if not clean_q:
            return []

        sources: List[ResearchSource] = []
        try:
            # Query format for arXiv: all:searchTerm
            params = {
                "search_query": f"all:{clean_q}",
                "start": "0",
                "max_results": str(max_results),
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            resp = self.session.get(self.ARXIV_API_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning(f"arXiv API returned status {resp.status_code}")
                return []

            root = ET.fromstring(resp.text)
            entries = root.findall("atom:entry", self.ATOM_NS)
            for entry in entries:
                title_elem = entry.find("atom:title", self.ATOM_NS)
                title = _clean_text(title_elem.text if title_elem is not None else "Untitled Paper")

                id_elem = entry.find("atom:id", self.ATOM_NS)
                url = id_elem.text.strip() if id_elem is not None else ""

                summary_elem = entry.find("atom:summary", self.ATOM_NS)
                abstract = _clean_text(summary_elem.text if summary_elem is not None else "")

                # Authors
                authors = []
                for author_elem in entry.findall("atom:author", self.ATOM_NS):
                    name_elem = author_elem.find("atom:name", self.ATOM_NS)
                    if name_elem is not None and name_elem.text:
                        authors.append(_clean_text(name_elem.text))

                # Publication Date
                pub_elem = entry.find("atom:published", self.ATOM_NS)
                published_date = None
                if pub_elem is not None and pub_elem.text:
                    # e.g. 2024-03-15T18:00:00Z -> 2024-03-15
                    published_date = pub_elem.text[:10]

                # DOI & PDF Link
                doi = None
                doi_elem = entry.find("arxiv:doi", self.ATOM_NS)
                if doi_elem is not None and doi_elem.text:
                    doi = doi_elem.text.strip()

                pdf_link = ""
                for link in entry.findall("atom:link", self.ATOM_NS):
                    if link.attrib.get("title") == "pdf":
                        pdf_link = link.attrib.get("href", "")
                        break

                src = ResearchSource(
                    source_id=f"src_{uuid.uuid4().hex[:10]}",
                    task_id=task_id,
                    url=pdf_link or url,
                    title=title,
                    authors=authors,
                    publisher_or_domain="arxiv.org",
                    published_date=published_date,
                    category=SourceCategory.PEER_REVIEWED_PAPER,
                    extraction_status=ExtractionStatus.ABSTRACT_ONLY,
                    content=abstract,
                    summary=abstract[:400],
                    doi=doi,
                    is_abstract_only=True,
                    raw_metadata={
                        "provider": "arxiv",
                        "arxiv_id": url,
                        "pdf_url": pdf_link,
                    },
                )
                sources.append(src)

        except Exception as exc:
            logger.warning(f"arXiv search error for '{clean_q}': {exc}")

        return sources[:max_results]


class CrossrefProvider(BaseSearchProvider):
    """Academic paper and DOI metadata search provider using Crossref REST API."""

    CROSSREF_API_URL = "https://api.crossref.org/works"

    def __init__(self, timeout: int = 8) -> None:
        super().__init__("crossref", timeout=timeout)

    def search(self, query: str, max_results: int = 5, task_id: str = "") -> List[ResearchSource]:
        clean_q = _clean_text(query)
        if not clean_q:
            return []

        sources: List[ResearchSource] = []
        try:
            params = {
                "query": clean_q,
                "rows": str(max_results),
                "select": "DOI,title,author,issued,publisher,container-title,abstract,URL,is-referenced-by-count",
            }
            resp = self.session.get(self.CROSSREF_API_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning(f"Crossref API returned status {resp.status_code}")
                return []

            data = resp.json()
            items = data.get("message", {}).get("items", [])
            for item in items:
                titles = item.get("title", [])
                title = _clean_text(titles[0] if titles else "Untitled Scholarly Work")

                doi = item.get("DOI")
                url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

                # Authors
                authors = []
                for auth in item.get("author", []):
                    if "family" in auth:
                        given = auth.get("given", "")
                        authors.append(f"{given} {auth['family']}".strip())
                    elif "name" in auth:
                        authors.append(auth["name"].strip())

                # Published date
                published_date = None
                issued_parts = item.get("issued", {}).get("date-parts", [[]])
                if issued_parts and issued_parts[0]:
                    parts = issued_parts[0]
                    year = parts[0]
                    month = f"{parts[1]:02d}" if len(parts) > 1 else "01"
                    day = f"{parts[2]:02d}" if len(parts) > 2 else "01"
                    published_date = f"{year}-{month}-{day}" if len(parts) > 1 else str(year)

                publisher = item.get("publisher", "")
                container = item.get("container-title", [])
                container_title = container[0] if container else publisher

                abstract = _clean_text(item.get("abstract", ""))
                citations = item.get("is-referenced-by-count", 0)

                src = ResearchSource(
                    source_id=f"src_{uuid.uuid4().hex[:10]}",
                    task_id=task_id,
                    url=url,
                    title=title,
                    authors=authors,
                    publisher_or_domain=container_title or "crossref.org",
                    published_date=published_date,
                    category=SourceCategory.PEER_REVIEWED_PAPER,
                    extraction_status=ExtractionStatus.ABSTRACT_ONLY if abstract else ExtractionStatus.METADATA_ONLY,
                    content=abstract or f"Published in {container_title} ({published_date}). DOI: {doi}",
                    summary=abstract[:400] if abstract else f"Scholarly publication: {title}",
                    doi=doi,
                    is_abstract_only=True,
                    citation_count=citations,
                    raw_metadata={"provider": "crossref", "doi": doi},
                )
                sources.append(src)

        except Exception as exc:
            logger.warning(f"Crossref search error for '{clean_q}': {exc}")

        return sources[:max_results]


class OpenAlexProvider(BaseSearchProvider):
    """Open science bibliographic search provider using OpenAlex REST API."""

    OPENALEX_API_URL = "https://api.openalex.org/works"

    def __init__(self, timeout: int = 8) -> None:
        super().__init__("openalex", timeout=timeout)

    def search(self, query: str, max_results: int = 5, task_id: str = "") -> List[ResearchSource]:
        clean_q = _clean_text(query)
        if not clean_q:
            return []

        sources: List[ResearchSource] = []
        try:
            params = {
                "search": clean_q,
                "per_page": str(max_results),
            }
            resp = self.session.get(self.OPENALEX_API_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning(f"OpenAlex API returned status {resp.status_code}")
                return []

            data = resp.json()
            items = data.get("results", [])
            for item in items:
                title = _clean_text(item.get("display_name", "Untitled Work"))
                doi = item.get("doi")
                landing_url = item.get("primary_location", {}).get("landing_page_url") or doi or item.get("id", "")

                # Authors
                authors = []
                for authorship in item.get("authorships", []):
                    auth_name = authorship.get("author", {}).get("display_name")
                    if auth_name:
                        authors.append(_clean_text(auth_name))

                pub_date = item.get("publication_date") or str(item.get("publication_year", ""))
                citations = item.get("cited_by_count", 0)

                # Reconstruct abstract from inverted index if present
                abstract = ""
                inv_index = item.get("abstract_inverted_index")
                if inv_index and isinstance(inv_index, dict):
                    abstract = self._reconstruct_abstract(inv_index)

                src = ResearchSource(
                    source_id=f"src_{uuid.uuid4().hex[:10]}",
                    task_id=task_id,
                    url=landing_url,
                    title=title,
                    authors=authors,
                    publisher_or_domain="openalex.org",
                    published_date=pub_date,
                    category=SourceCategory.PEER_REVIEWED_PAPER,
                    extraction_status=ExtractionStatus.ABSTRACT_ONLY if abstract else ExtractionStatus.METADATA_ONLY,
                    content=abstract or f"OpenAlex record for: {title}. Cited by {citations}.",
                    summary=abstract[:400] if abstract else f"Scholarly record: {title}",
                    doi=doi.replace("https://doi.org/", "") if doi else None,
                    is_abstract_only=True,
                    citation_count=citations,
                    raw_metadata={"provider": "openalex", "openalex_id": item.get("id")},
                )
                sources.append(src)

        except Exception as exc:
            logger.warning(f"OpenAlex search error for '{clean_q}': {exc}")

        return sources[:max_results]

    @staticmethod
    def _reconstruct_abstract(inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct plain abstract text from OpenAlex word position inverted index."""
        try:
            positions: List[tuple[int, str]] = []
            for word, pos_list in inverted_index.items():
                for p in pos_list:
                    positions.append((p, word))
            positions.sort(key=lambda x: x[0])
            return _clean_text(" ".join(w for _, w in positions))
        except Exception:
            return ""


class EuropePmcProvider(BaseSearchProvider):
    """Biomedical and life sciences scholarly search provider using Europe PMC REST API."""

    EPMC_API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def __init__(self, timeout: int = 8) -> None:
        super().__init__("europepmc", timeout=timeout)

    def search(self, query: str, max_results: int = 5, task_id: str = "") -> List[ResearchSource]:
        clean_q = _clean_text(query)
        if not clean_q:
            return []

        sources: List[ResearchSource] = []
        try:
            params = {
                "query": clean_q,
                "format": "json",
                "pageSize": str(max_results),
                "resultType": "core",
            }
            resp = self.session.get(self.EPMC_API_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning(f"Europe PMC returned status {resp.status_code}")
                return []

            data = resp.json()
            items = data.get("resultList", {}).get("result", [])
            for item in items:
                title = _clean_text(item.get("title", "Untitled Biomedical Paper"))
                doi = item.get("doi")
                pmid = item.get("pmid")
                url = f"https://doi.org/{doi}" if doi else (f"https://europepmc.org/article/MED/{pmid}" if pmid else "")

                author_str = item.get("authorString", "")
                authors = [_clean_text(a) for a in author_str.split(", ") if a.strip()]

                pub_year = item.get("pubYear", "")
                journal = item.get("journalTitle", "Europe PMC")
                abstract = _clean_text(item.get("abstractText", ""))
                citations = int(item.get("citedByCount", 0))

                src = ResearchSource(
                    source_id=f"src_{uuid.uuid4().hex[:10]}",
                    task_id=task_id,
                    url=url,
                    title=title,
                    authors=authors,
                    publisher_or_domain=journal,
                    published_date=str(pub_year),
                    category=SourceCategory.PEER_REVIEWED_PAPER,
                    extraction_status=ExtractionStatus.ABSTRACT_ONLY if abstract else ExtractionStatus.METADATA_ONLY,
                    content=abstract or f"Published in {journal} ({pub_year}). DOI: {doi}",
                    summary=abstract[:400] if abstract else title,
                    doi=doi,
                    is_abstract_only=True,
                    citation_count=citations,
                    raw_metadata={"provider": "europepmc", "pmid": pmid},
                )
                sources.append(src)

        except Exception as exc:
            logger.warning(f"Europe PMC search error for '{clean_q}': {exc}")

        return sources[:max_results]


class SearchDispatcher:
    """Coordinates and routes queries across search providers with deduplication."""

    def __init__(self, timeout: int = 8) -> None:
        self.providers: Dict[str, BaseSearchProvider] = {
            "web": DuckDuckGoProvider(timeout=timeout),
            "arxiv": ArxivProvider(timeout=timeout),
            "crossref": CrossrefProvider(timeout=timeout),
            "openalex": OpenAlexProvider(timeout=timeout),
            "europepmc": EuropePmcProvider(timeout=timeout),
        }

    def search_query(self, query: ResearchQuery, task_id: str = "", limit: int = 5) -> List[ResearchSource]:
        """Execute a single ResearchQuery against appropriate providers."""
        target = query.target_provider.lower().strip()
        provider = self.providers.get(target)

        if provider:
            results = provider.search(query.query_text, max_results=limit, task_id=task_id)
        elif target in ("academic", "scholar"):
            # Query academic providers
            results = []
            for key in ("arxiv", "crossref", "europepmc"):
                sub_res = self.providers[key].search(query.query_text, max_results=max(2, limit // 2), task_id=task_id)
                results.extend(sub_res)
        else:
            # "auto" or general: query web and crossref/arxiv
            web_res = self.providers["web"].search(query.query_text, max_results=max(3, limit - 2), task_id=task_id)
            acad_res = self.providers["crossref"].search(query.query_text, max_results=2, task_id=task_id)
            results = web_res + acad_res

        query.executed = True
        query.results_count = len(results)
        return results

    def search_plan(self, plan: ResearchPlan, task: ResearchTask) -> List[ResearchSource]:
        """Execute all queries in a ResearchPlan with deduplication and source limits."""
        all_sources: List[ResearchSource] = []
        seen_urls = set()
        seen_titles = set()
        seen_dois = set()

        max_sources = task.max_sources or plan.source_limits or 10

        for query in plan.planned_queries:
            if len(all_sources) >= max_sources:
                break

            remaining = max_sources - len(all_sources)
            fetch_limit = min(remaining + 2, 5)
            new_sources = self.search_query(query, task_id=task.task_id, limit=fetch_limit)

            for src in new_sources:
                norm_url = _normalize_url(src.url)
                norm_title = re.sub(r"[^a-z0-9]", "", src.title.lower())
                doi = src.doi.lower().strip() if src.doi else ""

                if norm_url and norm_url in seen_urls:
                    continue
                if doi and doi in seen_dois:
                    continue
                if len(norm_title) > 15 and norm_title in seen_titles:
                    continue

                if norm_url:
                    seen_urls.add(norm_url)
                if doi:
                    seen_dois.add(doi)
                if norm_title:
                    seen_titles.add(norm_title)

                all_sources.append(src)
                if len(all_sources) >= max_sources:
                    break

        return all_sources
