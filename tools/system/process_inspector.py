"""
JARVIS OS — Safe Read-Only Process & Desktop Window Inspector.
Lists open desktop windows (via wmctrl on DISPLAY=:0), top CPU/RAM processes (via psutil),
and core JARVIS service states without leaking secrets or commandline arguments.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import Any, Dict, List, Optional
import psutil

logger = logging.getLogger("JARVIS.System.ProcessInspector")


class ProcessInspector:
    """Safe, read-only process and desktop window inspector."""

    def __init__(self, default_display: str = ":0"):
        self.default_display = default_display

    def get_open_windows(self, display: Optional[str] = None) -> List[Dict[str, Any]]:
        """List open desktop windows via wmctrl without executing mutating commands."""
        disp = display or os.environ.get("DISPLAY", self.default_display)
        windows: List[Dict[str, Any]] = []
        try:
            res = subprocess.run(
                ["wmctrl", "-l", "-p", "-G"],
                env={**os.environ, "DISPLAY": disp},
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            for line in res.stdout.splitlines():
                parts = line.split(None, 8)
                if len(parts) >= 8:
                    win_id = parts[0]
                    desktop_id = int(parts[1]) if parts[1].lstrip('-').isdigit() else -1
                    pid = int(parts[2]) if parts[2].isdigit() else 0
                    x = int(parts[3])
                    y = int(parts[4])
                    w = int(parts[5])
                    h = int(parts[6])
                    client = parts[7]
                    title = parts[8] if len(parts) > 8 else "Untitled"

                    # Skip system desktop root or sticky pager if desired, but keep normal windows
                    if desktop_id != -1 or title not in ("Desktop", "xfce4-panel", "panel"):
                        windows.append({
                            "window_id": win_id,
                            "desktop": desktop_id,
                            "pid": pid,
                            "client": client,
                            "title": title,
                            "geometry": {"x": x, "y": y, "width": w, "height": h},
                        })
        except Exception as e:
            logger.warning("Failed to list open windows: %s", e)

        return windows

    def get_top_processes(self, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Collect top processes by CPU and RAM usage.
        
        Strictly omits command-line arguments and environment variables to prevent secret leakage.
        """
        procs: List[Dict[str, Any]] = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
            try:
                info = p.info
                mem_bytes = info['memory_info'].rss if info.get('memory_info') else 0
                procs.append({
                    "pid": info['pid'],
                    "name": info.get('name') or "unknown",
                    "user": info.get('username') or "unknown",
                    "cpu_pct": info.get('cpu_percent') or 0.0,
                    "memory_mb": round(mem_bytes / (1024 * 1024), 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug("Error inspecting process: %s", e)
                continue

        # Top by CPU
        top_cpu = sorted(procs, key=lambda x: x["cpu_pct"], reverse=True)[:limit]
        # Top by RAM
        top_ram = sorted(procs, key=lambda x: x["memory_mb"], reverse=True)[:limit]

        return {
            "top_cpu": top_cpu,
            "top_ram": top_ram,
            "total_process_count": len(procs),
        }

    def get_service_states(self) -> Dict[str, Dict[str, Any]]:
        """Inspect core JARVIS systemd service states."""
        services: Dict[str, Dict[str, Any]] = {}
        for sname in ("jarvis-core", "jarvis-backend", "jarvis-voice"):
            active_str = "inactive"
            try:
                # Check system level
                res = subprocess.run(["systemctl", "is-active", sname], capture_output=True, text=True, timeout=2, check=False)
                active_str = res.stdout.strip()
                if active_str != "active":
                    # Check user level
                    user_env = os.environ.copy()
                    user_env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
                    res_user = subprocess.run(["systemctl", "--user", "is-active", sname], capture_output=True, text=True, timeout=2, check=False, env=user_env)
                    if res_user.stdout.strip() == "active":
                        active_str = "active"
                    elif not active_str:
                        active_str = res_user.stdout.strip() or "inactive"
            except Exception as e:
                active_str = f"error: {e}"

            services[sname] = {
                "active": active_str == "active",
                "status": active_str,
            }

        return services

    def get_running_overview(self, limit: int = 10) -> Dict[str, Any]:
        """Generate structured status and markdown summary for running apps and processes."""
        windows = self.get_open_windows()
        proc_data = self.get_top_processes(limit=limit)
        services = self.get_service_states()

        # Build markdown summary
        md_lines = [
            "🖥️ **Running Software & Desktop Processes**",
            "",
            f"### 🪟 Open Desktop Windows ({len(windows)})",
        ]

        if windows:
            for w in windows:
                md_lines.append(f"- `[{w['window_id']}]` **{w['title']}** (PID: {w['pid']})")
        else:
            md_lines.append("- *No top-level application windows detected on DISPLAY=:0.*")

        md_lines.extend([
            "",
            "### ⚙️ Core JARVIS Services",
            f"- **`jarvis-core.service`**: `{'ACTIVE' if services.get('jarvis-core', {}).get('active') or services.get('jarvis-backend', {}).get('active') else 'INACTIVE'}` (Port 8000)",
            f"- **`jarvis-voice.service`**: `{'ACTIVE' if services.get('jarvis-voice', {}).get('active') else 'INACTIVE'}` (Single microphone owner)",
            "",
            f"### 🚀 Top Running Processes by CPU (Total: {proc_data['total_process_count']})",
            "| PID | Name | User | CPU % | RAM (MB) |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])

        for p in proc_data["top_cpu"][:8]:
            md_lines.append(f"| {p['pid']} | `{p['name']}` | {p['user']} | {p['cpu_pct']}% | {p['memory_mb']} MB |")

        md_lines.extend([
            "",
            "### 💾 Top Running Processes by RAM",
            "| PID | Name | User | RAM (MB) | CPU % |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])

        for p in proc_data["top_ram"][:8]:
            md_lines.append(f"| {p['pid']} | `{p['name']}` | {p['user']} | {p['memory_mb']} MB | {p['cpu_pct']}% |")

        markdown_text = "\n".join(md_lines)

        return {
            "status": "ok",
            "windows": windows,
            "processes": proc_data,
            "services": services,
            "markdown": markdown_text,
        }


process_inspector = ProcessInspector()
