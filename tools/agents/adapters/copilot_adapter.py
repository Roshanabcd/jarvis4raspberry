"""
GitHub Copilot CLI Adapter for JARVIS OS.
Integrates with `copilot` CLI for non-interactive scripting, code inspection, and repairs.
Uses granular tool sandboxing and non-secret authentication verification.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.agents.adapters.base import BaseAgentAdapter
from tools.agents.models import AgentCapabilities, AgentMetadata, AgentStatus, AgentTask, ProblemContext

logger = logging.getLogger("JARVIS.CopilotAdapter")


class CopilotAdapter(BaseAgentAdapter):
    """Adapter for GitHub Copilot CLI (`copilot`)."""

    def __init__(self, cli_path: Optional[str] = None):
        super().__init__(agent_id="copilot", display_name="GitHub Copilot")
        self.cli_path = cli_path or shutil.which("copilot") or "/home/roshan/.local/bin/copilot"
        self._cached_meta: Optional[AgentMetadata] = None

    def discover(self) -> AgentMetadata:
        """Inspect copilot executable, version, auth status, and capabilities."""
        installed = os.path.exists(self.cli_path) and os.access(self.cli_path, os.X_OK)
        if not installed:
            return AgentMetadata(
                id=self.agent_id,
                display_name=self.display_name,
                installed=False,
                authenticated=False,
                status=AgentStatus.NOT_INSTALLED,
                error_message="GitHub Copilot CLI ('copilot') not found on system.",
            )

        # Detect version safely
        version = "Unknown"
        try:
            res_v = subprocess.run([self.cli_path, "--version"], capture_output=True, text=True, timeout=5)
            if res_v.returncode == 0:
                match = re.search(r"(\d+\.\d+\.\d+)", res_v.stdout)
                version = match.group(1) if match else res_v.stdout.strip().splitlines()[0]
        except Exception as e:
            logger.warning("Failed to check copilot version: %s", e)

        # Detect authentication safely without leaking tokens or keys
        authenticated = False
        try:
            gh_hosts = Path.home() / ".config" / "gh" / "hosts.yml"
            copilot_cfg = Path.home() / ".config" / "github-copilot"
            copilot_home = Path.home() / ".copilot"
            if gh_hosts.exists() or copilot_cfg.exists() or copilot_home.exists():
                authenticated = True
        except Exception as e:
            logger.warning("Failed to check copilot auth indicators: %s", e)

        caps = AgentCapabilities(
            supports_noninteractive=True,
            supports_file_editing=True,
            supports_shell=True,
            supports_structured_output=True,
            supports_review=True,
            supports_sandbox=True,
            models=["GPT-5.6 Luna", "Claude 3.7 Sonnet"],
        )

        meta = AgentMetadata(
            id=self.agent_id,
            display_name=self.display_name,
            installed=True,
            authenticated=authenticated,
            version=version,
            cli_path=self.cli_path,
            capabilities=caps,
            permission_mode="granular_sandbox",
            last_health_check=time.time(),
            status=AgentStatus.READY if authenticated else AgentStatus.UNAUTHENTICATED,
        )
        self._cached_meta = meta
        return meta

    def health_check(self) -> bool:
        meta = self.discover()
        return meta.status == AgentStatus.READY

    def execute_task(self, task: AgentTask, context: ProblemContext) -> Dict[str, Any]:
        """Execute a non-interactive task with copilot -p."""
        meta = self.discover()
        if meta.status != AgentStatus.READY:
            return {
                "status": "error",
                "message": f"Copilot CLI is not ready (status: {meta.status.value})",
            }

        prompt = (
            f"JARVIS DEBUGGING TASK:\n"
            f"Problem: {context.original_request}\n"
            f"Error: {context.error_message}\n"
            f"Traceback:\n{context.traceback}\n"
            f"Please inspect the error in {context.working_dir} and provide the code repair."
        )

        cmd = [
            self.cli_path,
            "-p", prompt,
            "--silent",
            "--allow-tool=write",
            "--allow-tool=shell(git:*)",
        ]
        if context.working_dir and Path(context.working_dir).exists():
            cmd.append(f"--add-dir={context.working_dir}")

        logger.info("Executing Copilot task in %s...", context.working_dir)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=context.working_dir or str(Path.cwd()),
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
            return {"status": "error", "message": "Copilot task timed out after 120s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
