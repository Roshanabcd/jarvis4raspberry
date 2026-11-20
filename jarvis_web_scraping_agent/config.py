"""Environment-driven configuration for JARVIS Autonomous Web Scraping Agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> Path:
    env_db = os.getenv("JARVIS_SCRAPER_DB_PATH")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return (Path.cwd() / ".jarvis_web_scraper" / "web_scraper.db").resolve()


@dataclass(frozen=True)
class WebScraperConfig:
    """Immutable runtime settings for policy-compliant web scraping."""

    db_path: Path = field(default_factory=_default_db_path)
    user_agent: str = field(
        default_factory=lambda: os.getenv(
            "JARVIS_SCRAPER_UA", "JARVIS-OS-WebScraper/1.0 (+https://localhost/jarvis-os)"
        )
    )
    respect_robots_txt: bool = field(
        default_factory=lambda: os.getenv("JARVIS_SCRAPER_RESPECT_ROBOTS", "true").lower()
        in ("1", "true", "yes")
    )
    allow_private_hosts: bool = field(
        default_factory=lambda: os.getenv("JARVIS_SCRAPER_ALLOW_PRIVATE", "false").lower()
        in ("1", "true", "yes")
    )
    request_timeout_sec: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_SCRAPER_TIMEOUT_SEC", "15"))
    )
    max_response_bytes: int = field(
        default_factory=lambda: int(os.getenv("JARVIS_SCRAPER_MAX_BYTES", str(2 * 1024 * 1024)))
    )
    min_domain_interval_sec: float = field(
        default_factory=lambda: float(os.getenv("JARVIS_SCRAPER_RATE_LIMIT_SEC", "1.5"))
    )
