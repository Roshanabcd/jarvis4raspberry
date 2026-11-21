"""
JARVIS OS — Operator Profile & Account Center REST API.
Exposes endpoints for profile management, avatar uploads, preferences persistence,
session lifecycle controls, YuNet face biometric enrollment, and security activity logging.
"""

import datetime
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from apps.api.active_desktop_api import require_local_dashboard
from apps.voice.session_manager import voice_session_mgr
from tools.identity.permission_manager import permission_manager
from tools.identity.user_manager import AVATARS_DIR, UserRole, user_manager
from tools.vision.camera_manager import camera_manager

logger = logging.getLogger("JARVIS.API.Account")

account_router = APIRouter(prefix="/account", tags=["account"])


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=128)
    bio: Optional[str] = Field(None, max_length=512)
    callsign: Optional[str] = Field(None, max_length=64)


class AvatarPresetRequest(BaseModel):
    preset: str = Field(..., min_length=1, max_length=64)


class PreferencesUpdateRequest(BaseModel):
    default_tab: Optional[str] = Field(None, max_length=32)
    voice_greeting: Optional[bool] = None
    notification_speech: Optional[str] = Field(None, max_length=32)
    default_model: Optional[str] = Field(None, max_length=128)
    default_voice: Optional[str] = Field(None, max_length=128)


class SessionDurationRequest(BaseModel):
    duration_s: float = Field(..., ge=60, le=864000)


class ChangePinRequest(BaseModel):
    current_pin: str = Field(..., min_length=4)
    new_pin: str = Field(..., min_length=4)
    confirm_pin: str = Field(..., min_length=4)


class FaceEnrollRequest(BaseModel):
    photo_path: Optional[str] = None
    capture_camera: bool = True


class UserRoleChangeRequest(BaseModel):
    target_user_id: str
    new_role: str
    admin_pin: str


class UserResetPinRequest(BaseModel):
    target_user_id: str
    new_pin: str
    admin_pin: str


@account_router.get("/profile")
def get_operator_profile():
    """Return active operator profile, live session details, and account KPI stats."""
    active_session = voice_session_mgr.get_active_session()
    active_perm = permission_manager.get_active_user() or {}
    admin_user = user_manager.get_admin_user() or {}
    
    # Active identity metadata
    user_id = active_session.user_id if active_session.is_authenticated else (admin_user.get("user_id") or "guest")
    user_doc = user_manager.get_user(user_id) or admin_user or {}

    role = active_session.authorization_role()
    now = time.time()
    remaining_s = max(0.0, round(active_session.expires_at - now, 1))

    access_desc = "GUEST (Read-Only Telemetry)"
    if role == "ADMIN":
        access_desc = "ADMIN (Full System Privileges)"
    elif role == "USER":
        access_desc = "USER (Standard Operator)"

    all_users = user_manager.list_users()

    return {
        "user_id": user_id,
        "display_name": user_doc.get("display_name") or active_session.display_name or "Guest",
        "role": role,
        "bio": user_doc.get("bio", "Lead Robotics Engineer · JARVIS OS"),
        "callsign": user_doc.get("callsign") or user_doc.get("display_name") or "Roshan",
        "avatar_url": user_doc.get("avatar_url"),
        "avatar_preset": user_doc.get("avatar_preset", "preset_reactor"),
        "is_authenticated": active_session.is_authenticated,
        "is_admin_elevated": active_session.is_admin_elevated,
        "session_expires_at": active_session.expires_at,
        "session_remaining_s": remaining_s,
        "session_ttl_s": voice_session_mgr.session_ttl_s,
        "host_hardware": "Raspberry Pi 5 · aarch64 (Linux)",
        "stats": {
            "access_level": access_desc,
            "face_id_enrolled": bool(user_doc.get("has_face_enrolled")),
            "face_confidence": user_doc.get("face_confidence") or 0.0,
            "registered_users_count": len(all_users),
            "last_sign_in": user_doc.get("last_sign_in_at") or user_doc.get("enrolled_at") or "Active now",
        }
    }


