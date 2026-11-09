"""
OpenCode CLI Adapter for JARVIS OS.
Integrates with `opencode` CLI.
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

logger = logging.getLogger("JARVIS.OpenCodeAdapter")


class OpenCodeAdapter(BaseAgentAdapter):
    """Adapter for OpenCode CLI (`opencode`)."""

    def __init__(self, cli_path: Optional[str] = None):
        super().__init__(agent_id="opencode", display_name="OpenCode")
        self.cli_path = cli_path or shutil.which("opencode") or "/home/roshan/.npm-global/bin/opencode"
        self._cached_meta: Optional[AgentMetadata] = None

    def discover(self) -> AgentMetadata:
        """Inspect opencode executable, version, and auth status."""
        installed = os.path.exists(self.cli_path) and os.access(self.cli_path, os.X_OK)
        if not installed:
            return AgentMetadata(
                id=self.agent_id,
                display_name=self.display_name,
                installed=False,
                authenticated=False,
                status=AgentStatus.NOT_INSTALLED,
                error_message="OpenCode CLI ('opencode') not found on system.",
            )

        # Detect version
        version = "Unknown"
        try:
            res_v = subprocess.run([self.cli_path, "--version"], capture_output=True, text=True, timeout=5)
            if res_v.returncode == 0:
                version = res_v.stdout.strip()
        except Exception as e:
            logger.warning("Failed to check opencode version: %s", e)

        # Detect auth
        authenticated = False
        try:
            res_a = subprocess.run([self.cli_path, "auth", "list"], capture_output=True, text=True, timeout=5)
            if res_a.returncode == 0 and "no authenticated" not in res_a.stdout.lower() and res_a.stdout.strip():
                authenticated = True
        except Exception as e:
            logger.warning("Failed to check opencode auth: %s", e)

        caps = AgentCapabilities(
            supports_noninteractive=True,
            supports_file_editing=True,
            supports_shell=True,
            supports_structured_output=True,
            supports_review=False,
            supports_sandbox=False,
            models=["opencode-default"],
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
            error_message=None if authenticated else "OpenCode is installed but has no authenticated integrations.",
        )
        self._cached_meta = meta
        return meta

    def health_check(self) -> bool:
        meta = self.discover()
        return meta.status == AgentStatus.READY

    def execute_task(self, task: AgentTask, context: ProblemContext) -> Dict[str, Any]:
        meta = self.discover()
        if meta.status != AgentStatus.READY:
            return {
                "status": "error",
                "message": f"OpenCode is not ready (status: {meta.status.value})",
            }
        return {"status": "error", "message": "OpenCode execution not configured"}
