"""
Search Manager for JARVIS OS.
Provides organic web search result parsing, ranked result extraction,
conversational search session state, and numbered website opening.
"""
from __future__ import annotations

import logging
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-SEARCH-MANAGER")


class SearchRecord:
    """Individual organic search result."""

    def __init__(self, rank: int, title: str, domain: str, url: str, snippet: str = ""):
        self.rank = rank
        self.title = title
        self.domain = domain
        self.url = url
        self.snippet = snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "title": self.title,
            "domain": self.domain,
            "url": self.url,
            "snippet": self.snippet,
        }


class SearchSession:
    """Stores active search context to resolve numbered follow-up requests."""

    def __init__(self, query: str, search_type: str = "web"):
        self.query = query
        self.search_type = search_type
        self.results: List[SearchRecord] = []
        self.created_at = time.time()
        self.active_index: Optional[int] = None
        self.opened_urls: List[str] = []

    def add_result(self, record: SearchRecord) -> None:
        self.results.append(record)

    def get_by_index(self, index: int) -> Optional[SearchRecord]:
        """Index can be 1-based (1..len for natural language) or 0-based (0..len-1)."""
        if index == 0 and len(self.results) > 0:
            return self.results[0]
        if 1 <= index <= len(self.results):
            return self.results[index - 1]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "search_type": self.search_type,
            "total_results": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "active_index": self.active_index,
            "opened_urls": self.opened_urls,
            "created_at": self.created_at,
        }


