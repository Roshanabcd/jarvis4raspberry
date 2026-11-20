"""JARVIS OS — Autonomous Web Scraping Agent (Additive Feature Module #7).

Policy-compliant website data extraction, HTML structure parsing, scheduled
change monitoring, and JSON export for Raspberry Pi 5.
"""

from .config import WebScraperConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["WebScraperConfig", "create_router", "__version__"]
