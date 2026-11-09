"""
JARVIS Central Desktop Action Engine
Coordinates high-level desktop and terminal operations with verified execution,
deterministic action auditing, and structured result formatting.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from tools.desktop.app_launcher import app_launcher
from tools.desktop.browser_controller import browser_controller
from tools.desktop.file_search import file_search
from tools.desktop.program_runner import program_runner
from tools.desktop.project_manager import project_manager
from tools.desktop.window_manager import window_manager
from tools.terminal.terminal_manager import terminal_engine

logger = logging.getLogger("JARVIS-DESKTOP-ENGINE")


class DesktopActionEngine:
    """Central orchestrator for all verified desktop actions."""

    def __init__(self) -> None:
        self.action_history: List[Dict[str, Any]] = []

    def _record_action(
        self,
        action_type: str,
        args: Dict[str, Any],
        result: Dict[str, Any],
        t_start: float,
        permission: str = "standard",
    ) -> Dict[str, Any]:
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        t_end = time.time()
        success = result.get("success", result.get("status") in ("opened", "SUCCESS", "completed"))
        record = {
            "action_id": action_id,
            "operation_type": action_type,
            "validated_arguments": args,
            "start_time": t_start,
            "end_time": t_end,
            "duration_ms": int((t_end - t_start) * 1000),
            "actual_result": result,
            "success": success,
            "exit_status": result.get("exit_code", 0 if success else 1),
            "error_details": result.get("error") or result.get("stderr"),
            "permission_requirement": permission,
        }
        self.action_history.append(record)
        return record

    def open_application(self, app_name: str, target: Optional[str] = None, new_window: bool = False) -> Dict[str, Any]:
        """Launch an installed desktop application with verification."""
        t_start = time.time()
        res = app_launcher.launch_app(app_name, target=target, new_window=new_window)
        return self._record_action("open_application", {"app_name": app_name, "target": target}, res, t_start)

    def open_url(self, url: str, browser: str = "chrome") -> Dict[str, Any]:
        """Open web URL in requested browser."""
        t_start = time.time()
        res = browser_controller.open_url(url, browser=browser)
        return self._record_action("open_url", {"url": url, "browser": browser}, res, t_start)

    def search_youtube(self, query: str, browser: str = "chrome") -> Dict[str, Any]:
        """Search YouTube in browser."""
        t_start = time.time()
        res = browser_controller.search_youtube(query, browser=browser)
        return self._record_action("search_youtube", {"query": query, "browser": browser}, res, t_start)

    def open_project(self, project_name_or_path: str, editor: str = "vscode") -> Dict[str, Any]:
        """Open a project in VS Code or Antigravity IDE."""
        t_start = time.time()
        res = project_manager.open_project(project_name_or_path, editor=editor)
        return self._record_action("open_project", {"project": project_name_or_path, "editor": editor}, res, t_start)

    def search_files(
        self,
        directory: Optional[str] = None,
        pattern: str = "*",
        extension: Optional[str] = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """Search directory for files matching pattern or extension."""
        t_start = time.time()
        files = file_search.search_files(directory=directory, pattern=pattern, extension=extension, max_results=max_results)
        res = {"success": True, "count": len(files), "files": files}
        return self._record_action("search_files", {"directory": directory, "pattern": pattern, "extension": extension}, res, t_start)

    def search_file_contents(
        self,
        query: str,
        directory: Optional[str] = None,
        file_pattern: Optional[str] = None,
        max_results: int = 25,
    ) -> Dict[str, Any]:
        """Search text contents inside source files."""
        t_start = time.time()
        matches = file_search.search_content(query=query, directory=directory, file_pattern=file_pattern, max_results=max_results)
        res = {"success": True, "count": len(matches), "matches": matches}
        return self._record_action("search_file_contents", {"query": query, "directory": directory}, res, t_start)

    def execute_terminal(
        self,
        command: str,
        session_id: Optional[str] = None,
        confirm: bool = False,
        confirmation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute command in terminal session."""
        t_start = time.time()
        res = terminal_engine.execute_command(
            command,
            session_id=session_id,
            confirm=confirm,
            confirmation_token=confirmation_token,
        )
        perm = "dangerous" if res.get("requires_confirmation") else "standard"
        return self._record_action("execute_terminal", {"command": command, "session_id": session_id}, res, t_start, permission=perm)

    def run_program(
        self,
        file_path: str,
        working_dir: Optional[str] = None,
        args: Optional[List[str]] = None,
        background: bool = False,
    ) -> Dict[str, Any]:
        """Execute program script."""
        t_start = time.time()
        res = program_runner.run_program(file_path, working_dir=working_dir, args=args, background=background)
        return self._record_action("run_program", {"file_path": file_path, "cwd": working_dir}, res, t_start)

    def get_desktop_status(self) -> Dict[str, Any]:
        """Get summary of desktop windows, active application, and resolution."""
        t_start = time.time()
        res = window_manager.get_desktop_status()
        res["success"] = True
        return self._record_action("get_desktop_status", {}, res, t_start)

    def get_active_window(self) -> Dict[str, Any]:
        """Get currently active desktop window."""
        t_start = time.time()
        res = window_manager.get_active_window()
        res["success"] = True
        return self._record_action("get_active_window", {}, res, t_start)

    def switch_application(self, query: str) -> Dict[str, Any]:
        """Focus window by title or app name."""
        t_start = time.time()
        res = window_manager.switch_window(query)
        return self._record_action("switch_application", {"query": query}, res, t_start)

    # Phase 4 Visual Computer-Use Additions
    def capture_screenshot(self, target: str = "fullscreen") -> Dict[str, Any]:
        """Capture screenshot of fullscreen or active window."""
        t_start = time.time()
        from tools.desktop.desktop_perception import desktop_perception
        if target == "active_window":
            res = desktop_perception.capture_active_window()
        else:
            res = desktop_perception.capture_fullscreen()
        return self._record_action("capture_screenshot", {"target": target}, res, t_start)

    def observe_screen(self) -> Dict[str, Any]:
        """Comprehensive observation of screen state, windows, and visual snapshot."""
        t_start = time.time()
        from tools.desktop.desktop_perception import desktop_perception
        res = desktop_perception.observe_desktop()
        return self._record_action("observe_screen", {}, res, t_start)

    def find_ui_element(self, query: str) -> Dict[str, Any]:
        """Locate interface element matching query."""
        t_start = time.time()
        from tools.desktop.element_detector import element_detector
        from tools.desktop.desktop_perception import desktop_perception
        act_win = desktop_perception.get_active_window()
        elem = element_detector.find_element(query, act_win)
        res = {"success": elem is not None, "element": elem.to_dict() if elem else None}
        return self._record_action("find_ui_element", {"query": query}, res, t_start)

    def click_ui_element(self, query: str) -> Dict[str, Any]:
        """Locate element semantically and click with verification."""
        t_start = time.time()
        from tools.desktop.computer_action_engine import computer_action_engine
        res = computer_action_engine.click_named_element(query)
        return self._record_action("click_ui_element", {"query": query}, res, t_start)

    def type_text(self, text: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        """Type text string with verification."""
        t_start = time.time()
        from tools.desktop.computer_action_engine import computer_action_engine
        res = computer_action_engine.type_text(text, target_window=target_window)
        return self._record_action("type_text", {"text": text, "target_window": target_window}, res, t_start)

    def scroll_screen(self, direction: str = "down", clicks: int = 5) -> Dict[str, Any]:
        """Scroll screen down or up with verification."""
        t_start = time.time()
        from tools.desktop.computer_action_engine import computer_action_engine
        res = computer_action_engine.scroll_page(direction=direction, clicks=clicks)
        return self._record_action("scroll_screen", {"direction": direction, "clicks": clicks}, res, t_start)


desktop_action_engine = DesktopActionEngine()
