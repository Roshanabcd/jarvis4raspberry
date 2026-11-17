"""
FastAPI Router for JARVIS Autonomous AI Research Assistant.
Mounted under /api/research/*.
Provides REST endpoints for research task lifecycle, plan approval, sources,
evidence, contradictions, reports, exports, and user settings.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from apps.apps_center.permissions import AppRequestIdentity, UserRole, apps_permissions
from apps.research.agent import get_research_agent
from apps.research.database import get_research_db
from apps.research.models import (
    ReportFormat,
    ResearchMode,
    ResearchStatus,
)
from apps.research.reports import ReportBuilder

logger = logging.getLogger("JARVIS-RESEARCH-API")

research_router = APIRouter(prefix="/research", tags=["research"])

_agent = get_research_agent()
_db = get_research_db()


def get_current_user_identity() -> AppRequestIdentity:
    """Resolve requesting user identity and role."""
    try:
        return apps_permissions.get_current_identity()
    except Exception:
        return AppRequestIdentity(user_id="default_user", display_name="User", role=UserRole.USER)


def is_guest(identity: AppRequestIdentity) -> bool:
    role_val = identity.role.value if hasattr(identity.role, "value") else str(identity.role).upper()
    return role_val == "GUEST"


# ── Request / Response Schemas ──────────────────────────────────────────────


class CreateTaskRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Core topic or research subject")
    question: Optional[str] = Field(None, max_length=1000, description="Specific research question or hypothesis")
    mode: Optional[str] = Field("standard", description="Research mode (e.g. standard, deep, academic, comparative)")
    depth: Optional[str] = Field("balanced", description="Depth tier: quick, balanced, deep")
    scope: Optional[str] = Field("broad", description="Scope: broad, narrow, exhaustive")
    max_sources: Optional[int] = Field(8, ge=2, le=30, description="Maximum sources to analyze")
    date_range: Optional[str] = Field("all", description="Temporal date constraint: all, past_year, past_5_years")
    preferred_sources: Optional[List[str]] = Field(None, description="Preferred providers: web, arxiv, crossref, openalex, europepmc")
    output_language: Optional[str] = Field("en", description="Report language")
    auto_approve: Optional[bool] = Field(False, description="Whether to auto-approve plan and execute continuously")
    auto_start: Optional[bool] = Field(True, description="Whether to start task immediately")


class ApprovePlanRequest(BaseModel):
    user_edits: Optional[Dict[str, Any]] = Field(None, description="Optional manual adjustments to supporting questions or limits")


class UpdateSettingsRequest(BaseModel):
    default_mode: Optional[str] = Field("standard")
    default_max_sources: Optional[int] = Field(8, ge=2, le=30)
    auto_approve_plan: Optional[bool] = Field(False)
    preferred_providers: Optional[List[str]] = Field(None)


# ── Endpoints ───────────────────────────────────────────────────────────────


@research_router.get("/health")
def get_health() -> Dict[str, Any]:
    """Health check for AI Research Assistant service."""
    return {
        "status": "healthy",
        "service": "ai-research-assistant",
        "timestamp": time.time(),
        "database": "sqlite_wal",
        "providers_available": ["duckduckgo", "arxiv", "crossref", "openalex", "europepmc"],
    }


@research_router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_research_task(
    req: CreateTaskRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Initialize a new autonomous research task."""
    if is_guest(identity):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest accounts do not have permission to execute autonomous research",
        )

    task = _agent.create_task(
        user_id=identity.user_id,
        topic=req.topic,
        question=req.question or req.topic,
        mode=req.mode or "standard",
        depth=req.depth or "balanced",
        scope=req.scope or "broad",
        max_sources=req.max_sources or 8,
        date_range=req.date_range or "all",
        preferred_sources=req.preferred_sources,
        output_language=req.output_language or "en",
        auto_start=req.auto_start if req.auto_start is not None else True,
        auto_approve=req.auto_approve or False,
    )

    return {
        "success": True,
        "task": task.to_dict(),
        "message": "Research task created and initialized",
    }


