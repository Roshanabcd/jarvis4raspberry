"""
Base Agent Adapter Abstract Class for JARVIS OS.
Defines the uniform interface for all AI coding agent integrations.
"""
from __future__ import annotations

import abc
import logging
from typing import Any, Dict, Optional

from tools.agents.models import AgentMetadata, AgentTask, ProblemContext

logger = logging.getLogger("JARVIS.AgentAdapter")


class BaseAgentAdapter(abc.ABC):
    """Abstract interface for an AI coding agent adapter."""

    def __init__(self, agent_id: str, display_name: str):
        self.agent_id = agent_id
        self.display_name = display_name
        self._current_process_pid: Optional[int] = None

    @abc.abstractmethod
    def discover(self) -> AgentMetadata:
        """Inspect system environment, executables, version, auth status, and capabilities."""
        pass

    @abc.abstractmethod
    def health_check(self) -> bool:
        """Fast check to verify readiness."""
        pass

    @abc.abstractmethod
    def execute_task(self, task: AgentTask, context: ProblemContext) -> Dict[str, Any]:
        """Execute a problem diagnosis or code repair task."""
        pass

    def cancel_task(self) -> bool:
        """Safely terminate any active child process."""
        if self._current_process_pid:
            try:
                import os
                import signal
                os.kill(self._current_process_pid, signal.SIGTERM)
                logger.info("Terminated agent process %d", self._current_process_pid)
                self._current_process_pid = None
                return True
            except Exception as e:
                logger.warning("Failed to terminate process %d: %s", self._current_process_pid, e)
        return False
