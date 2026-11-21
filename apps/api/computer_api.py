"""
JARVIS OS — Phase 4 Computer Use REST API Router
Exposes desktop perception, window listing, screenshot capture, UI element discovery,
action execution, and multi-step computer task management.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("JARVIS.API.Computer")

from tools.desktop.desktop_perception import desktop_perception
from tools.desktop.element_detector import element_detector
from tools.desktop.computer_action_engine import computer_action_engine
from tools.identity.permission_manager import permission_manager

router = APIRouter(prefix="/api/computer", tags=["Computer Use"])


def _require_computer_permission(tool_name: str) -> None:
    """Enforce role-based access on computer-interaction hardware actions.

    Raises HTTP 403 when the active session lacks permission for the tool.
    Read-only introspection endpoints are intentionally left ungated.
    """
    allowed, reason = permission_manager.check_tool_permission(tool_name)
    if not allowed:
        logger.warning("Computer access denied for %s: %s", tool_name, reason)
        raise HTTPException(status_code=403, detail=reason)


_COMPUTER_ACTION_TOOLS = {
    "click": "computer_click",
    "double_click": "computer_double_click",
    "right_click": "computer_right_click",
    "click_named": "computer_click",
    "move_mouse": "computer_move_mouse",
    "type": "computer_type",
    "press_key": "computer_press_key",
    "press_hotkey": "computer_press_hotkey",
    "scroll": "computer_scroll",
    "switch_window": "computer_switch_window",
    "focus_window": "computer_focus_window",
    "minimize": "computer_minimize_window",
    "maximize": "computer_maximize_window",
    "emergency_stop": "computer_stop",
}

# Pydantic Schemas
class CommandRequest(BaseModel):
    instruction: str = Field(..., description="Natural language computer instruction (e.g. 'Select option 1 and click Submit')")

class MoveMouseRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    target: Optional[str] = None
    smooth: bool = True

class BrowserNavigateRequest(BaseModel):
    url: str

class BrowserSelectRequest(BaseModel):
    option: str
    verify: bool = True

class BrowserClickRequest(BaseModel):
    button: str
    verify: bool = True

class ModeRequest(BaseModel):
    mode: str = Field(..., description="'observe', 'guided', 'command_control', or 'trusted_workflow'")

class ScreenshotRequest(BaseModel):
    target: str = Field(default="fullscreen", description="'fullscreen', 'active_window', or 'region'")
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

class FindElementRequest(BaseModel):
    query: str = Field(..., description="Semantic query (e.g. 'settings', 'search', 'close', 'tab 1')")
    window_id: Optional[str] = None

class ActionRequest(BaseModel):
    action: str = Field(..., description="Action name: click, double_click, right_click, click_named, move_mouse, type, press_key, press_hotkey, scroll, switch_window, focus_window, minimize, maximize")
    x: Optional[int] = None
    y: Optional[int] = None
    query: Optional[str] = None
    text: Optional[str] = None
    key: Optional[str] = None
    hotkey: Optional[str] = None
    app: Optional[str] = None
    direction: Optional[str] = "down"
    clicks: Optional[int] = 1
    target_window: Optional[str] = None
    verify: bool = True

class TaskCreateRequest(BaseModel):
    name: str = Field(..., description="Human-readable task title")
    steps: List[Dict[str, Any]] = Field(..., description="Ordered list of step actions")


@router.get("/status")
def get_computer_status() -> Dict[str, Any]:
    """Get high-level status of the computer use subsystem."""
    from tools.desktop.unified_computer_service import unified_computer_service
    u_stat = unified_computer_service.get_status()

    resolution = desktop_perception.get_screen_resolution()
    active_win = desktop_perception.get_active_window()
    wins = desktop_perception.list_open_windows()
    last_obs = desktop_perception.get_last_observation()

    return {
        **u_stat,
        "display": desktop_perception.display,
        "resolution": resolution,
        "active_window": active_win,
        "open_window_count": len([w for w in wins if w.get("desktop", 0) != -1]),
        "total_windows": len(wins),
        "last_observation_timestamp": last_obs.get("timestamp") if last_obs else None,
        "recent_actions_count": len(unified_computer_service.get_history()),
    }


@router.get("/windows")
def list_desktop_windows() -> Dict[str, Any]:
    """List all open desktop windows with geometry and application metadata."""
    wins = desktop_perception.list_open_windows()
    active_win = desktop_perception.get_active_window()
    return {
        "status": "ok",
        "count": len(wins),
        "active_window_id": active_win.get("id"),
        "windows": wins,
    }


@router.get("/applications")
def list_running_applications() -> Dict[str, Any]:
    """List distinct running applications currently visible in the window manager."""
    wins = desktop_perception.list_open_windows()
    apps = {}
    for w in wins:
        if w.get("desktop", 0) == -1:
            continue
        app_name = w.get("app", "unknown")
        if app_name not in apps:
            apps[app_name] = []
        apps[app_name].append({
            "id": w["id"],
            "title": w["title"],
            "pid": w.get("pid"),
            "geometry": w.get("geometry"),
        })

    return {
        "status": "ok",
        "application_count": len(apps),
        "applications": apps,
    }


@router.post("/screenshot")
def capture_screenshot(req: ScreenshotRequest) -> Dict[str, Any]:
    """Capture fullscreen, active window, or region screenshot with thumbnail generation."""
    _require_computer_permission("desktop_screenshot")
    if req.target == "active_window":
        snap = desktop_perception.capture_active_window()
    elif req.target == "region" and all(v is not None for v in [req.x, req.y, req.width, req.height]):
        snap = desktop_perception.capture_region(req.x, req.y, req.width, req.height)  # type: ignore
    else:
        snap = desktop_perception.capture_fullscreen()

    if snap.get("status") == "error":
        raise HTTPException(status_code=500, detail=snap.get("message", "Screenshot failed"))
    return snap


@router.post("/observe")
def observe_desktop() -> Dict[str, Any]:
    """Execute a complete perceptual observation cycle of the current desktop."""
    _require_computer_permission("desktop_perception")
    return desktop_perception.observe_desktop()


@router.post("/find-element")
def find_ui_element(req: FindElementRequest) -> Dict[str, Any]:
    """Locate a UI element matching query keywords."""
    act_win = desktop_perception.get_active_window()
    elem = element_detector.find_element(req.query, act_win)
    if not elem:
        return {"status": "not_found", "query": req.query, "element": None}
    return {"status": "ok", "query": req.query, "element": elem.to_dict()}


@router.post("/action")
def execute_computer_action(req: ActionRequest) -> Dict[str, Any]:
    """Dispatch a single verified computer interaction."""
    act = req.action.lower()
    tool = _COMPUTER_ACTION_TOOLS.get(act)
    if tool is not None:
        _require_computer_permission(tool)

    if act == "click":
        if req.x is None or req.y is None:
            raise HTTPException(status_code=400, detail="Click requires x and y coordinates")
        return computer_action_engine.click_element(req.x, req.y, clicks=req.clicks or 1, verify=req.verify)

    elif act == "click_named":
        if not req.query:
            raise HTTPException(status_code=400, detail="click_named requires 'query' parameter")
        return computer_action_engine.click_named_element(req.query, verify=req.verify)

    elif act == "double_click":
        if req.x is None or req.y is None:
            raise HTTPException(status_code=400, detail="double_click requires x and y coordinates")
        return computer_action_engine.double_click_element(req.x, req.y, verify=req.verify)

    elif act == "right_click":
        if req.x is None or req.y is None:
            raise HTTPException(status_code=400, detail="right_click requires x and y coordinates")
        return computer_action_engine.right_click_element(req.x, req.y, verify=req.verify)

    elif act == "type":
        if not req.text:
            raise HTTPException(status_code=400, detail="type requires 'text' parameter")
        return computer_action_engine.type_text(req.text, target_window=req.target_window, verify=req.verify)

    elif act == "press_key":
        if not req.key:
            raise HTTPException(status_code=400, detail="press_key requires 'key' parameter")
        return computer_action_engine.press_key(req.key)

    elif act == "press_hotkey":
        if not req.hotkey:
            raise HTTPException(status_code=400, detail="press_hotkey requires 'hotkey' parameter")
        return computer_action_engine.press_hotkey(req.hotkey)

    elif act == "scroll":
        return computer_action_engine.scroll_page(direction=req.direction or "down", clicks=req.clicks or 5)

    elif act == "switch_window":
        if not req.app:
            raise HTTPException(status_code=400, detail="switch_window requires 'app' parameter")
        return computer_action_engine.switch_window(req.app)

    elif act == "focus_window":
        if not req.target_window:
            raise HTTPException(status_code=400, detail="focus_window requires 'target_window' parameter")
        return computer_action_engine.focus_window(req.target_window)

    elif act == "minimize":
        if not req.target_window:
            raise HTTPException(status_code=400, detail="minimize requires 'target_window' parameter")
        return computer_action_engine.minimize_window(req.target_window)

    elif act == "move_mouse":
        if req.x is None or req.y is None:
            raise HTTPException(status_code=400, detail="move_mouse requires x and y coordinates")
        return computer_action_engine.move_cursor(req.x, req.y)

    elif act == "maximize":
        if not req.target_window:
            raise HTTPException(status_code=400, detail="maximize requires 'target_window' parameter")
        return computer_action_engine.maximize_window(req.target_window)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action '{req.action}'")


@router.get("/history")
def get_action_history() -> Dict[str, Any]:
    """Retrieve recent action logs with verification evidence."""
    from tools.desktop.unified_computer_service import unified_computer_service
    return {"status": "ok", "history": unified_computer_service.get_history()}


# Multi-Step Computer Tasks
@router.post("/task")
def create_and_run_task(req: TaskCreateRequest) -> Dict[str, Any]:
    """Create and immediately execute an ordered multi-step computer task."""
    task = computer_action_engine.create_task(req.name, req.steps)
    res = computer_action_engine.execute_task(task["task_id"])
    return res


@router.get("/task/{task_id}")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Query status and step progress of a computer task."""
    task = computer_action_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"status": "ok", "task": task}


