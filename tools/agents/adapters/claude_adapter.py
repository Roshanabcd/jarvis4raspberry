"""
Anthropic Claude Code CLI Adapter for JARVIS OS.
Integrates with `claude` CLI for coding, inspection, and repairs.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Dict, Optional

from tools.agents.adapters.base import BaseAgentAdapter
from tools.agents.models import AgentCapabilities, AgentMetadata, AgentStatus, AgentTask, ProblemContext

logger = logging.getLogger("JARVIS.ClaudeAdapter")


class ClaudeAdapter(BaseAgentAdapter):
    """Adapter for Anthropic Claude Code CLI (`claude`)."""

    def __init__(self, cli_path: Optional[str] = None):
        super().__init__(agent_id="claude", display_name="Anthropic Claude Code")
        self.cli_path = cli_path or shutil.which("claude") or "/home/roshan/.local/bin/claude"
        self._cached_meta: Optional[AgentMetadata] = None

    def discover(self) -> AgentMetadata:
        """Inspect claude executable, version, and auth status."""
        installed = os.path.exists(self.cli_path) and os.access(self.cli_path, os.X_OK)
        if not installed:
            return AgentMetadata(
                id=self.agent_id,
                display_name=self.display_name,
                installed=False,
                authenticated=False,
                status=AgentStatus.NOT_INSTALLED,
                error_message="Claude Code CLI ('claude') not found on system.",
            )

        # Detect version
        version = "Unknown"
        try:
            res_v = subprocess.run([self.cli_path, "--version"], capture_output=True, text=True, timeout=15)
            if res_v.returncode == 0:
                version = res_v.stdout.strip()
        except Exception as e:
            logger.warning("Failed to check claude version: %s", e)

        # Detect authentication status safely
        authenticated = False
        try:
            res_a = subprocess.run([self.cli_path, "auth", "status"], capture_output=True, text=True, timeout=15)
            # Output is JSON: {"loggedIn":false,"authMethod":"none",...}
            if res_a.stdout:
                try:
                    data = json.loads(res_a.stdout)
                    authenticated = bool(data.get("loggedIn", False))
                except Exception:
                    authenticated = "loggedin\":true" in res_a.stdout.lower()
        except Exception as e:
            logger.warning("Failed to check claude auth status: %s", e)

        caps = AgentCapabilities(
            supports_noninteractive=True,
            supports_file_editing=True,
            supports_shell=True,
            supports_structured_output=True,
            supports_review=True,
            supports_sandbox=True,
            models=["claude-3-7-sonnet", "claude-3-5-sonnet"],
        )

        meta = AgentMetadata(
            id=self.agent_id,
            display_name=self.display_name,
            installed=True,
            authenticated=authenticated,
            version=version,
            cli_path=self.cli_path,
            capabilities=caps,
            permission_mode="prompt",
            last_health_check=time.time(),
            status=AgentStatus.READY if authenticated else AgentStatus.UNAUTHENTICATED,
            error_message=None if authenticated else "Claude Code is installed but unauthenticated. Run 'claude' to log in.",
        )
        self._cached_meta = meta
        return meta

    def health_check(self) -> bool:
        meta = self.discover()
        return meta.status == AgentStatus.READY

    def execute_task(self, task: AgentTask, context: ProblemContext) -> Dict[str, Any]:
        """Execute a task with claude -p."""
        meta = self.discover()
        if meta.status != AgentStatus.READY:
            return {
                "status": "error",
                "message": f"Claude Code is not ready (status: {meta.status.value})",
            }

        prompt = (
            f"JARVIS DEBUGGING TASK:\n"
            f"Problem: {context.original_request}\n"
            f"Error: {context.error_message}\n"
            f"Traceback:\n{context.traceback}\n"
            f"Fix the issue in {context.working_dir}."
        )

        cmd = [self.cli_path, "-p", prompt]
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
            return {"status": "error", "message": "Claude task timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
