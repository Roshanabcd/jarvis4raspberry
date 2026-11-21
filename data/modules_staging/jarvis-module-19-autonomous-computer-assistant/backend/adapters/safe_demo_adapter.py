"""Safe Demonstration Desktop Adapter for JARVIS Module 19.

NEVER controls the real host OS. Maintains a deterministic virtual desktop
(applications, windows, active focus, cursor position, text buffer) and renders
real synthetic PNG screenshots with Pillow visibly labeled 'SIMULATED DESKTOP'.
"""

from __future__ import annotations

import base64
import io
import uuid
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw

from backend.adapters.contracts import DesktopAutomationAdapter
from backend.models.database import utc_now_iso


class SafeDemoDesktopAdapter(DesktopAutomationAdapter):
    adapter_name = "safe_demo_virtual_desktop"
    is_simulated = True

    def __init__(self) -> None:
        self._catalog: List[Dict[str, Any]] = [
            {"app_id": "jarvis-terminal", "name": "JARVIS Terminal", "category": "System", "allowlisted": True, "simulated": True},
            {"app_id": "code-studio", "name": "Code Studio IDE", "category": "Developer", "allowlisted": True, "simulated": True},
            {"app_id": "notes-pad", "name": "JARVIS Notes", "category": "Productivity", "allowlisted": True, "simulated": True},
            {"app_id": "browser-sandbox", "name": "Chromium Sandbox", "category": "Web", "allowlisted": True, "simulated": True},
            {"app_id": "robotics-telemetry", "name": "Pi 5 Telemetry HUD", "category": "Hardware", "allowlisted": True, "simulated": True},
        ]
        self._windows: Dict[str, Dict[str, Any]] = {
            "win-01": {
                "window_id": "win-01",
                "app_id": "jarvis-terminal",
                "title": "JARVIS Terminal - ~/scratch/jarvis-os",
                "bounds": {"x": 40, "y": 50, "w": 560, "h": 340},
                "focused": True,
                "text_buffer": "jarvis@pi5:~$ status --ok",
            },
            "win-02": {
                "window_id": "win-02",
                "app_id": "code-studio",
                "title": "Code Studio - orchestrator.py",
                "bounds": {"x": 280, "y": 110, "w": 580, "h": 360},
                "focused": False,
                "text_buffer": "# JARVIS OS Module 19 Safe Demo Buffer",
            },
        }
        self._active_window_id: str = "win-01"
        self._cursor: Dict[str, int] = {"x": 320, "y": 220}
        self._last_hotkey: Optional[List[str]] = None

    def discover_applications(self) -> List[Dict[str, Any]]:
        running_apps = {w["app_id"] for w in self._windows.values()}
        return [{**app, "running": app["app_id"] in running_apps} for app in self._catalog]

    def list_windows(self) -> List[Dict[str, Any]]:
        return list(self._windows.values())

    def select_window(self, window_id: str) -> Dict[str, Any]:
        if window_id not in self._windows:
            raise KeyError(f"Window '{window_id}' not found on virtual desktop")
        for wid, win in self._windows.items():
            win["focused"] = wid == window_id
        self._active_window_id = window_id
        return {"simulated": True, "focused_window": self._windows[window_id]}

    def launch_application(self, app_id: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        app = next((a for a in self._catalog if a["app_id"] == app_id), None)
        if not app:
            raise ValueError(f"Application '{app_id}' is not in the permitted allowlist")
        win_id = f"win-{uuid.uuid4().hex[:6]}"
        for w in self._windows.values():
            w["focused"] = False
        new_win = {
            "window_id": win_id,
            "app_id": app_id,
            "title": f"{app['name']} (Simulated)",
            "bounds": {"x": 120, "y": 90, "w": 560, "h": 340},
            "focused": True,
            "text_buffer": f"Launched {app['name']} args={args or []}",
        }
        self._windows[win_id] = new_win
        self._active_window_id = win_id
        return {"simulated": True, "launched_app": app, "window": new_win}

    def capture_screenshot(self, window_id: Optional[str] = None) -> Dict[str, Any]:
        width, height = 960, 540
        img = Image.new("RGB", (width, height), color=(5, 11, 22))
        draw = ImageDraw.Draw(img)

        # Header bar
        draw.rectangle([0, 0, width, 38], fill=(16, 30, 48))
        draw.line([(0, 38), (width, 38)], fill=(0, 217, 255), width=2)
        draw.text((16, 12), "JARVIS OS | SIMULATED DESKTOP CAPTURE (SAFE DEMO ADAPTER)", fill=(0, 217, 255))
        draw.text((width - 210, 12), utc_now_iso()[:19] + "Z", fill=(143, 168, 200))

        # Draw windows
        target_windows = (
            [self._windows[window_id]] if window_id and window_id in self._windows else list(self._windows.values())
        )
        for win in target_windows:
            b = win["bounds"]
            border = (0, 217, 255) if win["focused"] else (55, 85, 120)
            draw.rectangle([b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]], fill=(16, 30, 48), outline=border, width=2)
            draw.rectangle([b["x"], b["y"], b["x"] + b["w"], b["y"] + 28], fill=(22, 42, 68))
            draw.text((b["x"] + 10, b["y"] + 8), f"{win['title']} [{win['window_id']}]".encode("ascii", "replace").decode("ascii"), fill=(240, 248, 255))
            draw.text((b["x"] + 12, b["y"] + 44), str(win.get("text_buffer", ""))[:80].encode("ascii", "replace").decode("ascii"), fill=(37, 230, 162))

        # Draw virtual cursor reticle
        cx, cy = self._cursor["x"], self._cursor["y"]
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=(152, 104, 255), width=2)
        draw.line([(cx - 12, cy), (cx + 12, cy)], fill=(0, 217, 255), width=1)
        draw.line([(cx, cy - 12), (cx, cy + 12)], fill=(0, 217, 255), width=1)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return {
            "screenshot_id": f"shot_{uuid.uuid4().hex[:10]}",
            "window_id": window_id or self._active_window_id,
            "width": width,
            "height": height,
            "simulated": True,
            "image_b64": b64,
            "created_at": utc_now_iso(),
        }

    def mouse_move(self, x: int, y: int) -> Dict[str, Any]:
        self._cursor = {"x": max(0, min(1920, int(x))), "y": max(0, min(1080, int(y)))}
        return {"simulated": True, "cursor": self._cursor}

    def mouse_click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        self.mouse_move(x, y)
        return {
            "simulated": True,
            "cursor": self._cursor,
            "button": button,
            "clicks": clicks,
            "active_window_id": self._active_window_id,
        }

    def keyboard_type(self, text: str) -> Dict[str, Any]:
        win = self._windows.get(self._active_window_id)
        if win:
            win["text_buffer"] = (win.get("text_buffer", "") + "\n" + text)[-500:]
        return {
            "simulated": True,
            "typed_length": len(text),
            "active_window_id": self._active_window_id,
        }

    def keyboard_hotkey(self, keys: List[str]) -> Dict[str, Any]:
        self._last_hotkey = list(keys)
        return {
            "simulated": True,
            "keys": self._last_hotkey,
            "active_window_id": self._active_window_id,
        }

    def get_state_snapshot(self) -> Dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "simulated": self.is_simulated,
            "active_window_id": self._active_window_id,
            "cursor": self._cursor,
            "window_count": len(self._windows),
            "last_hotkey": self._last_hotkey,
        }
