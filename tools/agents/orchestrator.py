"""
Multi-AI Agent Orchestrator for JARVIS OS Phase 5.
Selects optimal agents based on capabilities and problem complexity, enforces bounded failover,
manages task concurrency, and coordinates second-opinion reviews.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from tools.agents.models import (
    AgentId,
    AgentMetadata,
    AgentStatus,
    AgentTask,
    ProblemContext,
    TaskPhase,
)
from tools.agents.registry import agent_registry
from tools.agents.stuck_watchdog import stuck_watchdog

logger = logging.getLogger("JARVIS.MultiAgentOrchestrator")


class MultiAgentOrchestrator:
    """Coordinates autonomous AI coding agents, failover sequences, and review pipelines."""

    def __init__(self):
        self._active_tasks: Dict[str, AgentTask] = {}
        self._write_lock = threading.Lock()
        self.max_fallback_attempts: int = 3
        self.local_only_mode: bool = False
        self.preferred_primary_agent: Optional[str] = None

    def select_best_agent(
        self,
        context: ProblemContext,
        exclude_agents: Optional[List[str]] = None
    ) -> Optional[AgentMetadata]:
        """Intelligently score and select the optimal agent for a given failure context."""
        ready_agents = agent_registry.get_ready_agents()
        if not ready_agents:
            logger.warning("No agents are currently READY and authenticated.")
            return None

        excluded = set(exclude_agents or [])
        candidates = [a for a in ready_agents if a.id not in excluded]
        if not candidates:
            return None

        # If user explicitly preferred a primary agent and it's available
        if self.preferred_primary_agent:
            for c in candidates:
                if c.id == self.preferred_primary_agent:
                    return c

        # If local-only mode is active, strictly pick Ollama
        if self.local_only_mode:
            for c in candidates:
                if c.id == AgentId.OLLAMA.value:
                    return c

        # Scoring heuristics:
        # 1. Antigravity or Codex for complex coding / file edits
        # 2. Ollama for quick local reasoning or offline troubleshooting
        is_complex = bool(context.traceback or "AssertionError" in context.error_message or context.file_contents)

        if is_complex:
            # Prefer Antigravity or Codex
            for preferred in [AgentId.ANTIGRAVITY.value, AgentId.CODEX.value, AgentId.OLLAMA.value]:
                for c in candidates:
                    if c.id == preferred:
                        return c

        # Default fallback to top candidate
        return candidates[0]

    def create_task(self, title: str, context: ProblemContext) -> AgentTask:
        """Initialize and register a new autonomous debugging task."""
        task = AgentTask(title=title, problem_context=context)
        self._active_tasks[task.task_id] = task
        return task

    def execute_with_failover(
        self,
        task: AgentTask,
        context: ProblemContext
    ) -> Dict[str, Any]:
        """Run task with bounded failover across suitable agents."""
        attempted_agents: List[str] = []

        while task.attempt_count < self.max_fallback_attempts:
            task.attempt_count += 1
            selected = self.select_best_agent(context, exclude_agents=attempted_agents)

            if not selected:
                task.phase = TaskPhase.FAILED
                task.error_message = "No further suitable or authenticated AI agents available for failover."
                return {
                    "status": "error",
                    "task_id": task.task_id,
                    "phase": task.phase.value,
                    "message": task.error_message,
                    "attempted_agents": attempted_agents,
                }

            agent_id = selected.id
            attempted_agents.append(agent_id)
            task.assigned_agent = agent_id
            task.phase = TaskPhase.DIAGNOSING
            task.updated_at = time.time()
            logger.info("Task %s (attempt %d/%d): Assigned to %s", task.task_id, task.attempt_count, self.max_fallback_attempts, selected.display_name)

            adapter = agent_registry.get_adapter(agent_id)
            if not adapter:
                continue

            # Concurrency governance: only one write agent at a time
            with self._write_lock:
                stuck_watchdog.register_task(task.task_id, agent_id, timeout_seconds=90.0)
                try:
                    res = adapter.execute_task(task, context)
                finally:
                    stuck_watchdog.unregister_task(task.task_id)

            if res.get("status") == "ok":
                task.phase = TaskPhase.PROPOSED_FIX
                task.logs.append(f"[{agent_id}] Success: {res.get('output', '')[:300]}")
                return {
                    "status": "ok",
                    "task_id": task.task_id,
                    "phase": task.phase.value,
                    "agent_id": agent_id,
                    "result": res,
                    "attempted_agents": attempted_agents,
                }
            else:
                task.logs.append(f"[{agent_id}] Failed: {res.get('message', 'Unknown error')}")
                logger.warning("Agent %s failed on task %s: %s. Initiating failover...", agent_id, task.task_id, res.get("message"))

        task.phase = TaskPhase.FAILED
        task.error_message = f"Exceeded maximum failover attempts ({self.max_fallback_attempts})."
        return {
            "status": "error",
            "task_id": task.task_id,
            "phase": task.phase.value,
            "message": task.error_message,
            "attempted_agents": attempted_agents,
        }

    def request_second_opinion_review(
        self,
        task: Optional[AgentTask] = None,
        context: Optional[ProblemContext] = None,
        proposed_patch: str = "",
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Request independent read-only review from a secondary agent."""
        if context is None:
            context = ProblemContext()
        if task is None:
            task = self.create_task("Second Opinion Review", context)

        ready_agents = agent_registry.get_ready_agents()
        reviewer_meta = None
        if agent_id:
            reviewer_meta = agent_registry.get_metadata(agent_id)
        if not reviewer_meta:
            for a in ready_agents:
                if a.id != task.assigned_agent and a.capabilities.supports_review:
                    reviewer_meta = a
                    break

        if not reviewer_meta:
            return {
                "status": "skipped",
                "message": "No independent secondary agent available for review.",
            }

        logger.info("Requesting second opinion review from %s for task %s...", reviewer_meta.display_name, task.task_id)
        adapter = agent_registry.get_adapter(reviewer_meta.id)
        if not adapter:
            return {"status": "skipped", "message": "Reviewer adapter not found."}

        review_context = ProblemContext(
            original_request=f"Code Review for Task {task.task_id}",
            error_message=f"Review this proposed patch for {context.error_message}",
            working_dir=context.working_dir,
            recent_git_diff=proposed_patch,
        )

        res = adapter.execute_task(task, review_context)
        return {
            "status": "ok",
            "reviewer_agent": reviewer_meta.id,
            "reviewer_name": reviewer_meta.display_name,
            "review": res.get("output") or res.get("analysis", "Review complete."),
        }

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._active_tasks.get(task_id)

    def get_active_tasks(self) -> List[AgentTask]:
        return [t for t in self._active_tasks.values() if t.phase.value not in ("completed", "failed")]

    def cancel_task(self, task_id: str, reason: str = "") -> bool:
        task = self._active_tasks.get(task_id)
        if not task:
            return False
        task.phase = TaskPhase.FAILED
        task.error_history.append(f"Cancelled: {reason}")
        if task.assigned_agent:
            adapter = agent_registry.get_adapter(task.assigned_agent)
            if adapter:
                adapter.cancel_task()
        return True

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._active_tasks.values()]


multi_agent_orchestrator = MultiAgentOrchestrator()
