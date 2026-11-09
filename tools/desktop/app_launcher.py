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
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,  # Detach process group so it lives independently
            )
            # Give application a moment to initialize
            time.sleep(0.4)
            running = proc.poll() is None or self.is_running(app_name)

            dur_ms = int((time.time() - t_start) * 1000)
            return {
                "action_id": action_id,
                "status": "opened" if running else "exited_early",
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
