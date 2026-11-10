"""
JARVIS OS — Apps Center REST API Router.
Exposes application catalog, search, launching, user favorites, recent apps,
user-isolated settings, shared AI inferences, resource telemetry, and admin controls.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from pydantic import BaseModel, Field

from apps.apps_center.ai_service import shared_ai
from apps.apps_center.database import apps_db
from apps.apps_center.models import (
    ApplicationManifest,
    AppCategory,
    AppStatus,
    ResourceProfile,
)
from apps.apps_center.permissions import apps_permissions
from apps.apps_center.registry import app_registry
from apps.apps_center.resource_manager import resource_manager
from apps.apps_center.task_manager import task_manager
from tools.identity.user_manager import UserRole, user_manager

logger = logging.getLogger("JARVIS.API.AppsCenter")

apps_center_router = APIRouter(prefix="/apps", tags=["apps_center"])


# ─── Request Schemas ─────────────────────────────────────────

class AppLaunchRequest(BaseModel):
    user_id: Optional[str] = "guest"
    pin: Optional[str] = None


class AppSettingsRequest(BaseModel):
    user_id: Optional[str] = "guest"
    settings: Dict[str, Any] = Field(default_factory=dict)


class AppStatusUpdateRequest(BaseModel):
    app_id: str
    status: AppStatus
    admin_pin: str


class SharedChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    provider: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7


class SharedSummarizeRequest(BaseModel):
    text: str
    max_words: Optional[int] = 150
    provider: Optional[str] = None


class SharedClassifyRequest(BaseModel):
    text: str
    categories: List[str]
    provider: Optional[str] = None


class SharedJsonRequest(BaseModel):
    prompt: str
    schema_or_example: Dict[str, Any]
    system_prompt: Optional[str] = None


# ─── Endpoints ───────────────────────────────────────────────

@apps_center_router.get("/catalog")
def get_application_catalog(
    query: Optional[str] = Query(None, description="Search term for name or description"),
    category: Optional[str] = Query(None, description="Category filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    capability: Optional[str] = Query(None, description="Capability filter"),
    user_id: Optional[str] = Query("guest", description="Current user ID for favorite status"),
):
    """
    Search and filter application manifests in the central registry.
    Decorates results with user favorite flags.
    """
    apps = app_registry.search_apps(query=query, category=category, status=status, capability=capability)
    user_favs = set(apps_db.get_user_favorites(user_id=user_id or "guest"))

    out = []
    for app in apps:
        d = app.model_dump()
        d["is_favorite"] = app.id in user_favs
        out.append(d)

    return {
        "status": "ok",
        "total": len(out),
        "applications": out,
    }


@apps_center_router.get("/categories")
def get_categories():
    """Return all 10 application categories with item counts."""
    return {
        "status": "ok",
        "categories": app_registry.get_categories(),
    }


@apps_center_router.get("/app/{app_id}")
def get_app_details(
    app_id: str,
    user_id: Optional[str] = Query("guest"),
):
    """Fetch complete metadata, resource requirements, and settings for a single app."""
    manifest = app_registry.get_app(app_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found in registry.")

    user_favs = set(apps_db.get_user_favorites(user_id=user_id or "guest"))
    user_settings = apps_db.get_app_settings(app_id=app_id, user_id=user_id or "guest")

    d = manifest.model_dump()
    d["is_favorite"] = manifest.id in user_favs
    d["user_settings"] = user_settings

    return {
        "status": "ok",
        "application": d,
    }


@apps_center_router.post("/launch/{app_id}")
def launch_application(
    app_id: str,
    req: Optional[AppLaunchRequest] = None,
):
    """
    Attempt to open an application.
    Enforces that Planned applications cannot be launched and returns roadmap information.
    Available applications record launch telemetry and return target routes.
    """
    manifest = app_registry.get_app(app_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found.")

    user_id = req.user_id if req else "guest"
    pin = req.pin if req else None

    # Determine user role securely
    current_user, role = apps_permissions.get_current_user_role(pin=pin, user_id=user_id)

    # Check launch permissions and lifecycle state
    can_launch, reason = apps_permissions.can_launch_app(manifest, role)
    if not can_launch:
        # If planned, return truthful HTTP 400 with roadmap
        if manifest.status == AppStatus.PLANNED:
            raise HTTPException(
                status_code=400,
                detail=f"'{manifest.name}' is currently in roadmap (Planned) and not yet implemented. {manifest.roadmap or ''}",
            )
        raise HTTPException(status_code=403, detail=reason or "Cannot launch application")

    # Record recent launch in DB
    apps_db.record_app_opened(user_id=user_id, app_id=manifest.id)

    return {
        "status": "ok",
        "success": True,
        "app_id": manifest.id,
        "name": manifest.name,
        "route": manifest.route,
        "target_tab": manifest.target_tab,
        "message": f"Application '{manifest.name}' launched successfully.",
    }


@apps_center_router.post("/favorite/{app_id}")
def toggle_favorite(
    app_id: str,
    user_id: Optional[str] = Query("guest"),
):
    """Toggle starred / favorite state for an application."""
    manifest = app_registry.get_app(app_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found.")

    is_fav = apps_db.toggle_favorite(user_id=user_id or "guest", app_id=app_id)
    return {
        "status": "ok",
        "app_id": app_id,
        "is_favorite": is_fav,
    }


@apps_center_router.get("/favorites")
def get_user_favorites(
    user_id: Optional[str] = Query("guest"),
):
    """Retrieve list of starred application IDs for the specified user."""
    fav_ids = apps_db.get_user_favorites(user_id=user_id or "guest")
    # Return manifest summaries
    fav_apps = [app_registry.get_app(aid).model_dump() for aid in fav_ids if app_registry.get_app(aid)]
    return {
        "status": "ok",
        "favorites": fav_apps,
    }


@apps_center_router.get("/recent")
def get_recent_apps(
    user_id: Optional[str] = Query("guest"),
    limit: Optional[int] = Query(6, ge=1, le=20),
):
    """Retrieve recently opened applications for the user."""
    recents = apps_db.get_recently_opened(user_id=user_id or "guest", limit=limit or 6)
    out = []
    for r in recents:
        manifest = app_registry.get_app(r["app_id"])
        if manifest:
            d = manifest.model_dump()
            d["opened_at"] = r["opened_at"]
            out.append(d)

    return {
        "status": "ok",
        "recent_apps": out,
    }


@apps_center_router.get("/settings/{app_id}")
def get_app_settings(
    app_id: str,
    user_id: Optional[str] = Query("guest"),
):
    """Fetch user-isolated application configuration."""
    manifest = app_registry.get_app(app_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found.")

    settings = apps_db.get_app_settings(app_id=app_id, user_id=user_id or "guest")
    return {
        "status": "ok",
        "app_id": app_id,
        "settings": settings,
    }


@apps_center_router.post("/settings/{app_id}")
def save_app_settings(
    app_id: str,
    req: AppSettingsRequest,
):
    """Persist user-isolated application configuration."""
    manifest = app_registry.get_app(app_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found.")

    user_id = req.user_id or "guest"
    for k, v in req.settings.items():
        apps_db.set_app_setting(app_id=app_id, user_id=user_id, key=k, value=v)

    return {
        "status": "ok",
        "app_id": app_id,
        "message": "Settings saved successfully.",
    }


# ─── Shared AI Services ──────────────────────────────────────

@apps_center_router.get("/providers")
def get_ai_providers():
    """Return truthful status, models, and connection states of all AI providers."""
    return {
        "status": "ok",
        "providers": shared_ai.get_providers_status(),
    }


@apps_center_router.post("/ai/chat")
def shared_chat(req: SharedChatRequest):
    """Execute shared chat completion."""
    res = shared_ai.chat_completion(
        messages=req.messages,
        provider=req.provider,
        model=req.model,
        system_prompt=req.system_prompt,
        temperature=req.temperature or 0.7,
    )
    if not res.get("success"):
        raise HTTPException(status_code=503, detail=res.get("error", "AI provider failure"))
    return res


@apps_center_router.post("/ai/summarize")
def shared_summarize(req: SharedSummarizeRequest):
    """Execute shared text summarization."""
    res = shared_ai.summarize(text=req.text, max_words=req.max_words or 150)
    return {"status": "ok", **res}


@apps_center_router.post("/ai/classify")
def shared_classify(req: SharedClassifyRequest):
    """Execute shared category classification."""
    res = shared_ai.classify(text=req.text, categories=req.categories)
    return {"status": "ok", **res}


@apps_center_router.post("/ai/json")
def shared_json(req: SharedJsonRequest):
    """Execute shared structured JSON synthesis."""
    res = shared_ai.generate_structured_json(
        prompt=req.prompt,
        json_schema_or_example=req.schema_or_example,
        system=req.system_prompt,
    )
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "JSON synthesis failure"))
    return res


# ─── Hardware Resource Telemetry ─────────────────────────────

@apps_center_router.get("/resources")
def get_system_resources():
    """Return truthful Raspberry Pi 5 CPU, RAM, Disk, and SoC temperature metrics."""
    return {
        "status": "ok",
        "telemetry": resource_manager.get_real_telemetry(),
    }


# ─── Task Management Endpoints ───────────────────────────────

@apps_center_router.get("/tasks")
def list_tasks(
    user_id: Optional[str] = Query("guest"),
    app_id: Optional[str] = Query(None),
):
    """List background application tasks for the current user."""
    tasks = task_manager.list_user_tasks(user_id=user_id or "guest", app_id=app_id)
    return {
        "status": "ok",
        "total": len(tasks),
        "tasks": tasks,
    }


@apps_center_router.post("/tasks/cancel/{task_id}")
def cancel_task(
    task_id: str,
    user_id: Optional[str] = Query("guest"),
):
    """Cancel a running or queued background task."""
    ok = task_manager.cancel_task(task_id=task_id, user_id=user_id or "guest")
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found or cancellation unauthorized.")
    return {
        "status": "ok",
        "task_id": task_id,
        "message": "Task cancellation signal dispatched.",
    }


# ─── Admin Status Governance ─────────────────────────────────

@apps_center_router.post("/admin/status")
def update_application_status(req: AppStatusUpdateRequest):
    """
    Administrator endpoint to enable, disable, or transition application status.
    Protected by PBKDF2-HMAC-SHA256 admin PIN verification.
    """
    is_valid, msg = user_manager.verify_admin_pin(req.admin_pin)
    if not is_valid:
        raise HTTPException(status_code=403, detail=f"Administrator verification failed: {msg}")

    manifest = app_registry.get_app(req.app_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Application '{req.app_id}' not found.")

    success = app_registry.set_app_status(req.app_id, req.status)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update application status.")

    return {
        "status": "ok",
        "app_id": req.app_id,
        "new_status": req.status.value,
        "message": f"Status for '{manifest.name}' updated to {req.status.value}.",
    }
