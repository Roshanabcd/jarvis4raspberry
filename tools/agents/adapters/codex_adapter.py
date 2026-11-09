"""
OpenAI Codex CLI Adapter for JARVIS OS.
Integrates with `codex` CLI for non-interactive coding, code inspection, and repairs.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from typing import Any, Dict, Optional

from tools.agents.adapters.base import BaseAgentAdapter
from tools.agents.models import AgentCapabilities, AgentMetadata, AgentStatus, AgentTask, ProblemContext

logger = logging.getLogger("JARVIS.CodexAdapter")


class CodexAdapter(BaseAgentAdapter):
    """Adapter for OpenAI Codex CLI (`codex`)."""

    def __init__(self, cli_path: Optional[str] = None):
        super().__init__(agent_id="codex", display_name="OpenAI Codex")
        self.cli_path = cli_path or shutil.which("codex") or "/home/roshan/.local/bin/codex"
        self._cached_meta: Optional[AgentMetadata] = None

    def discover(self) -> AgentMetadata:
        """Inspect codex executable, version, auth status, and capabilities."""
        installed = os.path.exists(self.cli_path) and os.access(self.cli_path, os.X_OK)
        if not installed:
            return AgentMetadata(
                id=self.agent_id,
                display_name=self.display_name,
                installed=False,
                authenticated=False,
                status=AgentStatus.NOT_INSTALLED,
                error_message="OpenAI Codex CLI ('codex') not found on system.",
            )

        # Detect version
        version = "Unknown"
        try:
            res_v = subprocess.run([self.cli_path, "--version"], capture_output=True, text=True, timeout=5)
            if res_v.returncode == 0:
                version = res_v.stdout.strip()
        except Exception as e:
            logger.warning("Failed to check codex version: %s", e)

        # Detect authentication status safely without revealing secrets
        authenticated = False
        try:
            res_s = subprocess.run([self.cli_path, "login", "status"], capture_output=True, text=True, timeout=5)
            output = (res_s.stdout + res_s.stderr).lower()
            if res_s.returncode == 0 and "logged in" in output:
                authenticated = True
        except Exception as e:
            logger.warning("Failed to check codex login status: %s", e)

        caps = AgentCapabilities(
            supports_noninteractive=True,
            supports_file_editing=True,
            supports_shell=True,
            supports_structured_output=True,
            supports_review=True,
            supports_sandbox=True,
            models=["gpt-4o", "o3-mini", "codex-default"],
        )

        meta = AgentMetadata(
            id=self.agent_id,
            display_name=self.display_name,
            installed=True,
            authenticated=authenticated,
            version=version,
            cli_path=self.cli_path,
            capabilities=caps,
            permission_mode="sandbox_prompt",
            last_health_check=time.time(),
            status=AgentStatus.READY if authenticated else AgentStatus.UNAUTHENTICATED,
        )
        self._cached_meta = meta
        return meta

    def health_check(self) -> bool:
        meta = self.discover()
        return meta.status == AgentStatus.READY

    def execute_task(self, task: AgentTask, context: ProblemContext) -> Dict[str, Any]:
        """Execute a non-interactive task with codex exec."""
        meta = self.discover()
        if meta.status != AgentStatus.READY:
            return {
                "status": "error",
                "message": f"Codex CLI is not ready (status: {meta.status.value})",
            }

        prompt = (
            f"JARVIS DEBUGGING TASK:\n"
            f"Problem: {context.original_request}\n"
            f"Error: {context.error_message}\n"
            f"Traceback:\n{context.traceback}\n"
            f"Please inspect the error in {context.working_dir} and provide the code repair."
        )

        cmd = [self.cli_path, "exec", prompt]
        logger.info("Executing Codex task in %s...", context.working_dir)
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
            return {"status": "error", "message": "Codex task timed out after 120s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
