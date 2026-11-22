"""Core Multi-Agent Task Orchestrator Engine for JARVIS Module 18.

Implements:
- Agent registration, capability routing, and per-agent + global concurrency limits
- Task creation with DAG dependency validation & cycle detection
- Priority scheduling (CRITICAL > HIGH > NORMAL > LOW, FIFO tie-breaker)
- Bounded parallel execution of independent tasks
- Persistent SQLite WAL task queue with restart recovery
- Global & per-task pause/resume and task cancellation (with downstream cascade)
- Retry with exponential backoff and strict per-task timeouts
- Human approval checkpoints (pauses task in AWAITING_APPROVAL until decided)
- Inter-agent messaging and workflow-level result aggregation
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from modules.module_18_multi_agent_orchestrator.backend.adapters.contracts import JarvisOrchestratorContract
from modules.module_18_multi_agent_orchestrator.backend.adapters.standalone import StandaloneHarness
from modules.module_18_multi_agent_orchestrator.backend.app.config import OrchestratorConfig
from modules.module_18_multi_agent_orchestrator.backend.models.database import OrchestratorDatabase, utc_now_iso
from modules.module_18_multi_agent_orchestrator.backend.models.schemas import ApprovalStatus, TaskPriority, TaskStatus
from modules.module_18_multi_agent_orchestrator.backend.services.reference_agents import (
    DEFAULT_REFERENCE_AGENTS,
    REFERENCE_HANDLERS,
    AgentHandler,
)


class OrchestratorError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class MultiAgentOrchestrator(JarvisOrchestratorContract):
    """Unified async multi-agent task orchestration engine."""

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        db: Optional[OrchestratorDatabase] = None,
        harness: Optional[StandaloneHarness] = None,
        seed_reference_agents: bool = True,
    ) -> None:
        self.config = config or OrchestratorConfig.from_env()
        self.db = db or OrchestratorDatabase(self.config.db_path)
        self.harness = harness or StandaloneHarness.create(
            self.db,
            {
                "max_concurrency": self.config.max_concurrency,
                "default_timeout_sec": self.config.default_timeout_sec,
                "simulation_mode": self.config.simulation_mode,
            },
        )
        self._handlers: Dict[str, AgentHandler] = dict(REFERENCE_HANDLERS)
        self._started_at = time.monotonic()

        # Restore persisted max_concurrency & paused flag if present
        persisted_mc = self.db.get_setting("max_concurrency")
        self.max_concurrency: int = int(persisted_mc) if persisted_mc else self.config.max_concurrency
        self.paused: bool = self.db.get_setting("engine_paused", "false") == "true"

        self._running = False
        self._scheduler_task: Optional[asyncio.Task[Any]] = None
        self._active_tasks: Dict[str, asyncio.Task[Any]] = {}
        self._agent_active_counts: Dict[str, int] = {}
        self._schedule_event: Optional[asyncio.Event] = None

        # Recover interrupted running tasks on startup
        recovered = self.db.reset_interrupted_running_tasks()
        if recovered > 0:
            self.db.add_log(
                event_type="engine.recovery",
                message=f"Recovered {recovered} interrupted running task(s) back to queued state.",
                level="WARNING",
            )

        if seed_reference_agents and not self.db.list_agents():
            self._seed_default_agents()

    def _seed_default_agents(self) -> None:
        now = utc_now_iso()
        for spec in DEFAULT_REFERENCE_AGENTS:
            record = dict(spec)
            record["status"] = "online"
            record["completed_tasks"] = 0
            record["failed_tasks"] = 0
            record["registered_at"] = now
            record["last_heartbeat"] = now
            self.db.upsert_agent(record)
        self.db.add_log(
            event_type="engine.seeded",
            message=f"Seeded {len(DEFAULT_REFERENCE_AGENTS)} reference agents.",
            level="INFO",
        )

    def register_handler(self, handler_type: str, handler: AgentHandler) -> None:
        """Register a custom async Python handler for an agent handler_type."""
        self._handlers[handler_type] = handler

    # --- Lifecycle ---
    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._schedule_event = asyncio.Event()
        self._schedule_event.set()
        self._scheduler_task = asyncio.create_task(self._scheduler_loop(), name="jarvis-m18-scheduler")
        self.db.add_log(event_type="engine.started", message="Multi-Agent Orchestrator engine started.")

    async def stop(self) -> None:
        self._running = False
        if self._schedule_event:
            self._schedule_event.set()
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
        for task_id, atask in list(self._active_tasks.items()):
            atask.cancel()
            try:
                await atask
            except asyncio.CancelledError:
                pass
        self._active_tasks.clear()
        self._agent_active_counts.clear()
        self.db.add_log(event_type="engine.stopped", message="Multi-Agent Orchestrator engine stopped.")

    def _wake_scheduler(self) -> None:
        if self._schedule_event:
            self._schedule_event.set()

    # --- Engine Controls ---
    async def pause_engine(self) -> Dict[str, Any]:
        self.paused = True
        self.db.set_setting("engine_paused", "true")
        self.db.add_log(event_type="engine.paused", message="Orchestrator scheduling paused by operator.")
        await self.harness.event_bus.publish("engine.paused", {"paused": True})
        return self.get_status()

    async def resume_engine(self) -> Dict[str, Any]:
        self.paused = False
        self.db.set_setting("engine_paused", "false")
        self.db.add_log(event_type="engine.resumed", message="Orchestrator scheduling resumed by operator.")
        await self.harness.event_bus.publish("engine.resumed", {"paused": False})
        self._wake_scheduler()
        return self.get_status()

    async def set_max_concurrency(self, max_concurrency: int) -> Dict[str, Any]:
        if max_concurrency < 1 or max_concurrency > 32:
            raise OrchestratorError("INVALID_LIMIT", "max_concurrency must be between 1 and 32", 422)
        self.max_concurrency = max_concurrency
        self.db.set_setting("max_concurrency", str(max_concurrency))
        self.db.add_log(
            event_type="engine.limits_updated",
            message=f"Updated global max_concurrency to {max_concurrency}.",
            details={"max_concurrency": max_concurrency},
        )
        self._wake_scheduler()
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        tasks = self.db.list_tasks(limit=1000)
        counts: Dict[str, int] = {s.value: 0 for s in TaskStatus}
        for t in tasks:
            counts[t["status"]] = counts.get(t["status"], 0) + 1
        pending_approvals = len(self.db.list_approvals(status="pending"))
        return {
            "engine_state": "paused" if self.paused else ("running" if self._running else "stopped"),
            "paused": self.paused,
            "simulation_mode": self.config.simulation_mode,
            "max_concurrency": self.max_concurrency,
            "active_workers": len(self._active_tasks),
            "agent_count": len(self.db.list_agents()),
            "task_counts": counts,
            "pending_approvals": pending_approvals,
            "total_messages": self.db.count_messages(),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }

    # --- Agent Registry ---
    async def register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        agent_id = agent_data.get("agent_id") or f"agent-{uuid.uuid4().hex[:8]}"
        handler_type = agent_data.get("handler_type", "research")
        if handler_type not in self._handlers:
            raise OrchestratorError(
                "UNKNOWN_HANDLER",
                f"Unknown handler_type '{handler_type}'. Available: {sorted(self._handlers.keys())}",
                422,
            )
        record = {
            "agent_id": agent_id,
            "name": agent_data["name"],
            "role": agent_data["role"],
            "capabilities": list(agent_data.get("capabilities", [])),
            "status": "online",
            "max_concurrency": int(agent_data.get("max_concurrency", 2)),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "handler_type": handler_type,
            "simulated": bool(agent_data.get("simulated", True)),
            "metadata": dict(agent_data.get("metadata", {})),
            "registered_at": now,
            "last_heartbeat": now,
        }
        saved = self.db.upsert_agent(record)
        saved["active_tasks"] = self._agent_active_counts.get(agent_id, 0)
        self.db.add_log(
            event_type="agent.registered",
            agent_id=agent_id,
            message=f"Registered agent '{saved['name']}' ({agent_id}).",
            details={"capabilities": saved["capabilities"], "handler_type": handler_type},
        )
        await self.harness.event_bus.publish("agent.registered", saved)
        self._wake_scheduler()
        return saved

    def list_agents(self) -> List[Dict[str, Any]]:
        agents = self.db.list_agents()
        for a in agents:
            a["active_tasks"] = self._agent_active_counts.get(a["agent_id"], 0)
            if a["status"] == "online" and a["active_tasks"] >= a["max_concurrency"]:
                a["status"] = "busy"
        return agents

    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        updated = self.db.update_agent(agent_id, updates)
        if not updated:
            raise OrchestratorError("AGENT_NOT_FOUND", f"Agent '{agent_id}' not found", 404)
        updated["active_tasks"] = self._agent_active_counts.get(agent_id, 0)
        self.db.add_log(
            event_type="agent.updated",
            agent_id=agent_id,
            message=f"Updated agent '{agent_id}'.",
            details=updates,
        )
        await self.harness.event_bus.publish("agent.updated", updated)
        self._wake_scheduler()
        return updated

    async def remove_agent(self, agent_id: str) -> Dict[str, Any]:
        if self._agent_active_counts.get(agent_id, 0) > 0:
            raise OrchestratorError(
                "AGENT_BUSY",
                f"Cannot remove agent '{agent_id}' while it has active running tasks.",
                409,
            )
        deleted = self.db.delete_agent(agent_id)
        if not deleted:
            raise OrchestratorError("AGENT_NOT_FOUND", f"Agent '{agent_id}' not found", 404)
        self.db.add_log(event_type="agent.removed", agent_id=agent_id, message=f"Removed agent '{agent_id}'.")
        await self.harness.event_bus.publish("agent.removed", {"agent_id": agent_id})
        return {"deleted": True, "agent_id": agent_id}

    # --- DAG Validation ---
    def _validate_dependencies(self, new_task_id: str, depends_on: List[str]) -> List[str]:
        unique_deps = list(dict.fromkeys(depends_on))
        if new_task_id in unique_deps:
            raise OrchestratorError("DAG_CYCLE", "A task cannot depend on itself.", 422)
        for dep_id in unique_deps:
            if not self.db.get_task(dep_id):
                raise OrchestratorError(
                    "DEPENDENCY_NOT_FOUND",
                    f"Dependency task '{dep_id}' does not exist.",
                    422,
                )

        # Build adjacency map (task -> dependencies) and verify acyclicity via DFS
        edges = self.db.get_all_dependency_edges()
        adj: Dict[str, List[str]] = {}
        for edge in edges:
            adj.setdefault(edge["target"], []).append(edge["source"])
        adj[new_task_id] = list(unique_deps)

        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(node: str) -> None:
            if node in visiting:
                raise OrchestratorError("DAG_CYCLE", "Circular dependency detected in task graph.", 422)
            if node in visited:
                return
            visiting.add(node)
            for nxt in adj.get(node, []):
                dfs(nxt)
            visiting.remove(node)
            visited.add(node)

        dfs(new_task_id)
        return unique_deps

    # --- Task Management ---
    async def submit_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = f"tsk_{uuid.uuid4().hex[:10]}"
        depends_on = self._validate_dependencies(task_id, list(task_data.get("depends_on", [])))

        assigned_agent_id = task_data.get("assigned_agent_id")
        if assigned_agent_id and not self.db.get_agent(assigned_agent_id):
            raise OrchestratorError(
                "AGENT_NOT_FOUND",
                f"Assigned agent '{assigned_agent_id}' is not registered.",
                422,
            )

        now = utc_now_iso()
        requires_approval = bool(task_data.get("requires_approval", False))
        initial_status = TaskStatus.PENDING.value if depends_on else TaskStatus.QUEUED.value
        if requires_approval and not depends_on:
            initial_status = TaskStatus.AWAITING_APPROVAL.value

        priority_val = task_data.get("priority", TaskPriority.NORMAL.value)
        if isinstance(priority_val, TaskPriority):
            priority_val = priority_val.value

        record = {
            "task_id": task_id,
            "workflow_id": task_data.get("workflow_id", "default-workflow"),
            "title": task_data["title"],
            "description": task_data.get("description", ""),
            "required_capability": task_data.get("required_capability"),
            "assigned_agent_id": assigned_agent_id,
            "priority": int(priority_val),
            "status": initial_status,
            "payload": dict(task_data.get("payload", {})),
            "result": None,
            "error": None,
            "retries_attempted": 0,
            "max_retries": int(task_data.get("max_retries", 2)),
            "retry_backoff_sec": float(task_data.get("retry_backoff_sec", 0.25)),
            "timeout_sec": float(task_data.get("timeout_sec", self.config.default_timeout_sec)),
            "requires_approval": requires_approval,
            "approval_status": ApprovalStatus.PENDING.value if requires_approval else None,
            "created_at": now,
            "updated_at": now,
        }
        saved = self.db.create_task(record, depends_on)

        if requires_approval:
            prompt = (
                task_data.get("approval_prompt")
                or f"Approve execution of task '{saved['title']}' in workflow '{saved['workflow_id']}'?"
            )
            apr = await self.harness.approvals.request_approval(
                task_id=task_id,
                workflow_id=saved["workflow_id"],
                prompt=prompt,
            )
            await self.harness.event_bus.publish("approval.requested", apr)

        self.db.add_log(
            event_type="task.created",
            task_id=task_id,
            agent_id=assigned_agent_id,
            message=f"Created task '{saved['title']}' ({task_id}) with priority {saved['priority']}.",
            details={"workflow_id": saved["workflow_id"], "depends_on": depends_on, "status": saved["status"]},
        )
        await self.harness.event_bus.publish("task.created", saved)
        self._wake_scheduler()
        return saved

    async def pause_task(self, task_id: str) -> Dict[str, Any]:
        task = self.db.get_task(task_id)
        if not task:
            raise OrchestratorError("TASK_NOT_FOUND", f"Task '{task_id}' not found", 404)
        if task["status"] in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
            raise OrchestratorError("INVALID_STATE", f"Cannot pause terminal task in state '{task['status']}'", 409)
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
        updated = self.db.update_task_fields(task_id, status=TaskStatus.PAUSED.value)
        self.db.add_log(event_type="task.paused", task_id=task_id, message=f"Task '{task_id}' paused.")
        await self.harness.event_bus.publish("task.paused", updated or {})
        return updated  # type: ignore[return-value]

    async def resume_task(self, task_id: str) -> Dict[str, Any]:
        task = self.db.get_task(task_id)
        if not task:
            raise OrchestratorError("TASK_NOT_FOUND", f"Task '{task_id}' not found", 404)
        if task["status"] != TaskStatus.PAUSED.value:
            raise OrchestratorError("INVALID_STATE", f"Task '{task_id}' is not paused (state: {task['status']})", 409)
        next_status = TaskStatus.QUEUED.value
        if task["requires_approval"] and task["approval_status"] != ApprovalStatus.APPROVED.value:
            next_status = TaskStatus.AWAITING_APPROVAL.value
        elif not self._dependencies_satisfied(task):
            next_status = TaskStatus.PENDING.value
        updated = self.db.update_task_fields(task_id, status=next_status)
        self.db.add_log(event_type="task.resumed", task_id=task_id, message=f"Task '{task_id}' resumed -> {next_status}.")
        await self.harness.event_bus.publish("task.resumed", updated or {})
        self._wake_scheduler()
        return updated  # type: ignore[return-value]

    async def cancel_task(self, task_id: str, cascade: bool = True) -> Dict[str, Any]:
        task = self.db.get_task(task_id)
        if not task:
            raise OrchestratorError("TASK_NOT_FOUND", f"Task '{task_id}' not found", 404)
        if task["status"] in (TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value):
            return task

        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()

        updated = self.db.update_task_fields(
            task_id,
            status=TaskStatus.CANCELLED.value,
            error="Cancelled by operator",
            completed_at=utc_now_iso(),
        )
        self.db.add_log(event_type="task.cancelled", task_id=task_id, message=f"Task '{task_id}' cancelled.")
        await self.harness.event_bus.publish("task.cancelled", updated or {})

        if cascade:
            for dep_child_id in self.db.get_dependents(task_id):
                child = self.db.get_task(dep_child_id)
                if child and child["status"] not in (
                    TaskStatus.COMPLETED.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.CANCELLED.value,
                ):
                    await self.cancel_task(dep_child_id, cascade=True)

        return updated  # type: ignore[return-value]

    # --- Approvals ---
    async def decide_approval(
        self, approval_id: str, approved: bool, decided_by: str = "operator", comment: str = ""
    ) -> Dict[str, Any]:
        existing = self.db.get_approval(approval_id)
        if not existing:
            raise OrchestratorError("APPROVAL_NOT_FOUND", f"Approval '{approval_id}' not found", 404)
        if existing["status"] != ApprovalStatus.PENDING.value:
            raise OrchestratorError(
                "APPROVAL_ALREADY_DECIDED",
                f"Approval '{approval_id}' is already '{existing['status']}'",
                409,
            )

        decided = await self.harness.approvals.record_decision(approval_id, approved, decided_by, comment)
        task_id = decided["task_id"]
        task = self.db.get_task(task_id)
        if task:
            if approved:
                next_status = (
                    TaskStatus.QUEUED.value if self._dependencies_satisfied(task) else TaskStatus.PENDING.value
                )
                self.db.update_task_fields(
                    task_id,
                    approval_status=ApprovalStatus.APPROVED.value,
                    status=next_status,
                )
                self.db.add_log(
                    event_type="approval.approved",
                    task_id=task_id,
                    message=f"Approval '{approval_id}' approved by {decided_by}. Task queued.",
                    details={"comment": comment},
                )
            else:
                self.db.update_task_fields(
                    task_id,
                    approval_status=ApprovalStatus.REJECTED.value,
                    status=TaskStatus.CANCELLED.value,
                    error=f"Approval rejected by {decided_by}: {comment or 'no comment'}",
                    completed_at=utc_now_iso(),
                )
                self.db.add_log(
                    event_type="approval.rejected",
                    task_id=task_id,
                    level="WARNING",
                    message=f"Approval '{approval_id}' rejected by {decided_by}. Task cancelled.",
                    details={"comment": comment},
                )
                # Cascade cancellation to downstream dependents
                for child_id in self.db.get_dependents(task_id):
                    await self.cancel_task(child_id, cascade=True)

        await self.harness.event_bus.publish("approval.decided", decided)
        self._wake_scheduler()
        return decided

    # --- Inter-Agent Communication ---
    async def send_message(self, msg_data: Dict[str, Any]) -> Dict[str, Any]:
        msg = {
            "message_id": f"msg_{uuid.uuid4().hex[:10]}",
            "sender_agent_id": msg_data["sender_agent_id"],
            "recipient_agent_id": msg_data.get("recipient_agent_id", "broadcast"),
            "task_id": msg_data.get("task_id"),
            "workflow_id": msg_data.get("workflow_id"),
            "channel": msg_data.get("channel", "coordination"),
            "content": msg_data["content"],
            "metadata": dict(msg_data.get("metadata", {})),
            "created_at": utc_now_iso(),
        }
        saved = self.db.create_message(msg)
        self.db.add_log(
            event_type="message.sent",
            task_id=saved["task_id"],
            agent_id=saved["sender_agent_id"],
            message=f"{saved['sender_agent_id']} -> {saved['recipient_agent_id']} [{saved['channel']}]: {saved['content'][:100]}",
        )
        await self.harness.event_bus.publish("message.sent", saved)
        return saved

    # --- DAG & Result Aggregation ---
    def get_dag(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        tasks = self.db.list_tasks(workflow_id=workflow_id, limit=500)
        edges = self.db.get_all_dependency_edges(workflow_id=workflow_id)
        nodes = [
            {
                "task_id": t["task_id"],
                "title": t["title"],
                "workflow_id": t["workflow_id"],
                "status": t["status"],
                "priority": t["priority"],
                "assigned_agent_id": t["assigned_agent_id"],
                "requires_approval": t["requires_approval"],
                "approval_status": t["approval_status"],
            }
            for t in tasks
        ]
        return {"workflow_id": workflow_id or "all", "nodes": nodes, "edges": edges}

    async def get_workflow_aggregation(self, workflow_id: str) -> Dict[str, Any]:
        tasks = self.db.list_tasks(workflow_id=workflow_id, limit=500)
        if not tasks:
            raise OrchestratorError("WORKFLOW_NOT_FOUND", f"No tasks found for workflow '{workflow_id}'", 404)

        by_status: Dict[str, int] = {}
        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}
        for t in tasks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
            if t["result"] is not None:
                results[t["task_id"]] = {"title": t["title"], "agent_id": t["assigned_agent_id"], "result": t["result"]}
            if t["error"]:
                errors[t["task_id"]] = t["error"]

        total = len(tasks)
        completed = by_status.get(TaskStatus.COMPLETED.value, 0)
        failed = by_status.get(TaskStatus.FAILED.value, 0)
        cancelled = by_status.get(TaskStatus.CANCELLED.value, 0)
        if completed == total:
            wf_status = "completed"
        elif failed > 0:
            wf_status = "failed"
        elif cancelled == total:
            wf_status = "cancelled"
        elif by_status.get(TaskStatus.AWAITING_APPROVAL.value, 0) > 0:
            wf_status = "awaiting_approval"
        else:
            wf_status = "in_progress"

        return {
            "workflow_id": workflow_id,
            "status": wf_status,
            "total_tasks": total,
            "progress_percent": round((completed / total) * 100, 1) if total else 0.0,
            "status_breakdown": by_status,
            "aggregated_results": results,
            "errors": errors,
            "messages": self.db.list_messages(workflow_id=workflow_id, limit=50),
        }

    # --- Scheduling & Execution Internals ---
    def _dependencies_satisfied(self, task: Dict[str, Any]) -> bool:
        for dep_id in task.get("depends_on", []):
            dep = self.db.get_task(dep_id)
            if not dep or dep["status"] != TaskStatus.COMPLETED.value:
                return False
        return True

    def _has_failed_dependency(self, task: Dict[str, Any]) -> Optional[str]:
        for dep_id in task.get("depends_on", []):
            dep = self.db.get_task(dep_id)
            if dep and dep["status"] in (TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
                return dep_id
        return None

    def _select_agent(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        agents = self.db.list_agents()
        assigned_id = task.get("assigned_agent_id")
        if assigned_id:
            for a in agents:
                if a["agent_id"] == assigned_id:
                    if a["status"] != "online":
                        return None
                    if self._agent_active_counts.get(assigned_id, 0) >= a["max_concurrency"]:
                        return None
                    return a
            return None

        req_cap = task.get("required_capability")
        candidates: List[Dict[str, Any]] = []
        for a in agents:
            if a["status"] != "online":
                continue
            active = self._agent_active_counts.get(a["agent_id"], 0)
            if active >= a["max_concurrency"]:
                continue
            if req_cap and req_cap not in a["capabilities"] and a["handler_type"] != req_cap:
                continue
            candidates.append(a)

        if not candidates:
            return None
        # Least-loaded agent first
        candidates.sort(key=lambda a: (self._agent_active_counts.get(a["agent_id"], 0), a["completed_tasks"]))
        return candidates[0]

    async def _promote_ready_pending_tasks(self) -> None:
        pending_tasks = self.db.list_tasks(status=TaskStatus.PENDING.value, limit=200)
        for task in pending_tasks:
            failed_dep = self._has_failed_dependency(task)
            if failed_dep:
                self.db.update_task_fields(
                    task["task_id"],
                    status=TaskStatus.CANCELLED.value,
                    error=f"Cancelled because upstream dependency '{failed_dep}' failed or was cancelled.",
                    completed_at=utc_now_iso(),
                )
                self.db.add_log(
                    event_type="task.cancelled",
                    task_id=task["task_id"],
                    level="WARNING",
                    message=f"Task '{task['task_id']}' auto-cancelled due to upstream failure '{failed_dep}'.",
                )
                continue

            if self._dependencies_satisfied(task):
                if task["requires_approval"] and task["approval_status"] != ApprovalStatus.APPROVED.value:
                    self.db.update_task_fields(task["task_id"], status=TaskStatus.AWAITING_APPROVAL.value)
                    await self.harness.event_bus.publish("task.awaiting_approval", {"task_id": task["task_id"]})
                else:
                    self.db.update_task_fields(task["task_id"], status=TaskStatus.QUEUED.value)
                    await self.harness.event_bus.publish("task.queued", {"task_id": task["task_id"]})

    async def _scheduler_loop(self) -> None:
        while self._running:
            try:
                if not self.paused:
                    await self._promote_ready_pending_tasks()
                    await self._dispatch_queued_tasks()
            except Exception as exc:
                self.db.add_log(
                    event_type="scheduler.error",
                    level="ERROR",
                    message=f"Scheduler iteration error: {exc}",
                )

            if self._schedule_event:
                self._schedule_event.clear()
                try:
                    await asyncio.wait_for(self._schedule_event.wait(), timeout=self.config.poll_interval_sec)
                except asyncio.TimeoutError:
                    pass
            else:
                await asyncio.sleep(self.config.poll_interval_sec)

    async def _dispatch_queued_tasks(self) -> None:
        if len(self._active_tasks) >= self.max_concurrency:
            return

        # Tasks already ordered by priority DESC, created_at ASC
        queued = self.db.list_tasks(status=TaskStatus.QUEUED.value, limit=100)
        for task in queued:
            if len(self._active_tasks) >= self.max_concurrency:
                break
            task_id = task["task_id"]
            if task_id in self._active_tasks:
                continue
            if task["requires_approval"] and task["approval_status"] != ApprovalStatus.APPROVED.value:
                self.db.update_task_fields(task_id, status=TaskStatus.AWAITING_APPROVAL.value)
                continue

            agent = self._select_agent(task)
            if not agent:
                continue

            agent_id = agent["agent_id"]
            self._agent_active_counts[agent_id] = self._agent_active_counts.get(agent_id, 0) + 1
            self.db.update_task_fields(
                task_id,
                assigned_agent_id=agent_id,
                status=TaskStatus.RUNNING.value,
                started_at=utc_now_iso(),
            )
            worker = asyncio.create_task(
                self._execute_task(task_id, agent),
                name=f"jarvis-m18-task-{task_id}",
            )
            self._active_tasks[task_id] = worker

    async def _execute_task(self, task_id: str, agent: Dict[str, Any]) -> None:
        agent_id = agent["agent_id"]
        handler = self._handlers.get(agent["handler_type"])
        try:
            task = self.db.get_task(task_id)
            if not task:
                return
            if not handler:
                raise RuntimeError(f"No handler registered for '{agent['handler_type']}'")

            # Gather upstream dependency results
            dep_results: Dict[str, Any] = {}
            for dep_id in task.get("depends_on", []):
                dep = self.db.get_task(dep_id)
                if dep and dep.get("result") is not None:
                    dep_results[dep_id] = dep["result"]

            self.db.add_log(
                event_type="task.started",
                task_id=task_id,
                agent_id=agent_id,
                message=f"Agent '{agent['name']}' started task '{task['title']}'.",
            )
            await self.harness.event_bus.publish(
                "task.started",
                {"task_id": task_id, "agent_id": agent_id, "workflow_id": task["workflow_id"]},
            )

            max_retries = int(task.get("max_retries", 2))
            backoff = float(task.get("retry_backoff_sec", 0.25))
            timeout_sec = float(task.get("timeout_sec", self.config.default_timeout_sec))

            attempt = 0
            while True:
                attempt += 1
                try:
                    result = await asyncio.wait_for(
                        handler(
                            task,
                            {
                                "agent": agent,
                                "attempt": attempt,
                                "dependency_results": dep_results,
                                "orchestrator": self,
                            },
                        ),
                        timeout=timeout_sec,
                    )
                    self.db.update_task_fields(
                        task_id,
                        status=TaskStatus.COMPLETED.value,
                        result=result,
                        error=None,
                        retries_attempted=attempt - 1,
                        completed_at=utc_now_iso(),
                    )
                    self.db.increment_agent_counter(agent_id, "completed_tasks")
                    self.db.add_log(
                        event_type="task.completed",
                        task_id=task_id,
                        agent_id=agent_id,
                        message=f"Task '{task['title']}' completed on attempt {attempt}.",
                    )
                    await self.send_message(
                        {
                            "sender_agent_id": agent_id,
                            "recipient_agent_id": "broadcast",
                            "task_id": task_id,
                            "workflow_id": task["workflow_id"],
                            "channel": "task_results",
                            "content": f"Completed '{task['title']}' on attempt {attempt}.",
                            "metadata": {"status": "completed"},
                        }
                    )
                    await self.harness.event_bus.publish(
                        "task.completed",
                        {"task_id": task_id, "agent_id": agent_id, "workflow_id": task["workflow_id"], "result": result},
                    )
                    return

                except asyncio.CancelledError:
                    raise
                except (asyncio.TimeoutError, Exception) as exc:
                    err_msg = f"Timeout after {timeout_sec}s" if isinstance(exc, asyncio.TimeoutError) else str(exc)
                    if attempt <= max_retries:
                        wait_s = backoff * (2 ** (attempt - 1))
                        self.db.update_task_fields(
                            task_id,
                            status=TaskStatus.RETRYING.value,
                            retries_attempted=attempt,
                            error=err_msg,
                        )
                        self.db.add_log(
                            event_type="task.retrying",
                            task_id=task_id,
                            agent_id=agent_id,
                            level="WARNING",
                            message=f"Attempt {attempt} failed ({err_msg}); retrying in {wait_s:.2f}s.",
                        )
                        await self.harness.event_bus.publish(
                            "task.retrying",
                            {"task_id": task_id, "attempt": attempt, "error": err_msg, "backoff_sec": wait_s},
                        )
                        await asyncio.sleep(wait_s)
                        self.db.update_task_fields(task_id, status=TaskStatus.RUNNING.value)
                    else:
                        self.db.update_task_fields(
                            task_id,
                            status=TaskStatus.FAILED.value,
                            retries_attempted=attempt - 1,
                            error=err_msg,
                            completed_at=utc_now_iso(),
                        )
                        self.db.increment_agent_counter(agent_id, "failed_tasks")
                        self.db.add_log(
                            event_type="task.failed",
                            task_id=task_id,
                            agent_id=agent_id,
                            level="ERROR",
                            message=f"Task '{task['title']}' failed permanently after {attempt} attempt(s): {err_msg}",
                        )
                        await self.harness.event_bus.publish(
                            "task.failed",
                            {"task_id": task_id, "agent_id": agent_id, "error": err_msg},
                        )
                        return

        except asyncio.CancelledError:
            # Pause or Cancel already updated status; do not overwrite
            pass
        finally:
            self._active_tasks.pop(task_id, None)
            current = self._agent_active_counts.get(agent_id, 1) - 1
            if current <= 0:
                self._agent_active_counts.pop(agent_id, None)
            else:
                self._agent_active_counts[agent_id] = current
            self._wake_scheduler()
