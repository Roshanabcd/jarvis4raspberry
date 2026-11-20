"""Policy compliance guard: URL validation, SSRF blocking, rate limiting, and robots.txt verification."""

from __future__ import annotations

import ipaddress
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from typing import Dict, Tuple

from .config import WebScraperConfig


class PolicyViolationError(ValueError):
    """Raised when a scraping request violates SSRF, scheme, or robots.txt policy."""


class ScrapePolicyGuard:
    """Enforces safe, polite, policy-compliant HTTP fetching."""

    def __init__(self, config: WebScraperConfig) -> None:
        self.config = config
        self._last_domain_hit: Dict[str, float] = {}
        self._robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def validate_url(self, url: str) -> urllib.parse.ParseResult:
        parsed = urllib.parse.urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            raise PolicyViolationError(f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed.")
        if not parsed.hostname:
            raise PolicyViolationError("URL must include a valid hostname.")

        host = parsed.hostname.lower()
        if not self.config.allow_private_hosts:
            if host in ("localhost", "localhost.localdomain") or host.endswith(".local"):
                raise PolicyViolationError(f"Access to local host '{host}' is blocked by SSRF policy.")
            try:
                ip_obj = ipaddress.ip_address(host)
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                    raise PolicyViolationError(f"Access to private/reserved IP '{host}' is blocked by SSRF policy.")
            except ValueError:
                # Domain name; resolve if possible and check for private IPs
                try:
                    resolved = socket.gethostbyname(host)
                    ip_obj = ipaddress.ip_address(resolved)
                    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                        raise PolicyViolationError(f"Domain '{host}' resolves to blocked private IP '{resolved}'.")
                except OSError:
                    # Offline DNS failure will be handled gracefully during fetch
                    pass
        return parsed

    def check_robots(self, url: str) -> bool:
        if not self.config.respect_robots_txt:
            return True
        parsed = urllib.parse.urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots_cache.get(origin)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = f"{origin}/robots.txt"
            try:
                req = urllib.request.Request(
                    robots_url,
                    headers={"User-Agent": self.config.user_agent},
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=min(5.0, self.config.request_timeout_sec)) as resp:
                    lines = resp.read(128 * 1024).decode("utf-8", errors="replace").splitlines()
                rp.parse(lines)
            except (urllib.error.URLError, TimeoutError, OSError):
                # If robots.txt does not exist (404) or cannot be fetched, default to allow per RFC 9309
                rp.parse([])
            self._robots_cache[origin] = rp
        return rp.can_fetch(self.config.user_agent, url)

    def fetch_html_sync(self, url: str) -> Tuple[str, bool]:
        """Validate policy, respect domain rate limit and robots.txt, and fetch HTML."""
        parsed = self.validate_url(url)
        if not self.check_robots(url):
            raise PolicyViolationError(f"Blocked by robots.txt for User-Agent '{self.config.user_agent}': {url}")

        domain = parsed.netloc.lower()
        now = time.monotonic()
        last = self._last_domain_hit.get(domain, 0.0)
        wait = self.config.min_domain_interval_sec - (now - last)
        if wait > 0:
            time.sleep(min(wait, 5.0))
        self._last_domain_hit[domain] = time.monotonic()

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=self.config.request_timeout_sec) as resp:
            raw = resp.read(self.config.max_response_bytes)
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace"), True
