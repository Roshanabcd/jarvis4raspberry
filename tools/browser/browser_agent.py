"""
JARVIS Real Browser Agent.
Controls Google Chrome and Firefox on native X11 DISPLAY=:0,
preserves user profiles and authenticated sessions, performs tab management,
window activation, keyboard navigation, and DOM text extraction.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-BROWSER-AGENT")


class BrowserAgent:
    """Controls installed web browsers with profile preservation on Linux X11."""

    def __init__(self, display: str = ":0") -> None:
        self.display = display
        self._last_opened_url: Optional[str] = None
        self._last_browser: str = "chrome"

    def _get_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env["DISPLAY"] = self.display
        return env

    def find_browser_windows(self, browser: str = "chrome") -> List[Dict[str, Any]]:
        """Find active browser windows in the X11 session using wmctrl."""
        target_name = "chrome" if "chrome" in browser.lower() else "firefox"
        windows = []

        try:
            res = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                env=self._get_env(),
                timeout=3,
                check=False,
            )
            for line in res.stdout.splitlines():
                parts = line.split(maxsplit=3)
                if len(parts) >= 4:
                    win_id = parts[0]
                    desktop = parts[1]
                    host = parts[2]
                    title = parts[3]

                    title_lower = title.lower()
                    if target_name in title_lower or ("google" in title_lower and target_name == "chrome"):
                        windows.append({
                            "window_id": win_id,
                            "desktop": desktop,
                            "host": host,
                            "title": title,
                            "browser": target_name,
                        })
        except Exception as e:
            logger.error("Failed to list browser windows: %s", e)

        return windows

    def activate_window(self, window_id_or_title: str) -> bool:
        """Bring browser window to foreground and focus it."""
        try:
            if window_id_or_title.startswith("0x"):
                cmd = ["wmctrl", "-i", "-a", window_id_or_title]
            else:
                cmd = ["wmctrl", "-a", window_id_or_title]

            res = subprocess.run(cmd, env=self._get_env(), timeout=2, check=False)
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to activate window: %s", e)
            return False

    def open_url(
        self,
        url: str,
        browser: str = "chrome",
        new_tab: bool = False,
        new_window: bool = False,
    ) -> Dict[str, Any]:
        """Open a URL in Google Chrome or Firefox, preserving existing profile and sessions."""
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://", "about:", "chrome://")):
            clean_url = f"https://{clean_url}"

        b_norm = browser.lower().strip()
        is_chrome = "chrome" in b_norm or "chromium" in b_norm
        bin_name = "google-chrome" if is_chrome else "firefox"
        bin_path = shutil.which(bin_name) or shutil.which("chromium-browser") or shutil.which("firefox")

        if not bin_path:
            return {"status": "error", "message": f"Browser binary '{bin_name}' not found on system."}

        # Build launch arguments preserving user profile
        args = [bin_path]
        if new_window:
            args.append("--new-window")
        args.append(clean_url)

        try:
            proc = subprocess.Popen(
                args,
                env=self._get_env(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
            )

            self._last_opened_url = clean_url
            self._last_browser = "chrome" if is_chrome else "firefox"

            # Allow window manager to register new tab / window
            time.sleep(0.8)

            # Bring to focus
            win_match = "Google Chrome" if is_chrome else "Mozilla Firefox"
            self.activate_window(win_match)

            return {
                "status": "ok",
                "browser": "chrome" if is_chrome else "firefox",
                "binary": bin_path,
                "url": clean_url,
                "pid": proc.pid,
                "message": f"Opened {clean_url} in {bin_name}.",
            }
        except Exception as e:
            logger.error("Failed to open browser URL: %s", e)
            return {"status": "error", "message": f"Failed to launch browser: {e}"}

    def send_shortcut(self, key_combination: str, browser: str = "chrome") -> Dict[str, Any]:
        """Send a keyboard shortcut to the active browser window via xdotool."""
        wins = self.find_browser_windows(browser)
        if not wins:
            return {"status": "error", "message": f"No active {browser.title()} window found."}

        win_id = wins[0]["window_id"]
        try:
            # Activate window first
            self.activate_window(win_id)
            time.sleep(0.1)

            res = subprocess.run(
                ["xdotool", "key", "--window", win_id, key_combination],
                env=self._get_env(),
                timeout=3,
                check=False,
            )
            return {
                "status": "ok" if res.returncode == 0 else "error",
                "shortcut": key_combination,
                "window_id": win_id,
            }
        except Exception as e:
            logger.error("Shortcut error: %s", e)
            return {"status": "error", "message": str(e)}

    def go_back(self, browser: str = "chrome") -> Dict[str, Any]:
        """Navigate browser back (Alt+Left)."""
        res = self.send_shortcut("alt+Left", browser)
        res["action"] = "go_back"
        return res

    def go_forward(self, browser: str = "chrome") -> Dict[str, Any]:
        """Navigate browser forward (Alt+Right)."""
        res = self.send_shortcut("alt+Right", browser)
        res["action"] = "go_forward"
        return res

    def reload(self, browser: str = "chrome") -> Dict[str, Any]:
        """Reload active browser page (Ctrl+r)."""
        res = self.send_shortcut("ctrl+r", browser)
        res["action"] = "reload"
        return res

    def switch_tab(self, tab_num: int = 1, browser: str = "chrome") -> Dict[str, Any]:
        """Switch to tab number 1..9 (Ctrl+N) or next tab."""
        t_num = max(1, min(9, int(tab_num)))
        res = self.send_shortcut(f"ctrl+{t_num}", browser)
        res["action"] = "switch_tab"
        res["tab"] = t_num
        return res

    def close_tab(self, browser: str = "chrome") -> Dict[str, Any]:
        """Close active browser tab (Ctrl+w)."""
        res = self.send_shortcut("ctrl+w", browser)
        res["action"] = "close_tab"
        return res

    def scroll(self, direction: str = "down", browser: str = "chrome") -> Dict[str, Any]:
        """Scroll page up or down using Page_Down / Page_Up."""
        key = "Page_Down" if "down" in direction.lower() else "Page_Up"
        res = self.send_shortcut(key, browser)
        res["action"] = f"scroll_{direction}"
        return res


browser_agent = BrowserAgent()
