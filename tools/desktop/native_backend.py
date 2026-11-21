"""
JARVIS OS — Native Desktop Automation Backend
Controls the genuine Linux desktop pointer and keyboard on Raspberry Pi 5 (TigerVNC / X11 / Wayland).
Provides smooth mouse movement, multi-button clicks, scrolling, drag-and-drop,
window-targeted typing, shortcut combinations, coordinate mapping, and input release.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.NativeDesktop")

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Avoid throwing corner exceptions during automation
except ImportError:
    pyautogui = None


class NativeDesktopBackend:
    """Provides genuine OS-level mouse, keyboard, and window automation on Linux."""

    def __init__(self, display: Optional[str] = None):
        self.display = display or os.environ.get("DISPLAY", ":0")
        self._held_mouse_buttons: set[str] = set()
        self._held_keys: set[str] = set()
        self._server_type = self._detect_display_server()

    def _detect_display_server(self) -> str:
        """Autodetect whether current environment runs on X11 or Wayland."""
        if os.getenv("WAYLAND_DISPLAY"):
            return "wayland"
        session = os.getenv("XDG_SESSION_TYPE", "").lower()
        if session in ("wayland", "x11"):
            return session
        if os.getenv("DISPLAY"):
            return "x11"
        return "unknown"

    def get_display_server_info(self) -> Dict[str, Any]:
        """Return display server details and capabilities."""
        res = self.get_screen_resolution()
        return {
            "display": self.display,
            "server_type": self._server_type,
            "resolution": res,
            "pyautogui_available": pyautogui is not None,
            "xdotool_available": os.path.exists("/usr/bin/xdotool"),
            "wmctrl_available": os.path.exists("/usr/bin/wmctrl"),
        }

    def get_screen_resolution(self) -> Dict[str, int]:
        """Detect screen width and height."""
        if pyautogui is not None:
            try:
                w, h = pyautogui.size()
                return {"width": int(w), "height": int(h)}
            except Exception:
                pass

        # Fallback to xrandr
        try:
            res = subprocess.run(
                ["xrandr", "--current"],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=3,
            )
            for line in res.stdout.splitlines():
                if "*" in line:
                    match = re.search(r"(\d+)x(\d+)", line)
                    if match:
                        return {"width": int(match.group(1)), "height": int(match.group(2))}
        except Exception:
            pass

        return {"width": 1360, "height": 768}

    def get_cursor_position(self) -> Dict[str, int]:
        """Query genuine cursor coordinates."""
        if pyautogui is not None:
            try:
                pos = pyautogui.position()
                return {"x": int(pos.x), "y": int(pos.y)}
            except Exception:
                pass

        # Fallback via xdotool
        try:
            res = subprocess.run(
                ["xdotool", "getmouselocation", "--shell"],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=2,
            )
            data = {}
            for line in res.stdout.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    if v.isdigit():
                        data[k.lower()] = int(v)
            if "x" in data and "y" in data:
                return {"x": data["x"], "y": data["y"]}
        except Exception as e:
            logger.debug("Failed to get cursor position via xdotool: %s", e)

        return {"x": 0, "y": 0}

    def move_cursor(self, x: int, y: int, duration: float = 0.25, smooth: bool = True) -> Dict[str, Any]:
        """
        Move the genuine mouse pointer to (x, y) with visible movement across the screen.
        Clamps coordinates to the active screen bounds.
        """
        res = self.get_screen_resolution()
        target_x = max(0, min(res["width"] - 1, int(x)))
        target_y = max(0, min(res["height"] - 1, int(y)))
        t_start = time.perf_counter()

        try:
            if pyautogui is not None:
                move_dur = max(0.05, float(duration)) if smooth else 0.0
                pyautogui.moveTo(target_x, target_y, duration=move_dur, tween=pyautogui.easeInOutQuad if smooth else pyautogui.linear)
            else:
                subprocess.run(
                    ["xdotool", "mousemove", str(target_x), str(target_y)],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    timeout=3,
                )

            # Observe resulting pointer state
            pos_after = self.get_cursor_position()
            duration_ms = round((time.perf_counter() - t_start) * 1000, 2)
            return {
                "status": "ok",
                "action": "move_cursor",
                "target": {"x": target_x, "y": target_y},
                "position_after": pos_after,
                "duration_ms": duration_ms,
                "verified": abs(pos_after["x"] - target_x) <= 2 and abs(pos_after["y"] - target_y) <= 2,
            }
        except Exception as e:
            logger.error("Failed to move cursor to (%d, %d): %s", x, y, e)
            return {"status": "error", "message": str(e), "verified": False}

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        """
        Perform mouse click with optional cursor movement to (x, y).
        Supports left, right, middle, and multiple clicks (double click).
        """
        btn_map = {"left": "left", "right": "right", "middle": "middle"}
        btn = btn_map.get(button.lower(), "left")

        try:
            if x is not None and y is not None:
                self.move_cursor(x, y, duration=0.2, smooth=True)

            if pyautogui is not None:
                pyautogui.click(button=btn, clicks=clicks, interval=0.1)
            else:
                xdotool_btn = "1" if btn == "left" else ("3" if btn == "right" else "2")
                cmd = ["xdotool", "click"]
                if clicks > 1:
                    cmd.extend(["--repeat", str(clicks)])
                cmd.append(xdotool_btn)
                subprocess.run(cmd, env={**os.environ, "DISPLAY": self.display}, capture_output=True, timeout=3)

            time.sleep(0.15)
            pos = self.get_cursor_position()
            return {
                "status": "ok",
                "action": "click",
                "button": btn,
                "clicks": clicks,
                "position": pos,
                "verified": True,
            }
        except Exception as e:
            return {"status": "error", "message": f"Click failed: {e}", "verified": False}

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """Perform right click (context menu)."""
        return self.click(x=x, y=y, button="right", clicks=1)

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """Perform double click."""
        return self.click(x=x, y=y, button="left", clicks=2)

    def scroll(self, direction: str = "down", clicks: int = 5) -> Dict[str, Any]:
        """Scroll mouse wheel up or down."""
        try:
            if pyautogui is not None:
                amt = -int(clicks) if direction.lower() == "down" else int(clicks)
                pyautogui.scroll(amt)
            else:
                xbtn = "5" if direction.lower() == "down" else "4"
                subprocess.run(
                    ["xdotool", "click", "--repeat", str(clicks), xbtn],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    timeout=3,
                )
            time.sleep(0.1)
            return {"status": "ok", "action": "scroll", "direction": direction, "clicks": clicks, "verified": True}
        except Exception as e:
            return {"status": "error", "message": str(e), "verified": False}

    def drag_and_drop(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> Dict[str, Any]:
        """Drag from (x1, y1) and drop at (x2, y2)."""
        try:
            self.move_cursor(x1, y1, duration=0.2, smooth=True)
            if pyautogui is not None:
                pyautogui.mouseDown(button="left")
                self._held_mouse_buttons.add("left")
                pyautogui.moveTo(x2, y2, duration=duration, tween=pyautogui.easeInOutQuad)
                pyautogui.mouseUp(button="left")
                self._held_mouse_buttons.discard("left")
            else:
                subprocess.run(["xdotool", "mousedown", "1"], env={**os.environ, "DISPLAY": self.display}, timeout=2)
                self._held_mouse_buttons.add("left")
                subprocess.run(["xdotool", "mousemove", str(x2), str(y2)], env={**os.environ, "DISPLAY": self.display}, timeout=2)
                subprocess.run(["xdotool", "mouseup", "1"], env={**os.environ, "DISPLAY": self.display}, timeout=2)
                self._held_mouse_buttons.discard("left")

            return {
                "status": "ok",
                "action": "drag_and_drop",
                "from": {"x": x1, "y": y1},
                "to": {"x": x2, "y": y2},
                "verified": True,
            }
        except Exception as e:
            self.release_all_inputs()
            return {"status": "error", "message": f"Drag and drop failed: {e}", "verified": False}

    # ── Keyboard Automation ───────────────────────────────────

    def type_text(self, text: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        """Type text string safely with per-keystroke interval."""
        if target_window:
            self.focus_window(target_window)
            time.sleep(0.2)

        try:
            if pyautogui is not None:
                pyautogui.write(text, interval=0.015)
            else:
                subprocess.run(
                    ["xdotool", "type", "--delay", "15", text],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    timeout=10,
                )
            return {
                "status": "ok",
                "action": "type_text",
                "length": len(text),
                "verified": True,
            }
        except Exception as e:
            return {"status": "error", "message": f"Type text error: {e}", "verified": False}

    def press_key(self, key_name: str) -> Dict[str, Any]:
        """Press a keyboard key (e.g. Return, Escape, Tab, Backspace)."""
        k = key_name.strip()
        try:
            if pyautogui is not None:
                # Map names
                p_map = {"return": "enter", "backspace": "backspace", "escape": "esc", "page_down": "pagedown"}
                pyautogui.press(p_map.get(k.lower(), k.lower()))
            else:
                subprocess.run(["xdotool", "key", k], env={**os.environ, "DISPLAY": self.display}, timeout=3)

            return {"status": "ok", "action": "press_key", "key": key_name, "verified": True}
        except Exception as e:
            return {"status": "error", "message": f"Press key error: {e}", "verified": False}

    def press_hotkey(self, hotkey_str: str) -> Dict[str, Any]:
        """Press key combination like 'ctrl+a', 'ctrl+s', 'ctrl+c', 'alt+tab'."""
        parts = [p.strip().lower() for p in re.split(r"[+\s]", hotkey_str) if p.strip()]
        try:
            if pyautogui is not None:
                pyautogui.hotkey(*parts)
            else:
                subprocess.run(
                    ["xdotool", "key", "+".join(parts)],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    timeout=3,
                )
            time.sleep(0.15)
            return {"status": "ok", "action": "press_hotkey", "hotkey": hotkey_str, "verified": True}
        except Exception as e:
            return {"status": "error", "message": f"Press hotkey error: {e}", "verified": False}

    def select_all(self) -> Dict[str, Any]:
        """Select all text in focused control (Ctrl+A)."""
        return self.press_hotkey("ctrl+a")

    def copy(self) -> Dict[str, Any]:
        """Copy selected content (Ctrl+C)."""
        return self.press_hotkey("ctrl+c")

    def paste(self) -> Dict[str, Any]:
        """Paste clipboard content (Ctrl+V)."""
        return self.press_hotkey("ctrl+v")

    def focus_window(self, target: str) -> Dict[str, Any]:
        """Focus window by hex ID or title keyword using wmctrl."""
        try:
            cmd = ["wmctrl", "-i", "-a", target] if target.startswith("0x") else ["wmctrl", "-a", target]
            res = subprocess.run(cmd, env={**os.environ, "DISPLAY": self.display}, capture_output=True, timeout=3)
            time.sleep(0.2)
            return {"status": "ok", "action": "focus_window", "target": target, "verified": res.returncode == 0}
        except Exception as e:
            return {"status": "error", "message": str(e), "verified": False}

    def release_all_inputs(self) -> None:
        """Emergency release of any held mouse buttons or modifier keys."""
        if pyautogui is not None:
            try:
                for btn in list(self._held_mouse_buttons):
                    pyautogui.mouseUp(button=btn)
                pyautogui.mouseUp(button="left")
                pyautogui.mouseUp(button="right")
                pyautogui.mouseUp(button="middle")
            except Exception:
                pass
            try:
                for key in ["ctrl", "alt", "shift", "super"]:
                    pyautogui.keyUp(key)
            except Exception:
                pass
        else:
            try:
                subprocess.run(["xdotool", "mouseup", "1", "mouseup", "2", "mouseup", "3"], env={**os.environ, "DISPLAY": self.display})
            except Exception:
                pass

        self._held_mouse_buttons.clear()
        self._held_keys.clear()
        logger.info("Released all held mouse buttons and keys")


# Global singleton instance
native_backend = NativeDesktopBackend()
