"""
JARVIS OS — Phase 4 Computer Action Engine
Executes verified mouse clicks, typing, key combinations, window manipulation,
scrolling, and multi-step task workflows with state verification on Native X11.
"""

import os
import time
import uuid
import logging
import subprocess
from typing import Any, Dict, List, Optional
from tools.desktop.desktop_perception import desktop_perception
from tools.desktop.element_detector import element_detector, UIElement

logger = logging.getLogger("JARVIS.ActionEngine")

class ComputerActionEngine:
    """Central engine for executing observable and verified desktop computer-use actions."""

    def __init__(self, display: str = ":0"):
        self.display = display
        self._action_history: List[Dict[str, Any]] = []
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._max_history = 50

    def get_action_history(self) -> List[Dict[str, Any]]:
        return self._action_history[-self._max_history:]

    def move_cursor(self, x: int, y: int, smooth: bool = True) -> Dict[str, Any]:
        """Move native desktop pointer to (x, y) with visible movement."""
        from tools.desktop.native_backend import native_backend
        from tools.desktop.unified_computer_service import unified_computer_service
        if unified_computer_service.is_emergency_stopped():
            return {"status": "error", "message": "Emergency stop is active", "verified": False}
        return native_backend.move_cursor(x, y, duration=0.25, smooth=smooth)

    def click_element(
        self,
        x: int,
        y: int,
        button: int = 1,
        clicks: int = 1,
        verify: bool = True
    ) -> Dict[str, Any]:
        """Perform mouse click at (x, y) with pre- and post-action verification."""
        from tools.desktop.unified_computer_service import unified_computer_service
        if unified_computer_service.is_emergency_stopped():
            return {"status": "error", "message": "Emergency stop is active", "verified": False}

        action_id = f"act_{uuid.uuid4().hex[:8]}"
        t_start = time.perf_counter()

        pre_snap = desktop_perception.capture_fullscreen() if verify else None
        pre_win = desktop_perception.get_active_window()

        try:
            cmd = ["xdotool", "mousemove", str(x), str(y), "click"]
            if clicks > 1:
                cmd.extend(["--repeat", str(clicks)])
            cmd.append(str(button))

            res = subprocess.run(
                cmd,
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=3,
            )

            # Wait short settling time for UI repaint
            time.sleep(0.25)
            post_win = desktop_perception.get_active_window()
            post_snap = desktop_perception.capture_fullscreen() if verify else None

            # Verify observable change
            verification = {"verified": False, "change_ratio": 0.0}
            if verify and pre_snap and post_snap and pre_snap.get("filepath") and post_snap.get("filepath"):
                cmp_res = element_detector.compare_images(pre_snap["filepath"], post_snap["filepath"])
                focus_changed = pre_win.get("id") != post_win.get("id")
                is_verified = cmp_res.get("changed", False) or focus_changed
                verification = {
                    "verified": is_verified,
                    "change_ratio": cmp_res.get("change_ratio", 0.0),
                    "focus_changed": focus_changed,
                    "changed_pixels": cmp_res.get("changed_pixels", 0),
                }

            record = {
                "action_id": action_id,
                "action": "click",
                "coordinates": {"x": x, "y": y},
                "button": button,
                "clicks": clicks,
                "status": "ok" if res.returncode == 0 else "error",
                "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                "active_window_after": post_win,
                "verification": verification,
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record

        except Exception as e:
            logger.error("Click error at %d,%d: %s", x, y, e)
            return {
                "action_id": action_id,
                "action": "click",
                "status": "error",
                "message": str(e),
                "verification": {"verified": False},
            }

    def click_named_element(self, query: str, verify: bool = True) -> Dict[str, Any]:
        """Locate an element semantically and click its center coordinates."""
        active_win = desktop_perception.get_active_window()
        elem = element_detector.find_element(query, active_win)

        if not elem:
            return {
                "status": "not_found",
                "query": query,
                "message": f"Unable to locate UI element matching '{query}'",
                "verification": {"verified": False},
            }

        res = self.click_element(elem.center_x, elem.center_y, verify=verify)
        res["target_element"] = elem.to_dict()
        return res

    def double_click_element(self, x: int, y: int, verify: bool = True) -> Dict[str, Any]:
        """Perform double-click at (x, y)."""
        return self.click_element(x, y, button=1, clicks=2, verify=verify)

    def right_click_element(self, x: int, y: int, verify: bool = True) -> Dict[str, Any]:
        """Perform right-click at (x, y)."""
        return self.click_element(x, y, button=3, clicks=1, verify=verify)

    def type_text(self, text: str, target_window: Optional[str] = None, verify: bool = True) -> Dict[str, Any]:
        """Type text string into the active or target window with verification."""
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        t_start = time.perf_counter()

        if target_window:
            self.focus_window(target_window)
            time.sleep(0.15)

        pre_snap = desktop_perception.capture_fullscreen() if verify else None

        try:
            # Send text typing via xdotool with 12ms delay per keystroke for stability
            res = subprocess.run(
                ["xdotool", "type", "--delay", "12", text],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=10,
            )

            time.sleep(0.2)
            post_snap = desktop_perception.capture_fullscreen() if verify else None
            verification = {"verified": False, "change_ratio": 0.0}

            if verify and pre_snap and post_snap and pre_snap.get("filepath") and post_snap.get("filepath"):
                cmp_res = element_detector.compare_images(pre_snap["filepath"], post_snap["filepath"])
                verification = {
                    "verified": cmp_res.get("changed", False),
                    "change_ratio": cmp_res.get("change_ratio", 0.0),
                }

            record = {
                "action_id": action_id,
                "action": "type_text",
                "text_length": len(text),
                "status": "ok" if res.returncode == 0 else "error",
                "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                "verification": verification,
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record

        except Exception as e:
            logger.error("Type text error: %s", e)
            return {"action_id": action_id, "action": "type_text", "status": "error", "message": str(e)}

    def press_key(self, key: str) -> Dict[str, Any]:
        """Press a keyboard key (e.g. 'Return', 'Escape', 'Tab', 'BackSpace', 'Page_Down')."""
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        try:
            res = subprocess.run(
                ["xdotool", "key", key],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=3,
            )
            record = {
                "action_id": action_id,
                "action": "press_key",
                "key": key,
                "status": "ok" if res.returncode == 0 else "error",
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record
        except Exception as e:
            return {"action_id": action_id, "action": "press_key", "status": "error", "message": str(e)}

    def press_hotkey(self, hotkey: str) -> Dict[str, Any]:
        """Press a combination of keys (e.g. 'ctrl+t', 'ctrl+w', 'alt+Left', 'ctrl+Shift+p')."""
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        try:
            res = subprocess.run(
                ["xdotool", "key", hotkey],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=3,
            )
            time.sleep(0.2)
            record = {
                "action_id": action_id,
                "action": "press_hotkey",
                "hotkey": hotkey,
                "status": "ok" if res.returncode == 0 else "error",
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record
        except Exception as e:
            return {"action_id": action_id, "action": "press_hotkey", "status": "error", "message": str(e)}

    def scroll_page(self, direction: str = "down", clicks: int = 5) -> Dict[str, Any]:
        """Scroll page up or down with verification."""
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        pre_snap = desktop_perception.capture_fullscreen()
        btn = "5" if direction.lower() == "down" else "4"

        try:
            res = subprocess.run(
                ["xdotool", "click", "--repeat", str(clicks), btn],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=3,
            )
            time.sleep(0.3)
            post_snap = desktop_perception.capture_fullscreen()

            verification = {"verified": False, "change_ratio": 0.0}
            if pre_snap and post_snap and pre_snap.get("filepath") and post_snap.get("filepath"):
                cmp_res = element_detector.compare_images(pre_snap["filepath"], post_snap["filepath"])
                verification = {
                    "verified": cmp_res.get("changed", False),
                    "change_ratio": cmp_res.get("change_ratio", 0.0),
                }

            record = {
                "action_id": action_id,
                "action": "scroll",
                "direction": direction,
                "clicks": clicks,
                "status": "ok" if res.returncode == 0 else "error",
                "verification": verification,
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record
        except Exception as e:
            return {"action_id": action_id, "action": "scroll", "status": "error", "message": str(e)}

    def focus_window(self, target: str) -> Dict[str, Any]:
        """Activate and focus a window by hex ID or title substring."""
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        try:
            if target.startswith("0x"):
                res = subprocess.run(
                    ["wmctrl", "-i", "-a", target],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    timeout=3,
                )
            else:
                res = subprocess.run(
                    ["wmctrl", "-a", target],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    timeout=3,
                )

            time.sleep(0.2)
            active_win = desktop_perception.get_active_window()
            verified = (target.lower() in active_win.get("title", "").lower() or
                        target.lower() == active_win.get("id", "").lower())

            record = {
                "action_id": action_id,
                "action": "focus_window",
                "target": target,
                "status": "ok" if res.returncode == 0 else "error",
                "active_window": active_win,
                "verification": {"verified": verified},
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record
        except Exception as e:
            return {"action_id": action_id, "action": "focus_window", "status": "error", "message": str(e)}

    def switch_window(self, app_name: str) -> Dict[str, Any]:
        """Switch to a specific application window (e.g. 'chrome', 'code', 'terminal')."""
        wins = desktop_perception.list_open_windows()
        q = app_name.lower().strip()

        # Alias mapping
        alias_map = {
            "terminal": ["x-terminal-emulator", "lxterminal", "bash"],
            "vscode": ["com.microsoft.vscode", "code", "visual studio code"],
            "vs code": ["com.microsoft.vscode", "code", "visual studio code"],
            "chrome": ["google-chrome", "chrome", "chromium"],
            "browser": ["google-chrome", "chrome", "firefox"],
            "files": ["pcmanfm", "downloads"],
            "file manager": ["pcmanfm", "downloads"],
            "antigravity": ["antigravity"],
        }
        search_terms = alias_map.get(q, [q])

        target_win = None
        for w in wins:
            # Skip desktop root/panel/conky widgets
            if w.get("desktop", 0) == -1:
                continue

            app = w.get("app", "").lower()
            title = w.get("title", "").lower()

            for term in search_terms:
                if term in app or term in title:
                    target_win = w
                    break
            if target_win:
                break

        if not target_win:
            return {
                "status": "not_found",
                "target_app": app_name,
                "message": f"No open window found for application '{app_name}'",
                "verification": {"verified": False},
            }

        return self.focus_window(target_win["id"])

    def minimize_window(self, target: str) -> Dict[str, Any]:
        """Minimize a window by hex ID or title substring."""
        try:
            win_id = target
            if not target.startswith("0x"):
                wins = desktop_perception.list_open_windows()
                for w in wins:
                    if target.lower() in w["title"].lower():
                        win_id = w["id"]
                        break

            dec_id = int(win_id, 16)
            res = subprocess.run(
                ["xdotool", "windowminimize", str(dec_id)],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                timeout=3,
            )
            return {"status": "ok" if res.returncode == 0 else "error", "action": "minimize", "target": target}
        except Exception as e:
            return {"status": "error", "action": "minimize", "message": str(e)}

    def maximize_window(self, target: str) -> Dict[str, Any]:
        """Toggle maximize state of a window."""
        try:
            cmd = ["wmctrl"]
            if target.startswith("0x"):
                cmd.extend(["-i", "-r", target, "-b", "toggle,maximized_vert,maximized_horz"])
            else:
                cmd.extend(["-r", target, "-b", "toggle,maximized_vert,maximized_horz"])

            res = subprocess.run(cmd, env={**os.environ, "DISPLAY": self.display}, capture_output=True, timeout=3)
            return {"status": "ok" if res.returncode == 0 else "error", "action": "maximize", "target": target}
        except Exception as e:
            return {"status": "error", "action": "maximize", "message": str(e)}

    # Multi-Step Task Management
    def create_task(self, name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create and initialize a planned multi-step computer automation task."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_record = {
            "task_id": task_id,
            "name": name,
            "state": "PLANNING",
            "steps": steps,
            "current_step": 0,
            "completed_steps": [],
            "failed_steps": [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self._active_tasks[task_id] = task_record
        return task_record

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._active_tasks.get(task_id)

    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a created task step-by-step with observe-act-verify loop."""
        task = self._active_tasks.get(task_id)
        if not task:
            return {"status": "error", "message": f"Task {task_id} not found"}

        task["state"] = "ACTING"
        for idx, step in enumerate(task["steps"]):
            task["current_step"] = idx + 1
            action_type = step.get("action")

            step_res = {}
            if action_type == "click":
                step_res = self.click_element(step.get("x", 0), step.get("y", 0), verify=True)
            elif action_type == "click_named":
                step_res = self.click_named_element(step.get("query", ""), verify=True)
            elif action_type == "type":
                step_res = self.type_text(step.get("text", ""), target_window=step.get("window"), verify=True)
            elif action_type == "press_key":
                step_res = self.press_key(step.get("key", "Return"))
            elif action_type == "press_hotkey":
                step_res = self.press_hotkey(step.get("hotkey", ""))
            elif action_type == "scroll":
                step_res = self.scroll_page(direction=step.get("direction", "down"), clicks=step.get("clicks", 5))
            elif action_type == "switch_window":
                step_res = self.switch_window(step.get("app", ""))
            elif action_type == "focus_window":
                step_res = self.focus_window(step.get("target", ""))
            else:
                step_res = {"status": "skipped", "message": f"Unknown action {action_type}"}

            step["result"] = step_res
            if step_res.get("status") == "ok":
                task["completed_steps"].append(step)
            else:
                task["failed_steps"].append(step)
                task["state"] = "PARTIALLY COMPLETED" if task["completed_steps"] else "FAILED"
                task["updated_at"] = time.time()
                return task

        task["state"] = "COMPLETED"
        task["updated_at"] = time.time()
        return task

    def stop_task(self, task_id: str) -> Dict[str, Any]:
        """Halt an active computer task immediately."""
        task = self._active_tasks.get(task_id)
        if task:
            task["state"] = "CANCELLED"
            task["updated_at"] = time.time()
            return {"status": "ok", "task_id": task_id, "state": "CANCELLED"}
        return {"status": "error", "message": f"Task {task_id} not found"}


computer_action_engine = ComputerActionEngine()