@router.post("/task/{task_id}/stop")
def stop_task(task_id: str) -> Dict[str, Any]:
    """Halt an active computer task."""
    res = computer_action_engine.stop_task(task_id)
    return res


# ── Unified Computer Control Endpoints ────────────────────────

@router.post("/execute-command")
def execute_natural_command(req: CommandRequest) -> Dict[str, Any]:
    """Execute a natural-language computer automation instruction with verification."""
    from tools.desktop.unified_computer_service import unified_computer_service
    return unified_computer_service.execute_natural_instruction(req.instruction)


@router.post("/stop")
def emergency_stop() -> Dict[str, Any]:
    """Emergency stop kill switch — immediately halts all automation and releases inputs."""
    from tools.desktop.unified_computer_service import unified_computer_service
    return unified_computer_service.emergency_stop()


@router.post("/reset-stop")
def reset_stop() -> Dict[str, Any]:
    """Clear emergency stop condition."""
    from tools.desktop.unified_computer_service import unified_computer_service
    return unified_computer_service.reset_emergency_stop()


@router.get("/mode")
def get_control_mode() -> Dict[str, Any]:
    """Get active safety mode (observe, guided, command_control, trusted_workflow)."""
    from tools.desktop.unified_computer_service import unified_computer_service
    return {"status": "ok", "mode": unified_computer_service.mode.value}


