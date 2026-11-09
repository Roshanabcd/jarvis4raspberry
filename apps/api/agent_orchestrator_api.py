"""
Agent Orchestration, Permission, and Self-Healing REST API for JARVIS OS Phase 5.
Exposes endpoints for agent discovery, task execution, permission governance,
and autonomous debugging.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tools.agents.models import PermissionProfile
from tools.agents.orchestrator import multi_agent_orchestrator
from tools.agents.permission_manager import permission_manager
from tools.agents.registry import agent_registry
from tools.agents.self_healing import self_healing_engine

logger = logging.getLogger("JARVIS.AgentAPI")

agents_router = APIRouter()


# ─── Request Models ──────────────────────────────────────────
class ExecuteAgentRequest(BaseModel):
    prompt: str
    working_dir: Optional[str] = None


class DebugRequest(BaseModel):
    problem: str
    error_message: str
    traceback: Optional[str] = ""
    target_file: Optional[str] = None
    working_dir: Optional[str] = None


class RepairRequest(BaseModel):
    problem: str
    error_message: str
    traceback: Optional[str] = ""
    target_file: Optional[str] = None
    working_dir: Optional[str] = None
    test_command: Optional[str] = None
    reproduction_cmd: Optional[str] = None
    enable_review: Optional[bool] = False


class ReviewRequest(BaseModel):
    task_id: str
    patch_diff: str


class PermissionDecisionRequest(BaseModel):
    request_id: str
    create_similar_rule: Optional[bool] = False
    reason: Optional[str] = None


class ProfileSwitchRequest(BaseModel):
    profile: str  # SAFE_AUTO, SUPERVISED_AUTO, MANUAL


# ─── Discovery & Status Endpoints ────────────────────────────
@agents_router.get("/agents")
def list_agents() -> List[Dict[str, Any]]:
    """List all registered AI coding agents and their live discovery metadata."""
    meta = agent_registry.discover_all()
    return [m.to_dict() for m in meta]


@agents_router.get("/agents/discover")
def trigger_agent_discovery() -> Dict[str, Any]:
    """Force fresh discovery of all installed agents and their live capabilities."""
    meta = agent_registry.discover_all(force_refresh=True)
    ready = [m.id for m in meta if m.status.value == "READY"]
    return {
        "status": "ok",
        "total_agents": len(meta),
        "ready_agents": ready,
        "agents": [m.to_dict() for m in meta],
    }


@agents_router.get("/agents/status")
def get_orchestrator_status() -> Dict[str, Any]:
    """Return overall orchestrator health, active tasks count, and permission profile."""
    ready_agents = agent_registry.get_ready_agents()
    return {
        "status": "ok",
        "ready_agent_count": len(ready_agents),
        "ready_agents": [a.id for a in ready_agents],
        "active_permission_profile": permission_manager.current_profile.value,
        "active_tasks_count": len(multi_agent_orchestrator._active_tasks),
        "local_only_mode": multi_agent_orchestrator.local_only_mode,
    }


@agents_router.post("/agents/{agent_id}/health")
def check_agent_health(agent_id: str) -> Dict[str, Any]:
    """Check health and readiness for a specific agent."""
    adapter = agent_registry.get_adapter(agent_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    meta = adapter.discover()
    return {"status": "ok", "agent": meta.to_dict(), "healthy": meta.status.value == "READY"}


@agents_router.post("/agents/{agent_id}/cancel")
def cancel_agent(agent_id: str) -> Dict[str, Any]:
    """Terminate running operations for a specific agent."""
    adapter = agent_registry.get_adapter(agent_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    ok = adapter.cancel_task()
    return {"status": "ok", "agent_id": agent_id, "cancelled": ok}


# ─── Tasks & Debugging Endpoints ──────────────────────────────
@agents_router.get("/agents/tasks")
def list_tasks() -> List[Dict[str, Any]]:
    """List all active and recent agent debugging tasks."""
    return multi_agent_orchestrator.list_tasks()


@agents_router.get("/agents/tasks/{task_id}")
def get_task_detail(task_id: str) -> Dict[str, Any]:
    """Retrieve full details, phase, and logs for a specific task."""
    task = multi_agent_orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task.to_dict()


@agents_router.post("/agents/debug")
def debug_problem(req: DebugRequest) -> Dict[str, Any]:
    """Perform problem analysis with local Ollama or ready coding agent."""
    from tools.agents.context_packager import context_packager
    from tools.agents.adapters.ollama_adapter import OllamaAdapter

    ctx = context_packager.package_failure(
        original_request=req.problem,
        error_message=req.error_message,
        traceback=req.traceback or "",
        working_dir=req.working_dir or "/home/roshan/.gemini/antigravity/scratch/jarvis-os",
        target_files=[req.target_file] if req.target_file else None,
    )

    ollama = OllamaAdapter()
    return ollama.analyze_problem(ctx)


@agents_router.post("/agents/repair")
def execute_self_healing_repair(req: RepairRequest) -> Dict[str, Any]:
    """Execute autonomous self-healing repair pipeline."""
    res = self_healing_engine.diagnose_and_repair(
        original_request=req.problem,
        error_message=req.error_message,
        traceback=req.traceback or "",
        target_file=req.target_file,
        working_dir=req.working_dir,
        test_command=req.test_command,
        reproduction_cmd=req.reproduction_cmd,
        enable_review=req.enable_review or False,
    )
    return res


# ─── Permission Management Endpoints ──────────────────────────
@agents_router.get("/agents/permissions")
def get_permissions() -> Dict[str, Any]:
    """Retrieve current permission profile and all pending approval requests."""
    return {
        "profile": permission_manager.current_profile.value,
        "approved_workspaces": permission_manager.approved_workspaces,
        "project_scoped_rules": permission_manager.project_scoped_rules,
        "pending_requests": permission_manager.get_pending_requests(),
    }


@agents_router.post("/agents/permissions/profile")
def set_permission_profile(req: ProfileSwitchRequest) -> Dict[str, Any]:
    """Switch active permission profile (SAFE_AUTO, SUPERVISED_AUTO, MANUAL)."""
    try:
        prof = PermissionProfile(req.profile.upper().strip())
        return permission_manager.set_profile(prof)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid profile '{req.profile}'. Valid: SAFE_AUTO, SUPERVISED_AUTO, MANUAL")


@agents_router.post("/agents/permissions/approve")
def approve_permission(req: PermissionDecisionRequest) -> Dict[str, Any]:
    """Approve a pending permission request."""
    res = permission_manager.approve_request(
        request_id=req.request_id,
        create_similar_rule=req.create_similar_rule or False,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res


@agents_router.post("/agents/permissions/deny")
def deny_permission(req: PermissionDecisionRequest) -> Dict[str, Any]:
    """Deny a pending permission request."""
    res = permission_manager.deny_request(
        request_id=req.request_id,
        reason=req.reason or "Denied by user",
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res


@agents_router.get("/agents/permissions/history")
def get_permission_history(limit: int = Query(50, description="Max records")) -> List[Dict[str, Any]]:
    """Retrieve recent permission decisions from the audit log."""
    return permission_manager.get_audit_history(limit=limit)


# ─── Metrics Endpoint ─────────────────────────────────────────
@agents_router.get("/agents/metrics")
def get_agent_metrics() -> Dict[str, Any]:
    """Return real metrics on agent tasks, success rate, and memory usage."""
    tasks = multi_agent_orchestrator.list_tasks()
    total = len(tasks)
    verified = sum(1 for t in tasks if t.get("phase") == "RUNTIME_VERIFIED")
    failed = sum(1 for t in tasks if t.get("phase") == "FAILED")

    return {
        "total_tasks": total,
        "verified_repairs": verified,
        "failed_tasks": failed,
        "success_rate_pct": (verified / total * 100) if total > 0 else 100.0,
        "active_profile": permission_manager.current_profile.value,
        "audit_records_count": len(permission_manager.get_audit_history(limit=500)),
    }


@agents_router.post("/agents/rollback")
def rollback_checkpoint() -> Dict[str, Any]:
    """Roll back the most recent safety snapshot."""
    from tools.agents.git_safety import git_safety
    ok, msg = git_safety.rollback_latest()
    return {"status": "ok" if ok else "error", "restored": ok, "message": msg}
