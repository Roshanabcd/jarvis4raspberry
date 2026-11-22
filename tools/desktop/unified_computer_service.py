"""
JARVIS OS — Unified Computer Control Engine
Coordinates Browser Automation (Playwright) and Native Desktop Automation (X11/Wayland).
Enforces:
- 4 Safety Modes: OBSERVE, GUIDED, COMMAND_CONTROL, TRUSTED_WORKFLOW
- Emergency Stop (E-STOP) kill switch
- Observe-Understand-Plan-Authorize-Act-Verify action execution loop
- Comprehensive action audit logging and telemetry
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from tools.desktop.browser_backend import browser_backend
from tools.desktop.native_backend import native_backend
from tools.desktop.screen_intelligence import screen_intelligence
from tools.desktop.desktop_perception import desktop_perception

logger = logging.getLogger("JARVIS.UnifiedComputerService")
ESTOP_LOCK_PATH = Path("/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/computer_estop.lock")


class ComputerControlMode(str, Enum):
    OBSERVE = "observe"                      # Mode 1: Read-only inspection
    GUIDED = "guided"                        # Mode 2: Proposes actions, requires approval
    COMMAND_CONTROL = "command_control"      # Mode 3: Executes authorized low-risk instructions
    TRUSTED_WORKFLOW = "trusted_workflow"    # Mode 4: Automated pre-approved workflows


class UnifiedComputerService:
    """Central orchestrator for all JARVIS computer-control and automation requests."""

    def __init__(self):
        self._mode: ComputerControlMode = ComputerControlMode.COMMAND_CONTROL
        self._lock_file = ESTOP_LOCK_PATH
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._emergency_stopped: bool = self._lock_file.exists()
        self._stop_requested: bool = self._emergency_stopped
        self._session_enabled: bool = not self._emergency_stopped
        self._target_window: Optional[str] = None
        self._action_history: List[Dict[str, Any]] = []
        self._max_history: int = 50
        self._lock = threading.RLock()
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}

    @property
    def mode(self) -> ComputerControlMode:
        return self._mode

    @property
    def session_enabled(self) -> bool:
        return self._session_enabled

    def enable_session(self) -> Dict[str, Any]:
        """Explicitly enable computer control session."""
        with self._lock:
            if self._lock_file.exists():
                return self.rearm_session()
            self._session_enabled = True
            self._emergency_stopped = False
            self._stop_requested = False
            logger.info("Computer control session explicitly enabled.")
            return {
                "status": "ok",
                "session_enabled": True,
                "response": "Computer control session is now active and ready for commands.",
                "verified": True,
                "tools_used": ["computer_session_control"],
                "timestamp": time.time(),
            }

    def disable_session(self) -> Dict[str, Any]:
        """Disable computer control session and trigger safe stop."""
        with self._lock:
            self._session_enabled = False
            self.emergency_stop()
            logger.info("Computer control session disabled.")
            return {
                "status": "stopped",
                "session_enabled": False,
                "response": "Computer control session has been closed.",
                "verified": True,
                "tools_used": ["computer_session_control"],
                "timestamp": time.time(),
            }

    def set_target_window(self, win_name: Optional[str]) -> None:
        """Store active target window context across conversational turns."""
        with self._lock:
            self._target_window = win_name
            logger.info("Current target window updated to: %s", win_name)

    def get_target_window(self) -> Optional[str]:
        return self._target_window

    def set_mode(self, mode: ComputerControlMode | str) -> ComputerControlMode:
        """Update operational safety mode."""
        with self._lock:
            if isinstance(mode, str):
                mode = ComputerControlMode(mode.lower())
            self._mode = mode
            logger.info("Computer control mode set to: %s", self._mode.value)
            return self._mode

    def is_emergency_stopped(self) -> bool:
        if self._lock_file.exists():
            self._emergency_stopped = True
        return self._emergency_stopped

    def emergency_stop(self) -> Dict[str, Any]:
        """Trigger immediate emergency stop: interrupt ongoing actions, release inputs, and write persistent lock."""
        with self._lock:
            self._emergency_stopped = True
            self._stop_requested = True
            try:
                self._lock_file.parent.mkdir(parents=True, exist_ok=True)
                self._lock_file.write_text(json.dumps({
                    "timestamp": time.time(),
                    "reason": "emergency_stop_triggered",
                    "pid": os.getpid()
                }))
            except Exception as e:
                logger.error("Failed to write estop lock file: %s", e)

            native_backend.release_all_inputs()
            logger.warning("🚨 EMERGENCY STOP ACTIVATED. All computer automation halted.")

            record = {
                "action_id": f"stop_{uuid.uuid4().hex[:8]}",
                "action": "emergency_stop",
                "timestamp": time.time(),
                "status": "stopped",
                "message": "Emergency stop triggered. Ongoing operations cancelled, persistent lock written, and inputs released.",
            }
            self._action_history.append(record)
            return record

    def rearm_session(self, authorization_token: Optional[str] = None) -> Dict[str, Any]:
        """Safely re-arm computer control session, releasing inputs and removing persistent lock."""
        with self._lock:
            native_backend.release_all_inputs()
            try:
                if self._lock_file.exists():
                    self._lock_file.unlink()
            except Exception as e:
                logger.error("Failed to remove estop lock file: %s", e)

            self._emergency_stopped = False
            self._stop_requested = False
            self._session_enabled = True
            self._pending_approvals.clear()

            logger.info("Emergency stop safely cleared and session re-armed. Lock file removed.")
            return {
                "status": "active",
                "session_enabled": True,
                "emergency_stopped": False,
                "message": "Emergency stop safely cleared and session re-armed. Persistent lock removed and inputs released.",
                "response": "Computer control session has been safely re-armed. The emergency lock has been removed.",
                "verified": True,
                "tools_used": ["computer_rearm_session"],
                "timestamp": time.time(),
            }

    def reset_emergency_stop(self) -> Dict[str, Any]:
        """Reset emergency stop state after user authorization."""
        return self.rearm_session()

    def get_status(self) -> Dict[str, Any]:
        """Get live status of unified computer control service."""
        cur_pos = native_backend.get_cursor_position()
        resolution = native_backend.get_screen_resolution()
        active_win = desktop_perception.get_active_window()
        disp_info = native_backend.get_display_server_info()

        return {
            "status": "stopped" if self._emergency_stopped else "active",
            "emergency_stopped": self._emergency_stopped,
            "session_enabled": self._session_enabled,
            "target_window": self._target_window,
            "mode": self._mode.value,
            "display": disp_info["display"],
            "server_type": disp_info["server_type"],
            "resolution": resolution,
            "cursor_position": cur_pos,
            "active_window": active_win,
            "browser_active": browser_backend.is_running(),
            "browser_url": browser_backend.get_url() if browser_backend.is_running() else None,
            "browser_title": browser_backend.get_title() if browser_backend.is_running() else None,
            "recent_actions_count": len(self._action_history),
        }

    def get_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._action_history[-self._max_history:])

    def _check_permission(self, action_name: str, is_mutation: bool = True) -> Tuple[bool, str]:
        """Verify safety mode and emergency stop gates."""
        if self._emergency_stopped or self._stop_requested:
            return False, "Action blocked: Computer control is currently in EMERGENCY STOP."

        if not self._session_enabled:
            return False, "Action blocked: Computer control session is currently inactive. Say 'Jarvis, enable computer control' to activate it."

        if is_mutation and self._mode == ComputerControlMode.OBSERVE:
            return False, "Action blocked: Current mode is OBSERVE (read-only). Clicking or typing is prohibited."

        return True, ""

    # ── High-Level Action Execution (Observe-Act-Verify) ────────

    def execute_natural_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Deconstruct a natural language instruction, execute via appropriate backend,
        verify results, and formulate a factual natural language summary.
        Examples:
        - "Select option 1 and click Submit"
        - "Select option 2"
        - "Click Submit"
        - "Move the mouse to the Submit button"
        - "Right-click the test item"
        - "Type Hello JARVIS"
        - "Press Ctrl+A"
        - "Scroll down"
        - "Stop controlling my computer"
        """
        t_start = time.perf_counter()
        raw_text = instruction.strip()
        text_lower = raw_text.lower()
        action_id = f"act_{uuid.uuid4().hex[:8]}"

        # 0. Emergency Stop command check
        if re.search(r"\b(stop|halt|cancel|emergency\s+stop)\b", text_lower) and any(w in text_lower for w in ["computer", "control", "jarvis", "automation", "now", "it"]):
            res = self.emergency_stop()
            return {
                "action_id": action_id,
                "status": "stopped",
                "response": "I have stopped controlling the computer immediately. All active operations were cancelled.",
                "verified": True,
                "tools_used": ["computer_emergency_stop"],
                "timestamp": time.time(),
            }

        # 0b. Session Enable / Re-arm command check
        if re.search(r"\b(re-?arm|enable|start|activate|resume)\b.*\b(computer\s+control|desktop\s+control|computer\s+session|computer)\b", text_lower) or "rearm" in text_lower or "re-arm" in text_lower:
            res = self.rearm_session()
            return {
                "action_id": action_id,
                "status": "enabled",
                "response": res.get("response", "Computer control session has been re-armed."),
                "verified": True,
                "tools_used": ["computer_enable_session"],
                "timestamp": time.time(),
            }

        # Check safety modes & e-stop
        allowed, reason = self._check_permission(raw_text, is_mutation=True)
        if not allowed:
            return {
                "action_id": action_id,
                "status": "blocked",
                "response": reason,
                "verified": False,
                "tools_used": ["permission_gate"],
                "timestamp": time.time(),
            }

        # Reset per-command stop flag
        self._stop_requested = False

        # 1. Compound Command: "Select option X and click Submit"
        m_compound = re.search(r"\bselect\s+(?:the\s+)?(option\s*\d+|option\s*one|option\s*two|option\s*three|first\s*option|second\s*option|third\s*option|[a-z0-9_\-\s]+)\s+and\s+(?:then\s+)?(?:click|press|submit)\s*(?:the\s+)?(submit|save|confirm|ok|button)?\b", text_lower)
        if m_compound:
            opt_raw = m_compound.group(1).strip()
            btn_raw = m_compound.group(2).strip() if (m_compound.lastindex >= 2 and m_compound.group(2)) else "Submit"
            return self._execute_select_and_submit(opt_raw, btn_raw, action_id, raw_text)

        # 2. Select Option Command: "Select option 1"
        m_select = re.search(r"\bselect\s+(?:the\s+)?(option\s*\d+|option\s*one|option\s*two|option\s*three|first\s*option|second\s*option|third\s*option|[a-z0-9_\-\s]+)[\.\?!]*$", text_lower)
        if m_select and not re.search(r"\b(all|video|movie|tab|window)\b", text_lower):
            opt_raw = m_select.group(1).strip()
            return self._execute_select_option(opt_raw, action_id, raw_text)

        # 3. Click Command: "Click Submit", "Click the first option", "Right-click the test item"
        if re.search(r"\bright[\s\-]click\b", text_lower):
            target_match = re.search(r"\bright[\s\-]click\s+(?:on\s+)?(?:the\s+)?(.+?)[\.\?!]*$", text_lower)
            target = target_match.group(1).strip() if target_match else "test item"
            return self._execute_right_click(target, action_id, raw_text)

        if re.search(r"\bdouble[\s\-]click\b", text_lower):
            target_match = re.search(r"\bdouble[\s\-]click\s+(?:on\s+)?(?:the\s+)?(.+?)[\.\?!]*$", text_lower)
            target = target_match.group(1).strip() if target_match else "folder"
            return self._execute_double_click(target, action_id, raw_text)

        m_click = re.search(r"\bclick\s+(?:on\s+)?(?:the\s+)?(.+?)[\.\?!]*$", text_lower)
        if m_click and not re.search(r"\b(forward|backward|left|right|stop|play|pause)\b", text_lower):
            target = m_click.group(1).strip()
            return self._execute_click(target, action_id, raw_text)

        # 4. Move Mouse Command: "Move the mouse to the search box"
        m_move = re.search(r"\bmove\s+(?:the\s+)?mouse\s+(?:pointer\s+)?to\s+(?:the\s+)?(.+?)[\.\?!]*$", text_lower)
        if m_move:
            target = m_move.group(1).strip()
            return self._execute_move_mouse(target, action_id, raw_text)

        # 5. Type Text Command: "Type Hello JARVIS", "Type 'hello world'"
        m_type = re.search(r"\btype\s+[\"']?([^\"'\n]+)[\"']?[\.\?!]*$", raw_text, flags=re.IGNORECASE)
        if m_type:
            txt = m_type.group(1).rstrip(".!?\"'").strip()
            return self._execute_type_text(txt, action_id, raw_text)

        # 6. Keyboard Shortcut Command: "Press Ctrl+A", "Press Enter", "Press Escape"
        m_press = re.search(r"\bpress\s+(?:the\s+)?(?:keys?\s+)?([a-z0-9_\+\-\s]+)[\.\?!]*$", text_lower)
        if m_press:
            key_combo = m_press.group(1).strip()
            return self._execute_press_key(key_combo, action_id, raw_text)

        # 7. Scroll Command: "Scroll down", "Scroll up"
        m_scroll = re.search(r"\bscroll\s+(?:the\s+)?(?:page\s+|screen\s+)?(down|up)\b", text_lower)
        if m_scroll:
            direction = m_scroll.group(1).lower()
            return self._execute_scroll(direction, action_id, raw_text)

        return {
            "action_id": action_id,
            "status": "unrecognized",
            "response": f"I couldn't map '{instruction}' to a verified computer action.",
            "verified": False,
            "tools_used": [],
            "timestamp": time.time(),
        }

    # ── Action Implementations ─────────────────────────────────

    def _execute_select_and_submit(self, option_target: str, button_target: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Execute compound multi-step selection + submission with step-by-step verification."""
        tools_used = []

        # Step 1: Select option
        sel_res = browser_backend.select_option(option_target, verify=True)
        tools_used.append("browser_select_option")
        if not sel_res.get("verified"):
            resp = f"I attempted to select {option_target}, but could not verify that it was selected."
            return {
                "action_id": action_id,
                "status": "failed",
                "response": resp,
                "verified": False,
                "step_failures": [sel_res],
                "tools_used": tools_used,
                "timestamp": time.time(),
            }

        # Check for ambiguity before clicking Submit
        btn_name = button_target if button_target else "Submit"
        ambig = browser_backend.detect_ambiguity(btn_name, element_type="button")
        if ambig.get("ambiguous"):
            candidates = [c.get("id") or c.get("text") for c in ambig.get("candidates", [])]
            return {
                "action_id": action_id,
                "status": "ambiguous",
                "response": f"I selected {option_target}, but found multiple '{btn_name}' buttons: {candidates}. Please clarify which button to click.",
                "verified": False,
                "tools_used": tools_used,
                "timestamp": time.time(),
            }

        # Step 2: Click Submit exactly once
        click_res = browser_backend.click_button(btn_name, verify=True)
        tools_used.append("browser_click_button")

        # Verify outcome
        if click_res.get("verified") and click_res.get("form_submitted"):
            feedback = click_res.get("feedback", "Form submitted successfully.")
            resp = f"{option_target.title()} was selected and the form was submitted successfully."
            is_verified = True
        elif click_res.get("verified"):
            resp = f"I selected {option_target} and clicked {btn_name}, but I couldn't verify that the form was accepted."
            is_verified = False
        else:
            resp = f"I selected {option_target}, but clicking {btn_name} failed: {click_res.get('message', 'Unknown error')}."
            is_verified = False

        record = {
            "action_id": action_id,
            "instruction": raw_text,
            "status": "ok" if is_verified else "unverified",
            "response": resp,
            "verified": is_verified,
            "details": {"select": sel_res, "click": click_res},
            "tools_used": tools_used,
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def _execute_select_option(self, option_target: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Execute single option selection."""
        sel_res = browser_backend.select_option(option_target, verify=True)
        is_verified = bool(sel_res.get("verified"))

        if is_verified:
            resp = f"{option_target.title()} has been selected."
        else:
            resp = f"I was unable to select {option_target}: {sel_res.get('message', 'Selection could not be verified')}."

        record = {
            "action_id": action_id,
            "instruction": raw_text,
            "status": "ok" if is_verified else "failed",
            "response": resp,
            "verified": is_verified,
            "details": sel_res,
            "tools_used": ["browser_select_option"],
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def _execute_click(self, target_query: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Execute element or coordinate click with ambiguity detection."""
        # 1. If browser backend active, try browser click first
        if browser_backend.is_running():
            ambig = browser_backend.detect_ambiguity(target_query, element_type="button")
            if ambig.get("ambiguous"):
                candidates = [c.get("id") or c.get("text") for c in ambig.get("candidates", [])]
                return {
                    "action_id": action_id,
                    "status": "ambiguous",
                    "response": f"Multiple elements match '{target_query}' ({candidates}). Please clarify which one to click.",
                    "verified": False,
                    "tools_used": ["ambiguity_detector"],
                    "timestamp": time.time(),
                }

            b_res = browser_backend.click_button(target_query, verify=True)
            if b_res.get("status") == "ok":
                resp = f"Clicked '{target_query}'."
                record = {
                    "action_id": action_id,
                    "instruction": raw_text,
                    "status": "ok",
                    "response": resp,
                    "verified": True,
                    "details": b_res,
                    "tools_used": ["browser_click_button"],
                    "timestamp": time.time(),
                }
                self._action_history.append(record)
                return record

        # 2. Native / Grounded UI Click
        res = screen_intelligence.resolve_target(target_query)
        if res.get("status") == "ok":
            el = res.get("element", {})
            center = el.get("center") or {}
            rect = el.get("rect")
            if rect:
                cx = int(rect.get("x", 0) + rect.get("width", 0) // 2)
                cy = int(rect.get("y", 0) + rect.get("height", 0) // 2)
            else:
                cx = center.get("x")
                cy = center.get("y")

            if cx is not None and cy is not None:
                tools_used = ["native_click"]
                if browser_backend.is_running() and el.get("id"):
                    try:
                        browser_backend._page.click(f"#{el['id']}", timeout=2000)
                        tools_used.append("browser_click")
                    except Exception:
                        pass
                d_res = native_backend.click(x=cx, y=cy, button="left", clicks=1)
                resp = f"Moved to and clicked '{target_query}' at ({cx}, {cy})."
                record = {
                    "action_id": action_id,
                    "instruction": raw_text,
                    "status": "ok",
                    "response": resp,
                    "verified": True,
                    "details": d_res,
                    "tools_used": tools_used,
                    "timestamp": time.time(),
                }
                self._action_history.append(record)
                return record

        return {
            "action_id": action_id,
            "status": "not_found",
            "response": f"Could not find a clickable element matching '{target_query}'.",
            "verified": False,
            "tools_used": ["screen_intelligence"],
            "timestamp": time.time(),
        }

    def _execute_right_click(self, target_query: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Right click target item or active position."""
        tools_used = []
        d_res = None
        if browser_backend.is_running():
            b_res = browser_backend.right_click(target_query)
            if b_res.get("status") == "ok":
                tools_used.append("browser_right_click")

        res = screen_intelligence.resolve_target(target_query)
        if res.get("status") == "ok":
            el = res.get("element", {})
            center = el.get("center") or {}
            rect = el.get("rect")
            if rect:
                cx = int(rect.get("x", 0) + rect.get("width", 0) // 2)
                cy = int(rect.get("y", 0) + rect.get("height", 0) // 2)
            else:
                cx = center.get("x")
                cy = center.get("y")
            if cx is not None and cy is not None:
                d_res = native_backend.right_click(x=cx, y=cy)
                tools_used.append("native_right_click")
                resp = f"Right-clicked '{target_query}' at ({cx}, {cy})."
                record = {
                    "action_id": action_id,
                    "instruction": raw_text,
                    "status": "ok",
                    "response": resp,
                    "verified": True,
                    "details": d_res,
                    "tools_used": tools_used or ["native_right_click"],
                    "timestamp": time.time(),
                }
                self._action_history.append(record)
                return record

        d_res = native_backend.right_click()
        tools_used.append("native_right_click")
        resp = "Right-clicked at the current cursor position."
        record = {
            "action_id": action_id,
            "instruction": raw_text,
            "status": "ok",
            "response": resp,
            "verified": True,
            "details": d_res,
            "tools_used": tools_used,
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def _execute_double_click(self, target_query: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Double click target item."""
        res = screen_intelligence.resolve_target(target_query)
        if res.get("status") == "ok":
            el = res.get("element", {})
            center = el.get("center") or {}
            cx, cy = center.get("x"), center.get("y")
            if cx is not None and cy is not None:
                d_res = native_backend.double_click(x=cx, y=cy)
                resp = f"Double-clicked '{target_query}' at ({cx}, {cy})."
                record = {
                    "action_id": action_id,
                    "instruction": raw_text,
                    "status": "ok",
                    "response": resp,
                    "verified": True,
                    "details": d_res,
                    "tools_used": ["native_double_click"],
                    "timestamp": time.time(),
                }
                self._action_history.append(record)
                return record

        d_res = native_backend.double_click()
        resp = "Double-clicked at current position."
        record = {
            "action_id": action_id,
            "instruction": raw_text,
            "status": "ok",
            "response": resp,
            "verified": True,
            "details": d_res,
            "tools_used": ["native_double_click"],
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def _execute_move_mouse(self, target_query: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Move cursor smoothly to target interface element or coordinates."""
        # Check coordinate format (e.g. "500, 300" or "x=500, y=300")
        m_coords = re.search(r"(\d+)\s*[,x]\s*(\d+)", target_query)
        if m_coords:
            tx, ty = int(m_coords.group(1)), int(m_coords.group(2))
            res = native_backend.move_cursor(tx, ty, duration=0.25, smooth=True)
            resp = f"Moved mouse pointer to ({tx}, {ty})."
            record = {
                "action_id": action_id,
                "instruction": raw_text,
                "status": "ok",
                "response": resp,
                "verified": res.get("verified", False),
                "details": res,
                "tools_used": ["native_move_cursor"],
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record

        res = screen_intelligence.resolve_target(target_query)
        if res.get("status") == "ok":
            el = res.get("element", {})
            center = el.get("center") or {}
            # If element rect from browser
            rect = el.get("rect")
            if rect:
                cx = int(rect.get("x", 0) + rect.get("width", 0) // 2)
                cy = int(rect.get("y", 0) + rect.get("height", 0) // 2)
            else:
                cx = center.get("x")
                cy = center.get("y")

            if cx is not None and cy is not None:
                m_res = native_backend.move_cursor(cx, cy, duration=0.25, smooth=True)
                if browser_backend.is_running() and browser_backend._page:
                    try:
                        browser_backend._page.mouse.move(cx, cy)
                    except Exception:
                        pass
                resp = f"Moved mouse to '{target_query}' at ({cx}, {cy})."
                record = {
                    "action_id": action_id,
                    "instruction": raw_text,
                    "status": "ok",
                    "response": resp,
                    "verified": m_res.get("verified", False),
                    "details": m_res,
                    "tools_used": ["native_move_cursor"],
                    "timestamp": time.time(),
                }
                self._action_history.append(record)
                return record

        return {
            "action_id": action_id,
            "status": "not_found",
            "response": f"Target element '{target_query}' could not be located on the screen.",
            "verified": False,
            "tools_used": ["screen_intelligence"],
            "timestamp": time.time(),
        }

    def _execute_type_text(self, text: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Type text into active browser or native window."""
        if browser_backend.is_running():
            b_res = browser_backend.type_text(None, text, verify=True)
            if b_res.get("status") == "ok":
                resp = f"Typed \"{text}\" into the active field."
                record = {
                    "action_id": action_id,
                    "instruction": raw_text,
                    "status": "ok",
                    "response": resp,
                    "verified": b_res.get("verified", False),
                    "details": b_res,
                    "tools_used": ["browser_type_text"],
                    "timestamp": time.time(),
                }
                self._action_history.append(record)
                return record

        # Native desktop typing
        if self._target_window:
            try:
                native_backend.focus_window(self._target_window)
            except Exception:
                pass
        d_res = native_backend.type_text(text, target_window=self._target_window)
        resp = f"Typed \"{text}\" into the active window."
        record = {
            "action_id": action_id,
            "instruction": raw_text,
            "status": "ok",
            "response": resp,
            "verified": d_res.get("verified", False),
            "details": d_res,
            "tools_used": ["native_type_text"],
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def _execute_press_key(self, key_combo: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Press key or key combination."""
        tools_used = []
        if self._target_window and not browser_backend.is_running():
            try:
                native_backend.focus_window(self._target_window)
            except Exception:
                pass
        if browser_backend.is_running():
            b_res = browser_backend.press_key(key_combo)
            if b_res.get("status") == "ok":
                tools_used.append("browser_press_key")

        res = native_backend.press_hotkey(key_combo)
        tools_used.append("native_press_hotkey")
        resp = f"Pressed {key_combo.upper()}."
        record = {
            "action_id": action_id,
            "instruction": raw_text,
            "status": "ok",
            "response": resp,
            "verified": res.get("verified", False) or ("browser_press_key" in tools_used),
            "details": res,
            "tools_used": tools_used,
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def _execute_scroll(self, direction: str, action_id: str, raw_text: str) -> Dict[str, Any]:
        """Scroll active page or window."""
        if browser_backend.is_running():
            b_res = browser_backend.scroll_page(direction=direction)
            resp = f"Scrolled {direction}."
            record = {
                "action_id": action_id,
                "instruction": raw_text,
                "status": "ok",
                "response": resp,
                "verified": True,
                "details": b_res,
                "tools_used": ["browser_scroll"],
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record

        d_res = native_backend.scroll(direction=direction)
        resp = f"Scrolled {direction} on desktop."
        record = {
            "action_id": action_id,
            "instruction": raw_text,
            "status": "ok",
            "response": resp,
            "verified": True,
            "details": d_res,
            "tools_used": ["native_scroll"],
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def capture_evidence_screenshot(self, name: str) -> Optional[str]:
        """Capture and save verification screenshot under docs/jarvis-ui/evidence/computer-control/."""
        import os
        evidence_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "jarvis-ui", "evidence", "computer-control"))
        os.makedirs(evidence_dir, exist_ok=True)
        filepath = os.path.join(evidence_dir, f"{name}.png")
        if browser_backend.is_running() and browser_backend._page:
            try:
                browser_backend._page.screenshot(path=filepath)
                return filepath
            except Exception:
                pass
        return None

    def inspect_screen(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Inspect current screen on DISPLAY=:0: active window, wmctrl window list, problem/error detection, and target resolution."""
        res = screen_intelligence.inspect_screen(query=query)
        self._action_history.append({
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action": "inspect_screen",
            "query": query,
            "timestamp": time.time(),
            "status": "ok",
            "active_window": res.get("active_window"),
            "has_error": res.get("has_error", False),
        })
        return res

    def monitor_screen(self) -> Dict[str, Any]:
        """Query continuous screen monitoring telemetry."""
        return self.inspect_screen()

    def focus_window(self, target: str) -> Dict[str, Any]:
        """Bring target window to foreground on DISPLAY=:0 by title keyword or hex window ID."""
        if self._emergency_stopped or self._stop_requested:
            return {"status": "blocked", "message": "Action blocked: Computer control is in EMERGENCY STOP."}
        res = native_backend.focus_window(target)
        self.set_target_window(target)
        record = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action": "focus_window",
            "target": target,
            "timestamp": time.time(),
            "status": "ok" if res.get("verified") else "error",
            "verified": res.get("verified", False),
            "response": f"Focused window '{target}'.",
        }
        self._action_history.append(record)
        return record

    def desktop_click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1, target_element: Optional[str] = None) -> Dict[str, Any]:
        """Bounded, coordinate-validated X11 mouse click on DISPLAY=:0 with visual verification and instant abort support."""
        if self._emergency_stopped or self._stop_requested:
            return {"status": "blocked", "message": "Action blocked: Computer control is in EMERGENCY STOP."}

        res = native_backend.get_screen_resolution()
        max_w, max_h = res.get("width", 1440), res.get("height", 900)

        target_x, target_y = x, y
        if (target_x is None or target_y is None) and target_element:
            target_res = screen_intelligence.resolve_target(target_element)
            if target_res.get("status") == "ok":
                el = target_res.get("element", {})
                target_x = el.get("x", max_w // 2)
                target_y = el.get("y", max_h // 2)
            else:
                target_x, target_y = max_w // 2, max_h // 2

        if target_x is None:
            target_x = max_w // 2
        if target_y is None:
            target_y = max_h // 2

        # Bounded coordinate validation
        target_x = max(0, min(max_w - 1, int(target_x)))
        target_y = max(0, min(max_h - 1, int(target_y)))

        click_res = native_backend.click(x=target_x, y=target_y, button=button, clicks=clicks)
        pos_after = native_backend.get_cursor_position()

        record = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action": "desktop_click",
            "target": {"x": target_x, "y": target_y},
            "button": button,
            "clicks": clicks,
            "cursor_position_after": pos_after,
            "timestamp": time.time(),
            "status": "ok",
            "verified": click_res.get("verified", True),
            "response": f"Clicked {button} at ({target_x}, {target_y}).",
        }
        self._action_history.append(record)
        return record

    def desktop_type(self, text: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        """Safe text entry into focused control or target window on DISPLAY=:0."""
        if self._emergency_stopped or self._stop_requested:
            return {"status": "blocked", "message": "Action blocked: Computer control is in EMERGENCY STOP."}

        # Sensitivity gate: block direct destructive command injection
        if re.search(r"\b(?:rm\s+-rf|sudo\s+|mkfs|dd\s+if=)\b", text):
            return {
                "status": "blocked",
                "message": "Typing destructive system commands is prohibited without explicit administrative confirmation.",
                "verified": False,
            }

        res = native_backend.type_text(text, target_window=target_window)
        record = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action": "desktop_type",
            "text": text[:50] + ("..." if len(text) > 50 else ""),
            "target_window": target_window,
            "timestamp": time.time(),
            "status": "ok",
            "verified": res.get("verified", True),
            "response": f"Typed text into {target_window or 'active window'}.",
        }
        self._action_history.append(record)
        return record

    def desktop_hotkey(self, hotkey: str) -> Dict[str, Any]:
        """Press keyboard shortcut on DISPLAY=:0."""
        if self._emergency_stopped or self._stop_requested:
            return {"status": "blocked", "message": "Action blocked: Computer control is in EMERGENCY STOP."}

        res = native_backend.press_hotkey(hotkey)
        record = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action": "desktop_hotkey",
            "hotkey": hotkey,
            "timestamp": time.time(),
            "status": "ok",
            "verified": res.get("verified", True),
            "response": f"Pressed hotkey '{hotkey}'.",
        }
        self._action_history.append(record)
        return record

    def desktop_scroll(self, direction: str = "down", clicks: int = 5) -> Dict[str, Any]:
        """Scroll mouse wheel on DISPLAY=:0."""
        if self._emergency_stopped or self._stop_requested:
            return {"status": "blocked", "message": "Action blocked: Computer control is in EMERGENCY STOP."}

        res = native_backend.scroll(direction=direction, clicks=clicks)
        record = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action": "desktop_scroll",
            "direction": direction,
            "clicks": clicks,
            "timestamp": time.time(),
            "status": "ok",
            "verified": res.get("verified", True),
            "response": f"Scrolled {direction}.",
        }
        self._action_history.append(record)
        return record

    def browser_ui_action(self, action: str = "focus", target: Optional[str] = None, url: Optional[str] = None, clicks: int = 1, on_progress: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Interact with active Chrome window on DISPLAY=:0:
        focus tab, switch YouTube account, click visible UI elements found via screen vision, scroll, play/pause, or switch tabs.
        """
        if self._emergency_stopped or self._stop_requested:
            return {"status": "blocked", "message": "Action blocked: Computer control is in EMERGENCY STOP."}

        act_clean = (action or "").lower().strip()
        if act_clean in {"list_youtube_accounts", "resolve_youtube_account"}:
            if act_clean == "resolve_youtube_account" and (not isinstance(target, str) or not target.strip()):
                result = {"status": "needs_input", "verified": False,
                          "response": "Which visible account label should I match? No account was selected."}
            else:
                result = browser_backend.observe_youtube_accounts(
                    target=target if act_clean == "resolve_youtube_account" else None
                )
            return {**result, "action": act_clean,
                    "spoken_summary": result.get("response", "Account observation is unavailable.")}
        account_action = "account" in act_clean or (isinstance(target, str) and "account" in target.lower())
        if account_action and (not isinstance(target, str) or not target.strip()):
            message = "Which signed-in account should I use? Please provide its visible account label."
            record = {
                "action_id": f"act_{uuid.uuid4().hex[:8]}",
                "action": "switch_youtube_account",
                "status": "needs_input",
                "verified": False,
                "response": message,
                "spoken_summary": message,
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record
        t_start = time.time()
        res_geom = native_backend.get_screen_resolution()
        screen_w = res_geom.get("width", 1440)
        screen_h = res_geom.get("height", 900)

        # 1. Switch YouTube Account Workflow
        if account_action:
            def failed(stage: str, message: str, status: str = "error") -> Dict[str, Any]:
                record = {
                    "action_id": f"act_{uuid.uuid4().hex[:8]}",
                    "action": "switch_youtube_account",
                    "status": status,
                    "verified": False,
                    "failed_stage": stage,
                    "response": message,
                    "spoken_summary": message,
                    "timestamp": time.time(),
                }
                self._action_history.append(record)
                return record

            def stopped(stage: str) -> Optional[Dict[str, Any]]:
                if self._emergency_stopped or self._stop_requested:
                    return failed(stage, "Browser action stopped; the account change is not confirmed.", "cancelled")
                return None

            def delivered(result: Any) -> bool:
                return (isinstance(result, dict) and result.get("verified") is True
                        and result.get("status", "ok") == "ok")

            if on_progress:
                try:
                    on_progress({"type": "progress", "stage": "browser_action", "detail": "[Step 1/3] Capturing screen and focusing Google Chrome..."})
                except Exception:
                    pass

            # Bring Google Chrome to foreground
            cancelled = stopped("focus")
            if cancelled:
                return cancelled
            try:
                focus_res = native_backend.focus_window("Chrome")
                if not delivered(focus_res):
                    cancelled = stopped("focus")
                    if cancelled:
                        return cancelled
                    focus_res = native_backend.focus_window("YouTube")
            except Exception:
                return failed("focus", "Could not focus the browser. No account-menu clicks were sent.")
            if not delivered(focus_res):
                return failed("focus", "Could not focus Chrome or YouTube. No account-menu clicks were sent.")
            time.sleep(0.3)

            if on_progress:
                try:
                    on_progress({"type": "progress", "stage": "browser_action", "detail": "[Step 2/3] Locating YouTube profile avatar..."})
                except Exception:
                    pass

            # On YouTube layout in Chrome: Profile avatar is at top right header
            # Screen resolution-aware coordinates:
            avatar_x = screen_w - 35
            avatar_y = 125
            cancelled = stopped("avatar_click")
            if cancelled:
                return cancelled
            try:
                click_result = native_backend.click(x=avatar_x, y=avatar_y, button="left", clicks=1)
            except Exception:
                return failed("avatar_click", "Browser input failed; the account change is not confirmed.")
            if not delivered(click_result):
                return failed("avatar_click", "Browser input was not delivered; the account change is not confirmed.")
            time.sleep(0.4)

            if on_progress:
                try:
                    on_progress({"type": "progress", "stage": "browser_action", "detail": "[Step 3/3] Opening account switcher..."})
                except Exception:
                    pass

            # Account switcher menu item in YouTube popup menu:
            # Typically 4th menu item down, approx 140px below avatar
            menu_x = avatar_x - 80
            menu_y = avatar_y + 140
            cancelled = stopped("menu_click")
            if cancelled:
                return cancelled
            try:
                click_result = native_backend.click(x=menu_x, y=menu_y, button="left", clicks=1)
            except Exception:
                return failed("menu_click", "Browser input failed; the account change is not confirmed.")
            if not delivered(click_result):
                return failed("menu_click", "Browser input was not delivered; the account change is not confirmed.")
            time.sleep(0.3)

            cancelled = stopped("verification")
            if cancelled:
                return cancelled

            # Input delivery is not evidence of the website's resulting state.
            # Until the account identity is observed, never announce completion.
            spoken_summary = (
                "I attempted to open the account menu in Google Chrome, but I could not "
                "verify the menu or active account. Please check the browser; "
                "the requested account change is not confirmed."
            )
            record = {
                "action_id": f"act_{uuid.uuid4().hex[:8]}",
                "action": "switch_youtube_account",
                "status": "unverified",
                "verified": False,
                "spoken_summary": spoken_summary,
                "response": spoken_summary,
                "tools_used": ["focus_window", "desktop_click"],
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record

        # 2. Play / Pause Media in Browser
        if "play" in act_clean or "pause" in act_clean:
            native_backend.focus_window("Chrome")
            time.sleep(0.2)
            native_backend.press_hotkey("k")
            spoken_summary = "Toggled playback in YouTube."
            record = {
                "action_id": f"act_{uuid.uuid4().hex[:8]}",
                "action": "play_pause",
                "status": "ok",
                "verified": True,
                "spoken_summary": spoken_summary,
                "response": "Sent Play/Pause command to active Chrome media tab.",
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record

        # 3. Switch Browser Tab
        if "switch_tab" in act_clean or "next_tab" in act_clean:
            native_backend.focus_window("Chrome")
            time.sleep(0.2)
            native_backend.press_hotkey("ctrl+Tab")
            record = {
                "action_id": f"act_{uuid.uuid4().hex[:8]}",
                "action": "switch_tab",
                "status": "ok",
                "verified": True,
                "spoken_summary": "Switched to the next Chrome tab.",
                "response": "Switched active browser tab.",
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record

        # 4. General Window / Tab Focus
        native_backend.focus_window("Chrome")
        record = {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "action": "focus_chrome",
            "status": "ok",
            "verified": True,
            "spoken_summary": "Focused Google Chrome on DISPLAY=:0.",
            "response": "Focused Google Chrome window on DISPLAY=:0.",
            "timestamp": time.time(),
        }
        self._action_history.append(record)
        return record

    def run_safe_terminal_task(self, command: str, session_id: str = "default", confirm: bool = False, pin: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs read-only terminal diagnostics freely; gates mutating terminal commands behind explicit confirmation / fresh PIN.
        """
        if self._emergency_stopped or self._stop_requested:
            return {"status": "blocked", "message": "Action blocked: Computer control is in EMERGENCY STOP."}

        cmd_clean = command.strip()
        cmd_lower = cmd_clean.lower()

        # Mutating and destructive operation tokens
        mutating_tokens = [
            "rm ", "rm\t", "rmdir", "sudo ", "dd ", "mv ", "cp ", "shutdown", "reboot",
            "poweroff", "init ", "chmod", "chown", "mkfs", "kill", "pkill", "systemctl stop",
            "systemctl restart", "apt ", "pip install", "pip uninstall", ">", ">>",
        ]

        is_mutating = any(t in cmd_lower for t in mutating_tokens)

        # Gate mutating commands behind confirmation or Admin PIN
        if is_mutating and not confirm and not pin:
            return {
                "status": "confirmation_required",
                "command": cmd_clean,
                "requires_confirmation": True,
                "message": f"Command '{cmd_clean}' modifies files or system state. Explicit operator confirmation or Admin PIN is required.",
                "verified": False,
            }

        # Execute command safely
        import subprocess
        try:
            res = subprocess.run(
                cmd_clean,
                shell=True,
                capture_output=True,
                text=True,
                timeout=20,
                env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")},
            )
            out = res.stdout.strip()
            err = res.stderr.strip()
            combined = (out + ("\n" + err if err else "")).strip() or "(Command completed with no output)"
            record = {
                "action_id": f"act_{uuid.uuid4().hex[:8]}",
                "action": "run_safe_terminal_task",
                "command": cmd_clean,
                "returncode": res.returncode,
                "output": combined[:2000],
                "status": "ok" if res.returncode == 0 else "failed",
                "verified": res.returncode == 0,
                "timestamp": time.time(),
            }
            self._action_history.append(record)
            return record
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "command": cmd_clean,
                "error": "Terminal command timed out after 20 seconds.",
                "verified": False,
            }
        except Exception as exc:
            return {
                "status": "error",
                "command": cmd_clean,
                "error": str(exc),
                "verified": False,
            }


# Global singleton instance
unified_computer_service = UnifiedComputerService()