@router.post("/mode")
def set_control_mode(req: ModeRequest) -> Dict[str, Any]:
    """Set active safety mode."""
    from tools.desktop.unified_computer_service import unified_computer_service
    try:
        mode = unified_computer_service.set_mode(req.mode)
        return {"status": "ok", "mode": mode.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mouse/move")
def move_mouse(req: MoveMouseRequest) -> Dict[str, Any]:
    """Move genuine mouse pointer to target coordinates or named element."""
    _require_computer_permission("computer_move_mouse")
    from tools.desktop.native_backend import native_backend
    from tools.desktop.screen_intelligence import screen_intelligence

    if req.target:
        res = screen_intelligence.resolve_target(req.target)
        if res.get("status") == "ok":
            el = res.get("element", {})
            center = el.get("center") or {}
            cx, cy = center.get("x"), center.get("y")
            if cx is not None and cy is not None:
                return native_backend.move_cursor(cx, cy, duration=0.25, smooth=req.smooth)
        raise HTTPException(status_code=404, detail=f"Target '{req.target}' not located")

    if req.x is None or req.y is None:
        raise HTTPException(status_code=400, detail="Provide either 'target' or both 'x' and 'y'")

    return native_backend.move_cursor(req.x, req.y, duration=0.25, smooth=req.smooth)


@router.get("/mouse/position")
def get_mouse_position() -> Dict[str, Any]:
    """Get current pointer coordinates on desktop."""
    from tools.desktop.native_backend import native_backend
    return {"status": "ok", "position": native_backend.get_cursor_position()}


@router.post("/browser/navigate")
def browser_navigate(req: BrowserNavigateRequest) -> Dict[str, Any]:
    """Open or navigate Playwright browser to URL."""
    from tools.desktop.browser_backend import browser_backend
    return browser_backend.navigate(req.url)


@router.post("/browser/select")
def browser_select_option(req: BrowserSelectRequest) -> Dict[str, Any]:
    """Select option (radio button, checkbox, dropdown) semantically."""
    from tools.desktop.browser_backend import browser_backend
    return browser_backend.select_option(req.option, verify=req.verify)


@router.post("/browser/click")
def browser_click_button(req: BrowserClickRequest) -> Dict[str, Any]:
    """Click a button in the browser with ambiguity detection."""
    from tools.desktop.browser_backend import browser_backend
    return browser_backend.click_button(req.button, verify=req.verify)


@router.get("/browser/dom")
def browser_inspect_dom() -> Dict[str, Any]:
    """Inspect active page accessible DOM and form elements."""
    from tools.desktop.browser_backend import browser_backend
    return browser_backend.inspect_dom()


@router.get("/fixture/test-page")
def get_test_fixture():
    """Serve the local test application fixture for browser & desktop automation tests."""
    from fastapi.responses import FileResponse
    import os
    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures", "computer_control_test_page.html"))
    if os.path.exists(fixture_path):
        return FileResponse(fixture_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Test fixture HTML file not found")


# --- Antigravity IDE Automation & Auto-Approver Endpoints ---

@router.post("/antigravity/apply-settings")
def antigravity_apply_settings() -> Dict[str, Any]:
    """Apply Antigravity eager command execution policy and PreToolUse lifecycle hook."""
    from tools.desktop.antigravity_approver import apply_antigravity_settings
    return apply_antigravity_settings()


@router.post("/antigravity/auto-approve/run-once")
async def antigravity_auto_approve_run_once(port: int = Query(9333, description="Antigravity CDP debugging port")) -> Dict[str, Any]:
    """Scan all open Antigravity conversation tabs once and auto-accept Option 1."""
    from tools.desktop.antigravity_approver import scan_and_auto_approve_cdp
    return await scan_and_auto_approve_cdp(cdp_port=port)


@router.post("/antigravity/auto-approve/start")
def antigravity_auto_approve_start(port: int = Query(9333, description="Antigravity CDP debugging port")) -> Dict[str, Any]:
    """Start the background Antigravity auto-approver supervisor daemon."""
    from tools.desktop.antigravity_approver import antigravity_supervisor
    antigravity_supervisor.cdp_port = port
    return antigravity_supervisor.start()


@router.post("/antigravity/auto-approve/stop")
def antigravity_auto_approve_stop() -> Dict[str, Any]:
    """Stop the background Antigravity auto-approver supervisor daemon."""
    from tools.desktop.antigravity_approver import antigravity_supervisor
    return antigravity_supervisor.stop()


@router.get("/antigravity/auto-approve/status")
def antigravity_auto_approve_status() -> Dict[str, Any]:
    """Get the live status of the Antigravity auto-approver daemon and configuration."""
    from tools.desktop.antigravity_approver import antigravity_supervisor
    return antigravity_supervisor.get_status()


