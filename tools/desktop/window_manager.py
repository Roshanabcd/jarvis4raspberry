"""
JARVIS Desktop Window Manager & Screen Awareness
Uses native X11 tools (wmctrl, xdotool) to inspect open windows, query active
window titles and process IDs, and switch windows.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-WINDOW-MANAGER")


class DesktopWindowManager:
    """Provides screen and active window awareness using native X11 utilities."""

    def __init__(self, display: str = ":0") -> None:
        self.display = display

    def _run_cmd(self, cmd: List[str]) -> str:
        env = os.environ.copy()
        env["DISPLAY"] = self.display
        try:
            res = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=4,
            )
            return res.stdout.strip()
        except Exception as e:
            logger.debug(f"Command {' '.join(cmd)} failed: {e}")
            return ""

    def get_active_window(self) -> Dict[str, Any]:
        """Query currently active X11 window title, ID, and class."""
        win_id = self._run_cmd(["xdotool", "getactivewindow"])
        if not win_id:
            return {"active": False, "title": "No active window", "window_id": None}

        title = self._run_cmd(["xdotool", "getactivewindow", "getwindowname"])
        win_pid = self._run_cmd(["xdotool", "getactivewindow", "getwindowpid"])
        win_class = self._run_cmd(["xdotool", "getactivewindow", "getwindowclassname"])

        return {
            "active": True,
            "window_id": win_id,
            "title": title or "Unknown",
            "pid": int(win_pid) if win_pid.isdigit() else None,
            "class_name": win_class or "Unknown",
        }

    def list_open_windows(self) -> List[Dict[str, Any]]:
        """List all open top-level windows via wmctrl."""
        raw = self._run_cmd(["wmctrl", "-l", "-p", "-G"])
        if not raw:
            return []

        windows = []
        for line in raw.splitlines():
            parts = line.split(None, 8)
            if len(parts) >= 9:
                win_hex = parts[0]
                desktop = parts[1]
                pid = int(parts[2]) if parts[2].isdigit() else None
                x = int(parts[3]) if parts[3].isdigit() else 0
                y = int(parts[4]) if parts[4].isdigit() else 0
                w = int(parts[5]) if parts[5].isdigit() else 0
                h = int(parts[6]) if parts[6].isdigit() else 0
                host = parts[7]
                title = parts[8].strip()

                # Skip system background windows like desktop panel or desktop icon manager if requested
                windows.append({
                    "window_id": win_hex,
                    "desktop": desktop,
                    "pid": pid,
                    "geometry": {"x": x, "y": y, "width": w, "height": h},
                    "title": title,
                })
        return windows

    def switch_window(self, query: str) -> Dict[str, Any]:
        """Switch focus to a window matching query string."""
        q_clean = query.strip()
        res = self._run_cmd(["wmctrl", "-a", q_clean])
        # Verify active window after switch
        active = self.get_active_window()
        success = q_clean.lower() in (active.get("title") or "").lower()
        return {
            "query": query,
            "success": success,
            "active_window": active,
        }

    def get_desktop_status(self) -> Dict[str, Any]:
        """Return comprehensive desktop environment summary."""
        active = self.get_active_window()
        windows = self.list_open_windows()

        # Resolution check
        res_raw = self._run_cmd(["xdpyinfo"])
        resolution = "Unknown"
        m = re.search(r"dimensions:\s+(\d+x\d+)\s+pixels", res_raw)
        if m:
            resolution = m.group(1)

        return {
            "session_type": os.environ.get("XDG_SESSION_TYPE", "x11"),
            "display": self.display,
            "resolution": resolution,
            "active_window": active,
            "open_window_count": len(windows),
            "open_windows": windows[:10],
        }


window_manager = DesktopWindowManager()
