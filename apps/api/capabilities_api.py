"""
Capabilities REST API for JARVIS OS.
Provides endpoints for catalog discovery, natural language intent routing,
direct capability execution, and multi-task orchestration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ai.capabilities.models import (
    CapabilityCategory,
    CapabilityInvocationRequest,
    CapabilityResult,
    MultiTaskPlan,
)
from ai.capabilities.registry import get_capability_registry
from ai.capabilities.router import get_capability_router
from ai.capabilities.dispatcher import get_capability_dispatcher
from ai.capabilities.multi_task_brain import get_multi_task_brain

logger = logging.getLogger("JARVIS.API.Capabilities")

capabilities_router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


class RouteTestRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    role: str = "USER"
    channel: str = "chat"


class MultiTaskRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    role: str = "USER"
    user_id: str = "default_user"
    session_id: str = "default"
    channel: str = "chat"


@capabilities_router.get("")
def list_capabilities(
    category: Optional[str] = Query(None, description="Optional category filter"),
    is_cli: Optional[bool] = Query(None, description="Filter CLI tools"),
):
    """List all registered autonomous capabilities across apps, modules, tools, and CLIs."""
    reg = get_capability_registry()
    cat_enum = None
    if category:
        try:
            cat_enum = CapabilityCategory(category.lower())
        except ValueError:
            pass

    caps = reg.list_capabilities(category=cat_enum)
    if is_cli is not None:
        caps = [c for c in caps if c.is_cli == is_cli]

    return {
        "status": "ok",
        "total": len(caps),
        "capabilities": [c.model_dump() for c in caps],
    }


@capabilities_router.get("/{capability_id}")
def get_capability_detail(capability_id: str):
    """Retrieve detailed specification and parameter schemas for a capability."""
    reg = get_capability_registry()
    cap = reg.get_capability(capability_id)
    if not cap:
        raise HTTPException(status_code=404, detail=f"Capability '{capability_id}' not found.")
    return {"status": "ok", "capability": cap.model_dump()}


@capabilities_router.post("/route")
def test_capability_routing(req: RouteTestRequest):
    """Classify natural language intent and test parameter extraction."""
    router = get_capability_router()
    match = router.route(req.prompt, user_role=req.role, channel=req.channel)
    if not match:
        return {
            "status": "unmatched",
            "message": "No direct capability matched. Request falls back to LLM reasoning.",
            "prompt": req.prompt,
        }
    return {
        "status": "matched",
        "match": match.model_dump(),
        "prompt": req.prompt,
    }


@capabilities_router.post("/invoke", response_model=CapabilityResult)
def invoke_capability(req: CapabilityInvocationRequest):
    """Execute a specific capability action directly."""
    dispatcher = get_capability_dispatcher()
    return dispatcher.execute(req)


@capabilities_router.post("/multi-task", response_model=MultiTaskPlan)
def execute_multi_task(req: MultiTaskRequest):
    """Decompose and execute a compound multi-task request across capabilities."""
    brain = get_multi_task_brain()
    plan = brain.create_plan(
        text=req.prompt,
        user_role=req.role,
        user_id=req.user_id,
        session_id=req.session_id,
    )
    return brain.execute_plan(
        plan=plan,
        user_id=req.user_id,
        user_role=req.role,
        session_id=req.session_id,
        channel=req.channel,
    )