class SearchManager:
    """Performs web searches, manages search memory, and facilitates numbered navigation."""

    def __init__(self) -> None:
        self._current_session: Optional[SearchSession] = None
        self._last_search_time: float = 0.0

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Return the current search session dictionary if available."""
        if self._current_session:
            return self._current_session.to_dict()
        return None

    def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Perform an organic web search, record session, and return ranked results.
        
        Args:
            query: The search keywords
            max_results: Max organic results to return
        """
        clean_q = query.strip()
        if not clean_q:
            return {"status": "error", "message": "Search query cannot be empty"}

        logger.info("Executing web search for: '%s'", clean_q)
        results = self._fetch_organic_results(clean_q, max_results=max_results)

        session = SearchSession(query=clean_q, search_type="web")
        for r in results:
            session.add_result(r)

        self._current_session = session
        self._last_search_time = time.time()

        formatted_lines = []
        for r in results:
            formatted_lines.append(f"{r.rank}. [{r.domain}] {r.title}\n   {r.url}")

        summary = f"Found {len(results)} organic results for '{clean_q}':\n" + "\n".join(formatted_lines)

        return {
            "status": "ok",
            "query": clean_q,
            "count": len(results),
            "results": [r.to_dict() for r in results],
            "formatted_summary": summary,
        }

    def _fetch_organic_results(self, query: str, max_results: int = 10) -> List[SearchRecord]:
        """Fetch organic search results via DuckDuckGo Lite HTML without third-party dependencies."""
        records: List[SearchRecord] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        post_data = urllib.parse.urlencode({"q": query}).encode("utf-8")

        try:
            req = urllib.request.Request(
                "https://lite.duckduckgo.com/lite/",
                data=post_data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                html_text = response.read().decode("utf-8", errors="ignore")

            # Extract result links and snippets
            # DuckDuckGo Lite format:
            # <tr><td valign="top">&nbsp;1.&nbsp;</td><td><a rel="nofollow" href="..." class='result-link'>Title</a>...
            # <td class='result-snippet'>Snippet text...</td>
            link_pattern = re.compile(
                r"<a[^>]+class=[\'\"]result-link[\'\"][^>]*href=[\'\"]([^\'\"]+)[\'\"][^>]*>(.*?)</a>|"
                r"<a[^>]+href=[\'\"]([^\'\"]+)[\'\"][^>]*class=[\'\"]result-link[\'\"][^>]*>(.*?)</a>",
                re.IGNORECASE | re.DOTALL,
            )

            # Match snippet cells
            snippets = re.findall(r"<td[^>]+class=[\'\"]result-snippet[\'\"][^>]*>(.*?)</td>", html_text, re.IGNORECASE | re.DOTALL)

            matches = link_pattern.findall(html_text)
            rank = 1

            for idx, m in enumerate(matches):
                if rank > max_results:
                    break
                raw_href = m[0] or m[2]
                raw_title = m[1] or m[3]

                if not raw_href or not raw_title:
                    continue

                # Unescape and clean title
                clean_title = re.sub(r"<[^>]+>", "", raw_title).strip()
                clean_title = urllib.parse.unquote(clean_title)

                # Resolve actual URL from DuckDuckGo redirect uddg parameter
                actual_url = raw_href
                if "uddg=" in raw_href:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    if "uddg" in qs:
                        actual_url = qs["uddg"][0]
                elif raw_href.startswith("//"):
                    actual_url = "https:" + raw_href

                # Extract domain
                domain = urllib.parse.urlparse(actual_url).netloc or "web"

                # Filter internal/ad redirects
                if "duckduckgo.com" in domain and "uddg=" not in raw_href:
                    continue

                # Snippet if available
                snippet_text = ""
                if idx < len(snippets):
                    snippet_text = re.sub(r"<[^>]+>", "", snippets[idx]).strip()

                records.append(SearchRecord(
                    rank=rank,
                    title=clean_title,
                    domain=domain,
                    url=actual_url,
                    snippet=snippet_text,
                ))
                rank += 1

        except Exception as e:
            logger.error("Error fetching organic search results: %s", e)

        return records

    def open_result_by_index(
        self,
        index: int,
        new_tab: bool = False,
        browser: str = "chrome",
    ) -> Dict[str, Any]:
        """Open a numbered search result from the current search session.
        
        Args:
            index: 0-based or 1-based index (e.g. 1st result = 1 or 0)
            new_tab: Whether to open in new tab or reuse window
            browser: 'chrome' or 'firefox'
        """
        if not self._current_session:
            return {
                "status": "error",
                "message": "No active search session found. Please perform a search first (e.g. 'Search Google for ...').",
            }

        target = self._current_session.get_by_index(index)
        if not target:
            total = len(self._current_session.results)
            return {
                "status": "error",
                "message": f"Result index {index} is out of bounds. The current search only has {total} results.",
            }

        # Use browser_agent to open the verified URL
        from tools.browser.browser_agent import browser_agent
        nav_res = browser_agent.open_url(target.url, browser=browser, new_tab=new_tab)

        self._current_session.active_index = target.rank - 1
        self._current_session.opened_urls.append(target.url)

        return {
            "status": "ok",
            "rank": target.rank,
            "title": target.title,
            "domain": target.domain,
            "url": target.url,
            "snippet": target.snippet,
            "navigation": nav_res,
            "message": f"Opened result #{target.rank}: '{target.title}' ({target.domain}) in {browser.title()}.",
        }

    def summarize_page(self, url: str, max_words: int = 150) -> Dict[str, Any]:
        """Fetch and summarize clean textual content of a web page."""
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"

        try:
            req = urllib.request.Request(
                clean_url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) JARVIS-OS/1.0"},
            )
            with urllib.request.urlopen(req, timeout=7) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")

            # Remove scripts, styles, comments
            cleaned = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", cleaned)
            text = re.sub(r"\s+", " ", text).strip()

            words = text.split()
            summary = " ".join(words[:max_words])
            if len(words) > max_words:
                summary += "..."

            return {
                "status": "ok",
                "url": clean_url,
                "summary": summary,
                "word_count": len(words),
            }
        except Exception as e:
            return {"status": "error", "url": clean_url, "message": f"Could not extract page text: {e}"}


search_manager = SearchManager()
