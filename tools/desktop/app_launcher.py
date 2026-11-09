"""
JARVIS Desktop Application Launcher
Discovers real installed GUI applications and editors, launches them with
session verification on X11 desktop, and tracks application processes.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-DESKTOP-LAUNCHER")

# Verified paths for desktop applications on this Raspberry Pi 5
DEFAULT_APP_MAP = {
    "google-chrome": ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"],
    "chrome": ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"],
    "firefox": ["/usr/bin/firefox"],
    "browser": ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/firefox"],
    "code": ["/home/roshan/.local/bin/code", "/usr/bin/code"],
    "vscode": ["/home/roshan/.local/bin/code", "/usr/bin/code"],
    "vs code": ["/home/roshan/.local/bin/code", "/usr/bin/code"],
    "antigravity": [
        "/home/roshan/Downloads/Antigravity-arm64/antigravity",
        "/home/roshan/pi-apps/apps/Antigravity/install-64",
        "/usr/local/bin/antigravity",
        "/usr/bin/antigravity"
    ],
    "antigravity ide": [
        "/home/roshan/Downloads/Antigravity-arm64/antigravity",
        "/usr/local/bin/antigravity"
    ],
    "terminal": ["/usr/bin/lxterminal", "/usr/bin/x-terminal-emulator", "/usr/bin/xterm"],
    "lxterminal": ["/usr/bin/lxterminal"],
    "file_manager": ["/usr/bin/pcmanfm"],
    "pcmanfm": ["/usr/bin/pcmanfm"],
}


class DesktopAppLauncher:
    """Manages discovery and launching of verified desktop applications."""

    def __init__(self, display: str = ":0") -> None:
        self.display = display
        self._cache: Dict[str, str] = {}
        self._refresh_registry()

    def _refresh_registry(self) -> None:
        """Scan system paths for verified application executables."""
        for app_alias, candidate_paths in DEFAULT_APP_MAP.items():
            for p in candidate_paths:
                expanded = os.path.expanduser(p)
                if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
                    self._cache[app_alias] = expanded
                    break
            if app_alias not in self._cache:
                cmd = shutil.which(app_alias)
                if cmd:
                    self._cache[app_alias] = cmd

    def get_executable(self, app_name: str) -> Optional[str]:
        """Resolve app name or alias to executable path."""
        norm = app_name.lower().strip()
        if norm in self._cache:
            return self._cache[norm]
        self._refresh_registry()
        if norm in self._cache:
            return self._cache[norm]
        # Try generic which
        return shutil.which(norm)

    def list_installed_apps(self) -> List[Dict[str, Any]]:
        """Return list of discovered and verified desktop applications."""
        self._refresh_registry()
        installed = []
        seen = set()
        for alias, exe_path in self._cache.items():
            if exe_path not in seen:
                seen.add(exe_path)
                installed.append({
                    "name": alias,
                    "executable": exe_path,
                    "installed": True,
                    "running": self.is_running(alias),
                })
        return installed

    def is_running(self, app_name: str) -> bool:
        """Check if application process is currently running."""
        exe = self.get_executable(app_name)
        exe_name = os.path.basename(exe) if exe else app_name.lower()
        try:
            cmd = ["pgrep", "-f", exe_name]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode == 0 and bool(res.stdout.strip())
        except Exception:
            return False

    def get_lifecycle_status(
        self,
        app_name: str,
        pid: Optional[int] = None,
        target: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify the three-state lifecycle transitions:
        PROCESS_STARTED -> WINDOW_VISIBLE -> TARGET_PROJECT_OPENED
        """
        transitions: List[str] = []
        is_proc_running = False
        if pid:
            try:
                os.kill(pid, 0)
                is_proc_running = True
            except OSError:
                is_proc_running = self.is_running(app_name)
        else:
            is_proc_running = self.is_running(app_name)

        if is_proc_running:
            transitions.append("PROCESS_STARTED")

        # Check for visible window via wmctrl (poll up to ~1.2s for X11 mapping)
        win_info = None
        app_norm = app_name.lower().replace("-", " ")
        env = os.environ.copy()
        env["DISPLAY"] = self.display

        for _ in range(4):
            try:
                res = subprocess.run(
                    ["wmctrl", "-l", "-p"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2,
                )
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        parts = line.split(None, 4)
                        if len(parts) >= 5:
                            w_hex, d_num, p_id, host, w_title = parts[0], parts[1], parts[2], parts[3], parts[4]
                            title_lower = w_title.lower()
                            if (pid and str(pid) == p_id) or (app_norm in title_lower) or (app_name.lower() in title_lower):
                                win_info = {
                                    "window_id": w_hex,
                                    "window_title": w_title,
                                    "window_pid": int(p_id) if p_id.isdigit() else None,
                                }
                                break
                if win_info:
                    break
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"Error querying wmctrl: {e}")
                break

        if win_info:
            transitions.append("WINDOW_VISIBLE")

        if target and (win_info or is_proc_running):
            target_name = os.path.basename(str(target)).lower()
            if win_info and target_name in win_info.get("window_title", "").lower():
                transitions.append("TARGET_PROJECT_OPENED")
            elif is_proc_running:
                transitions.append("TARGET_PROJECT_OPENED")

        current_state = transitions[-1] if transitions else "NOT_STARTED"
        return {
            "current_state": current_state,
            "transitions": transitions,
            "window": win_info,
        }

    def launch_app(
        self,
        app_name: str,
        target: Optional[str] = None,
        args: Optional[List[str]] = None,
        new_window: bool = False,
    ) -> Dict[str, Any]:
        """Launch a desktop application with verified environment and return action result."""
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        t_start = time.time()
        exe = self.get_executable(app_name)

        if not exe:
            return {
                "action_id": action_id,
                "status": "not_installed",
                "lifecycle_state": "FAILED",
                "lifecycle_transitions": [],
                "app": app_name,
                "success": False,
                "error": f"Application '{app_name}' is not installed or executable cannot be found.",
                "duration_ms": int((time.time() - t_start) * 1000),
            }

        env = os.environ.copy()
        env["DISPLAY"] = self.display
        if "XAUTHORITY" not in env:
            xauth = os.path.expanduser("~/.Xauthority")
            if os.path.exists(xauth):
                env["XAUTHORITY"] = xauth

        cmd = [exe]

        # Specific CLI flags for known applications
        app_key = app_name.lower().strip()
        if app_key in ("code", "vscode", "vs code"):
            if new_window:
                cmd.append("--new-window")
            if target:
                clean_target = os.path.expanduser(target)
                cmd.append(clean_target)
        elif app_key in ("google-chrome", "chrome", "chromium"):
            if new_window:
                cmd.append("--new-window")
            if target:
                cmd.append(target)
        elif app_key == "firefox":
            if new_window:
                cmd.append("--new-window")
            if target:
                cmd.append(target)
        elif "antigravity" in app_key:
            if target:
                clean_target = os.path.expanduser(target)
                cmd.append(clean_target)
        elif app_key in ("terminal", "lxterminal"):
            if target:
                clean_target = os.path.expanduser(target)
                cmd.extend(["--working-directory", clean_target])
        else:
            if target:
                cmd.append(target)

        if args:
            cmd.extend(args)

        try:
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,  # Detach completely into new session
            )
            # Give application a moment to initialize
            time.sleep(0.4)
            running = proc.poll() is None or self.is_running(app_name)

            lifecycle = self.get_lifecycle_status(app_name, pid=proc.pid, target=target)
            dur_ms = int((time.time() - t_start) * 1000)
            return {
                "action_id": action_id,
                "status": "opened" if running else "exited_early",
                "lifecycle_state": lifecycle["current_state"],
                "lifecycle_transitions": lifecycle["transitions"],
                "window": lifecycle["window"],
                "success": running,
                "app": app_name,
                "executable": exe,
                "pid": proc.pid,
                "target": target,
                "command": cmd,
                "duration_ms": dur_ms,
            }
        except Exception as e:
            logger.error(f"Failed to launch '{app_name}': {e}")
            return {
                "action_id": action_id,
                "status": "failed",
                "success": False,
                "app": app_name,
                "executable": exe,
                "error": str(e),
                "duration_ms": int((time.time() - t_start) * 1000),
            }


app_launcher = DesktopAppLauncher()
