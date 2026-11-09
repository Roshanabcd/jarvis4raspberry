"""
Google Antigravity CLI Adapter for JARVIS OS.
Integrates with `agy` for non-interactive coding, code inspection, and repairs.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

from tools.agents.adapters.base import BaseAgentAdapter
from tools.agents.models import AgentCapabilities, AgentMetadata, AgentStatus, AgentTask, ProblemContext

logger = logging.getLogger("JARVIS.AntigravityAdapter")


class AntigravityAdapter(BaseAgentAdapter):
    """Adapter for Google Antigravity CLI (`agy`)."""

    def __init__(self, cli_path: Optional[str] = None):
        super().__init__(agent_id="antigravity", display_name="Google Antigravity")
        self.cli_path = cli_path or shutil.which("agy") or "/home/roshan/.local/bin/agy"
        self._cached_meta: Optional[AgentMetadata] = None

    def discover(self) -> AgentMetadata:
        """Inspect agy executable, version, auth status, and models."""
        installed = os.path.exists(self.cli_path) and os.access(self.cli_path, os.X_OK)
        if not installed:
            return AgentMetadata(
                id=self.agent_id,
                display_name=self.display_name,
                installed=False,
                authenticated=False,
                status=AgentStatus.NOT_INSTALLED,
                error_message="Antigravity CLI ('agy') not found on system.",
            )

        # Detect version
        version = "Unknown"
        try:
            res_v = subprocess.run([self.cli_path, "--version"], capture_output=True, text=True, timeout=5)
            if res_v.returncode == 0:
                version = res_v.stdout.strip()
        except Exception as e:
            logger.warning("Failed to check agy version: %s", e)

        # Detect authentication and models
        authenticated = False
        models: List[str] = []
        try:
            res_m = subprocess.run([self.cli_path, "models"], capture_output=True, text=True, timeout=25)
            if res_m.returncode == 0 and res_m.stdout:
                authenticated = True
                for line in res_m.stdout.splitlines():
                    match = re.match(r"^\s*([a-zA-Z0-9_\-\.]+)\s+", line)
                    if match and not line.strip().startswith("Fetching"):
                        models.append(match.group(1))
        except Exception as e:
            logger.warning("Failed to check agy models/auth: %s", e)

        caps = AgentCapabilities(
            supports_noninteractive=True,
            supports_file_editing=True,
            supports_shell=True,
            supports_structured_output=True,
            supports_review=True,
            supports_sandbox=True,
            models=models or ["gemini-3.8-flash-high", "claude-sonnet-4-6"],
        )

        meta = AgentMetadata(
            id=self.agent_id,
            display_name=self.display_name,
            installed=True,
            authenticated=authenticated,
            version=version,
            cli_path=self.cli_path,
            capabilities=caps,
            permission_mode="workspace_scoped",
            last_health_check=time.time(),
            status=AgentStatus.READY if authenticated else AgentStatus.UNAUTHENTICATED,
        )
        self._cached_meta = meta
        return meta

    def health_check(self) -> bool:
        meta = self.discover()
        return meta.status == AgentStatus.READY

    def execute_task(self, task: AgentTask, context: ProblemContext) -> Dict[str, Any]:
        """Execute a non-interactive coding task with agy in the target workspace."""
        meta = self.discover()
        if meta.status != AgentStatus.READY:
            return {
                "status": "error",
                "message": f"Antigravity CLI is not ready (status: {meta.status.value})",
            }

        prompt = (
            f"JARVIS DEBUGGING TASK:\n"
            f"Problem: {context.original_request}\n"
            f"Error: {context.error_message}\n"
            f"Traceback:\n{context.traceback}\n"
            f"Working directory: {context.working_dir}\n"
            f"Please analyze the defect, propose the exact file repair, and verify tests."
        )

        cmd = [
            self.cli_path,
            "-p", prompt,
            "--output-format", "text",
            "--add-dir", context.working_dir,
        ]

        logger.info("Executing Antigravity task in %s...", context.working_dir)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=context.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            self._current_process_pid = proc.pid
            task.process_pid = proc.pid

            stdout, stderr = proc.communicate(timeout=120)
            self._current_process_pid = None

            return {
                "status": "ok" if proc.returncode == 0 else "error",
                "exit_code": proc.returncode,
                "output": stdout,
                "error": stderr,
                "agent_id": self.agent_id,
            }
        except subprocess.TimeoutExpired:
            self.cancel_task()
            return {"status": "error", "message": "Antigravity task timed out after 120s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