@research_router.get("/tasks")
def list_tasks(
    limit: int = Query(50, ge=1, le=100),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """List research tasks for the active user."""
    tasks = _db.list_tasks(identity.user_id, limit=limit)
    return {"success": True, "tasks": tasks, "count": len(tasks)}


@research_router.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Get status, progress, and execution details for a research task."""
    task = _db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research task not found")

    return {"success": True, "task": task.to_dict()}


@research_router.get("/tasks/{task_id}/plan")
def get_task_plan(
    task_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Retrieve the generated ResearchPlan for a task."""
    task = _db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research task not found")
    if not task.plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan has not been generated yet")

    return {"success": True, "plan": task.plan.to_dict()}


@research_router.post("/tasks/{task_id}/approve")
def approve_task_plan(
    task_id: str,
    req: ApprovePlanRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Approve research plan and resume execution."""
    if is_guest(identity):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Guests cannot approve research tasks")

    task = _agent.approve_plan(task_id, user_edits=req.user_edits)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research task or plan not found")

    return {"success": True, "task": task.to_dict(), "message": "Plan approved; search phase initiated"}


@research_router.get("/tasks/{task_id}/sources")
def get_task_sources(
    task_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """List all retrieved and extracted sources for a task."""
    sources = _db.get_sources_for_task(task_id)
    return {"success": True, "sources": [s.to_dict() for s in sources], "count": len(sources)}


@research_router.get("/tasks/{task_id}/evidence")
def get_task_evidence(
    task_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """List extracted evidence records linked to source passages."""
    records = _db.get_evidence_for_task(task_id)
    return {"success": True, "evidence": [r.to_dict() for r in records], "count": len(records)}


@research_router.get("/tasks/{task_id}/contradictions")
def get_task_contradictions(
    task_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """List detected contradictions and conflicting claims across sources."""
    contradictions = _db.get_contradictions_for_task(task_id)
    return {"success": True, "contradictions": [c.to_dict() for c in contradictions], "count": len(contradictions)}


@research_router.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Cancel a running research task."""
    ok = _agent.cancel_task(task_id)
    return {"success": ok, "message": "Research task cancellation requested"}


@research_router.get("/reports")
def list_reports(
    limit: int = Query(50, ge=1, le=100),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """List completed research reports for the current user."""
    reports = _db.list_reports(identity.user_id, limit=limit)
    return {"success": True, "reports": reports, "count": len(reports)}


@research_router.get("/reports/{report_id}")
def get_report(
    report_id: str,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Retrieve full research report including Markdown and HTML bodies."""
    report = _db.get_report(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research report not found")

    return {"success": True, "report": report.to_dict()}


@research_router.get("/reports/{report_id}/export")
def export_report(
    report_id: str,
    format: str = Query("markdown", pattern="^(markdown|html|json)$"),
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Response:
    """Export research report as Markdown, standalone HTML, or complete JSON archive."""
    report = _db.get_report(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research report not found")

    if format == "html":
        return Response(content=report.html_content, media_type="text/html")
    elif format == "json":
        task = _db.get_task(report.task_id)
        if task and task.plan:
            archive = ReportBuilder.build_json_archive(
                task=task,
                plan=task.plan,
                sources=task.sources,
                evidence=task.evidence,
                contradictions=task.contradictions,
                report=report,
            )
        else:
            archive = report.to_dict()
        import json
        return Response(content=json.dumps(archive, indent=2), media_type="application/json")
    else:
        # Default to markdown
        return Response(content=report.markdown_content, media_type="text/markdown")


@research_router.get("/settings")
def get_settings(
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Get research configuration preferences for the active user."""
    settings = _db.get_settings(identity.user_id)
    return {"success": True, "settings": settings}


@research_router.post("/settings")
def update_settings(
    req: UpdateSettingsRequest,
    identity: AppRequestIdentity = Depends(get_current_user_identity),
) -> Dict[str, Any]:
    """Update research configuration preferences."""
    current = _db.get_settings(identity.user_id)
    if req.default_mode is not None:
        current["default_mode"] = req.default_mode
    if req.default_max_sources is not None:
        current["default_max_sources"] = req.default_max_sources
    if req.auto_approve_plan is not None:
        current["auto_approve_plan"] = req.auto_approve_plan
    if req.preferred_providers is not None:
        current["preferred_providers"] = req.preferred_providers

    _db.save_settings(identity.user_id, current)
    return {"success": True, "settings": current, "message": "Settings updated"}
