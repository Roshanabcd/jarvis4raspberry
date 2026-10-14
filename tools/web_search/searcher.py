"""Web search and web scraping tools for JARVIS OS.

Interacts with the DuckDuckGo Instant Answer API, scrapes clean text from web pages,
and provides network connectivity verification. Never fabricates or hallucinates results.
"""

from __future__ import annotations

import html
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional
import requests

from config.config_manager import config

logger = logging.getLogger("JARVIS-WEB-SEARCH")

USER_AGENT = "JARVIS-OS/0.1.0 (Raspberry Pi 5; ARM64 Linux)"


class WebSearcher:
    """Provides genuine web search via DuckDuckGo and clean text page retrieval."""

    DDG_API_URL = "https://api.duckduckgo.com/"

    def __init__(self, timeout: int = 10) -> None:
        """Initialize WebSearcher.

        Args:
            timeout: Default HTTP request timeout in seconds.
        """
        self.default_timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def is_online(self, test_hosts: Optional[List[str]] = None) -> bool:
        """Check active internet connectivity without long blocking.

        Args:
            test_hosts: Optional list of URLs to verify against.

        Returns:
            bool: True if reachable, False otherwise.
        """
        hosts = test_hosts or ["https://1.1.1.1", "https://api.duckduckgo.com"]
        for host in hosts:
            try:
                resp = self.session.head(host, timeout=2.5, allow_redirects=True)
                if resp.status_code < 500:
                    return True
            except (requests.RequestException, OSError):
                continue
        return False

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Perform search using DuckDuckGo Instant Answer API.

        Never fabricates results. Returns real data or empty list.

        Args:
            query: The search term.
            max_results: Max items to return (default 10).

        Returns:
            List of dictionaries with keys: title, url, snippet.
        """
        clean_query = query.strip() if isinstance(query, str) else ""
        if not clean_query:
            return []

        results: List[Dict[str, str]] = []

        params = {
            "q": clean_query,
            "format": "json",
            "no_redirect": "1",
            "no_html": "1",
            "skip_disambig": "0",
        }

        try:
            logger.info(f"Querying DuckDuckGo Instant Answer API for '{clean_query}'")
            resp = self.session.get(self.DDG_API_URL, params=params, timeout=self.default_timeout)
            resp.raise_for_status()
            data = resp.json()

            # 1. Primary Abstract / Answer
            abstract_text = data.get("AbstractText", "").strip()
            abstract_url = data.get("AbstractURL", "").strip()
            heading = data.get("Heading", clean_query).strip()

            if abstract_text:
                results.append({
                    "title": heading,
                    "url": abstract_url,
                    "snippet": abstract_text,
                })

            # 2. Direct Results
            for item in data.get("Results", []):
                if isinstance(item, dict):
                    text = item.get("Text", "").strip()
                    url = item.get("FirstURL", "").strip()
                    if text:
                        results.append({
                            "title": heading,
                            "url": url,
                            "snippet": text,
                        })

            # 3. Related Topics (can be nested or flat)
            def extract_topics(topic_list: List[Any]) -> None:
                for topic in topic_list:
                    if len(results) >= max_results:
                        return
                    if not isinstance(topic, dict):
                        continue
                    if "Topics" in topic and isinstance(topic["Topics"], list):
                        extract_topics(topic["Topics"])
                    else:
                        text = topic.get("Text", "").strip()
                        url = topic.get("FirstURL", "").strip()
                        if text:
                            # Split into approximate title and snippet if formatted as "Title - snippet"
                            parts = text.split(" - ", 1)
                            title = parts[0] if len(parts) > 1 else text[:60]
                            snippet = parts[1] if len(parts) > 1 else text
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                            })

            extract_topics(data.get("RelatedTopics", []))

        except requests.RequestException as exc:
            logger.warning(f"DuckDuckGo search error: {exc}")
        except Exception as exc:
            logger.error(f"Unexpected error during search: {exc}", exc_info=True)

        return results[:max_results]

    def fetch_page(self, url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Fetch a web page and extract clean plain text.

        Args:
            url: Target URL to retrieve.
            timeout: Optional override for request timeout.

        Returns:
            Dictionary containing:
                - url (str)
                - status_code (int)
                - title (str)
                - text (str)
                - error (Optional[str])
        """
        clean_url = url.strip() if isinstance(url, str) else ""
        parsed = urllib.parse.urlparse(clean_url)
        if parsed.scheme not in ("http", "https"):
            return {
                "url": clean_url,
                "status_code": 400,
                "title": "",
                "text": "",
                "error": f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed.",
            }

        req_timeout = timeout or self.default_timeout

        try:
            logger.info(f"Fetching page: {clean_url}")
            resp = self.session.get(clean_url, timeout=req_timeout)
            status_code = resp.status_code

            # Extract title and body text
            content_type = resp.headers.get("Content-Type", "")
            if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
                return {
                    "url": clean_url,
                    "status_code": status_code,
                    "title": "",
                    "text": f"[Non-text content type: {content_type}]",
                    "error": None,
                }

            html_text = resp.text
            title, plain_text = self._extract_clean_text(html_text)

            # Cap output to 50KB to protect Pi 5 RAM
            if len(plain_text) > 50000:
                plain_text = plain_text[:50000] + "\n...[truncated for length]"

            return {
                "url": clean_url,
                "status_code": status_code,
                "title": title,
                "text": plain_text,
                "error": None,
            }
        except requests.Timeout:
            err = f"Request to '{clean_url}' timed out after {req_timeout}s."
            logger.warning(err)
            return {"url": clean_url, "status_code": 408, "title": "", "text": "", "error": err}
        except requests.RequestException as exc:
            err = f"Failed to fetch '{clean_url}': {str(exc)}"
            logger.warning(err)
            return {"url": clean_url, "status_code": 500, "title": "", "text": "", "error": err}

    def _extract_clean_text(self, raw_html: str) -> tuple[str, str]:
        """Strip HTML tags, scripts, and stylesheets, yielding clean text.

        Args:
            raw_html: Raw HTML string.

        Returns:
            tuple[str, str]: (Title string, Clean text body).
        """
        # Extract title
        title_match = re.search(r"(?i)<title[^>]*>(.*?)</title>", raw_html)
        title = html.unescape(title_match.group(1).strip()) if title_match else ""

        # Remove scripts, styles, metadata, svgs, and navigation elements
        cleaned = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw_html)
        cleaned = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", cleaned)
        cleaned = re.sub(r"(?is)<nav[^>]*>.*?</nav>", " ", cleaned)
        cleaned = re.sub(r"(?is)<header[^>]*>.*?</header>", " ", cleaned)
        cleaned = re.sub(r"(?is)<footer[^>]*>.*?</footer>", " ", cleaned)
        cleaned = re.sub(r"(?is)<svg[^>]*>.*?</svg>", " ", cleaned)

        # Replace block breaks with newlines
        cleaned = re.sub(r"(?i)<(br|p|div|h[1-6]|li|tr)[^>]*>", "\n", cleaned)
        # Strip all remaining tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # Unescape entities
        cleaned = html.unescape(cleaned)

        # Normalize whitespace
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        text = "\n".join(lines)
        return title, text


# Global instance
web_searcher = WebSearcher()
