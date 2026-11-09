"""
JARVIS Browser Controller & YouTube Automation
Launches installed web browsers (Google Chrome, Firefox), opens requested URLs,
and executes YouTube searches with process and window verification.
"""
from __future__ import annotations

import logging
import os
import urllib.parse
from typing import Any, Dict, Optional

from tools.desktop.app_launcher import app_launcher
from tools.desktop.window_manager import window_manager

logger = logging.getLogger("JARVIS-BROWSER-CONTROLLER")


class DesktopBrowserController:
    """Automates web browsing and YouTube navigation through installed browsers."""

    def __init__(self) -> None:
        pass

    def open_url(
        self,
        url: str,
        browser: str = "chrome",
        new_window: bool = True,
    ) -> Dict[str, Any]:
        """Open a URL in Google Chrome, Firefox, or the system default browser."""
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"

        b_norm = browser.lower().strip()
        app_target = "firefox" if "firefox" in b_norm else "chrome"

        res = app_launcher.launch_app(app_target, target=clean_url, new_window=new_window)
        res.update({
            "requested_browser": browser,
            "resolved_browser": app_target,
            "url": clean_url,
        })
        return res

    def search_youtube(
        self,
        query: str,
        browser: str = "chrome",
    ) -> Dict[str, Any]:
        """Search YouTube for video or music in the specified browser."""
        clean_q = query.strip()
        encoded = urllib.parse.quote_plus(clean_q)
        yt_url = f"https://www.youtube.com/results?search_query={encoded}"

        res = self.open_url(yt_url, browser=browser, new_window=True)

        # Truthful report: distinguish browser search page launch from physical audio playback
        res.update({
            "action": "youtube_search",
            "query": clean_q,
            "youtube_url": yt_url,
            "playback_started": False,  # Truthful status: page loaded; physical playback requires user or video selection
            "status_message": f"Opened YouTube search results for '{clean_q}' in {res.get('resolved_browser', browser).title()}.",
        })
        return res


browser_controller = DesktopBrowserController()