@account_router.post("/profile", dependencies=[Depends(require_local_dashboard)])
def update_operator_profile(req: ProfileUpdateRequest):
    """Update operator display name, bio, or preferred callsign."""
    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")
    
    res = user_manager.update_profile(
        user_id=user_id,
        display_name=req.display_name,
        bio=req.bio,
        callsign=req.callsign
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@account_router.post("/avatar", dependencies=[Depends(require_local_dashboard)])
async def upload_avatar_file(file: UploadFile = File(...)):
    """Upload custom profile avatar image file and persist to private storage."""
    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")
    
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        raise HTTPException(400, "Supported formats: PNG, JPG, JPEG, WEBP, SVG")

    filename = f"avatar_{user_id}_{int(time.time())}{ext}"
    dest_path = AVATARS_DIR / filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Failed to save avatar image: {e}")

    avatar_url = f"/api/account/avatar_file/{filename}"
    res = user_manager.update_avatar(user_id=user_id, avatar_url=avatar_url)
    return {**res, "avatar_url": avatar_url}


@account_router.get("/avatar_file/{filename}")
def serve_avatar_file(filename: str):
    """Serve uploaded avatar file safely."""
    # Prevent path traversal
    safe_name = os.path.basename(filename)
    file_path = AVATARS_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(404, "Avatar image not found")
    return FileResponse(file_path)


@account_router.post("/avatar/preset", dependencies=[Depends(require_local_dashboard)])
def set_avatar_preset(req: AvatarPresetRequest):
    """Set preset icon monogram."""
    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")
    res = user_manager.update_avatar(user_id=user_id, avatar_preset=req.preset)
    return res


@account_router.post("/avatar/capture", dependencies=[Depends(require_local_dashboard)])
def capture_avatar_camera():
    """Capture fresh photo from Sony IMX708 camera and set as operator avatar."""
    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")

    cap = camera_manager.capture_photo()
    if not cap or not cap.get("success"):
        raise HTTPException(500, f"Camera capture failed: {cap.get('error') if cap else 'No response'}")

    photo_path = cap.get("image_path")
    if not photo_path or not os.path.exists(photo_path):
        raise HTTPException(500, "Captured photo file not found")

    filename = f"avatar_cam_{user_id}_{int(time.time())}.jpg"
    dest_path = AVATARS_DIR / filename
    try:
        shutil.copy(photo_path, dest_path)
    except Exception as e:
        raise HTTPException(500, f"Failed to persist avatar frame: {e}")

    avatar_url = f"/api/account/avatar_file/{filename}"
    res = user_manager.update_avatar(user_id=user_id, avatar_url=avatar_url)
    return {**res, "avatar_url": avatar_url}


@account_router.get("/preferences")
def get_preferences():
    """Get persisted operator preferences."""
    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")
    u = user_manager.get_user(user_id) or {}
    return {
        "preferences": u.get("preferences", {
            "default_tab": "home",
            "voice_greeting": True,
            "notification_speech": "important",
            "default_model": "nvidia/nemotron-3.5-bolt-e4b",
            "default_voice": "en-US-GuyNeural"
        })
    }


@account_router.post("/preferences", dependencies=[Depends(require_local_dashboard)])
def update_preferences(req: PreferencesUpdateRequest):
    """Save operator preferences."""
    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    res = user_manager.update_preferences(user_id=user_id, preferences=updates)
    return res


@account_router.post("/session/extend", dependencies=[Depends(require_local_dashboard)])
def extend_session(duration_s: Optional[float] = Query(None)):
    """Extend current session countdown timer."""
    sess = voice_session_mgr.extend_session(duration_s)
    remaining_s = max(0.0, round(sess.expires_at - time.time(), 1))
    user_manager.log_activity("SESSION_EXTEND", f"Session extended ({round(remaining_s)}s remaining)", sess.display_name, sess.authorization_role(), "success")
    return {
        "success": True,
        "expires_at": sess.expires_at,
        "remaining_s": remaining_s,
        "authorization_role": sess.authorization_role()
    }


@account_router.post("/session/duration", dependencies=[Depends(require_local_dashboard)])
def set_session_duration_policy(req: SessionDurationRequest):
    """Update active and default administrator session expiration policy."""
    voice_session_mgr.set_session_ttl(req.duration_s)
    user_manager.log_activity("SESSION_POLICY", f"Session duration set to {round(req.duration_s / 60)} minutes", "Administrator", "ADMIN", "success")
    return {
        "success": True,
        "session_ttl_s": req.duration_s,
        "message": f"Administrator session policy set to {round(req.duration_s / 60)} minutes."
    }


@account_router.get("/activity")
def get_security_activity(limit: int = Query(20, ge=1, le=50)):
    """Return recent security, authentication, and access activity events."""
    return {"activity": user_manager.get_activity(limit=limit)}


@account_router.delete("/activity", dependencies=[Depends(require_local_dashboard)])
def clear_security_activity(admin_pin: str = Query(...)):
    """Clear security activity audit log with admin PIN authorization."""
    ok, msg = user_manager.verify_admin_pin(admin_pin)
    if not ok:
        raise HTTPException(401, f"Admin authorization failed: {msg}")
    user_manager.clear_activity()
    user_manager.log_activity("AUDIT_CLEAR", "Security activity log cleared", "Administrator", "ADMIN", "warning")
    return {"success": True, "message": "Security activity log cleared."}


@account_router.post("/change_pin", dependencies=[Depends(require_local_dashboard)])
def change_pin(req: ChangePinRequest):
    """Change PIN with current PIN verification."""
    if req.new_pin != req.confirm_pin:
        raise HTTPException(400, "New PIN and confirmation do not match.")
    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")

    ok, msg = user_manager.change_pin(user_id=user_id, current_pin=req.current_pin, new_pin=req.new_pin)
    if not ok:
        raise HTTPException(400, msg)
    return {"success": True, "message": msg}


@account_router.post("/face/enroll", dependencies=[Depends(require_local_dashboard)])
def enroll_face_id(req: FaceEnrollRequest):
    """Enroll or update face recognition embeddings directly inside Account Center."""
    photo_path = req.photo_path
    if req.capture_camera or not photo_path:
        cap = camera_manager.capture_photo()
        if not cap or not cap.get("success"):
            raise HTTPException(500, f"Camera snapshot failed: {cap.get('error') if cap else 'Camera unavailable'}")
        photo_path = cap.get("image_path")

    admin_user = user_manager.get_admin_user() or {}
    user_id = admin_user.get("user_id", "admin")

    res = user_manager.enroll_or_update_face(user_id=user_id, photo_path=photo_path)
    if not res.get("success"):
        raise HTTPException(400, res.get("error", "Biometric enrollment failed"))
    return res


@account_router.post("/users/role", dependencies=[Depends(require_local_dashboard)])
def change_user_role(req: UserRoleChangeRequest):
    """Change role of a registered operator (requires admin PIN)."""
    ok, msg = user_manager.admin_change_user_role(target_user_id=req.target_user_id, new_role=req.new_role, admin_pin=req.admin_pin)
    if not ok:
        raise HTTPException(400, msg)
    return {"success": True, "message": msg}


@account_router.post("/users/reset_pin", dependencies=[Depends(require_local_dashboard)])
def reset_user_pin(req: UserResetPinRequest):
    """Reset PIN of a registered operator (requires admin PIN)."""
    ok, msg = user_manager.admin_reset_user_pin(target_user_id=req.target_user_id, new_pin=req.new_pin, admin_pin=req.admin_pin)
    if not ok:
        raise HTTPException(400, msg)
    return {"success": True, "message": msg}
