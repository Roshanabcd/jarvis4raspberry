"""
JARVIS OS — Identity & User Management REST API.
Exposes endpoints for administrator enrollment, user management, PIN verification,
and face recognition identification.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from tools.identity.user_manager import UserManager, UserRole, user_manager
from tools.identity.permission_manager import PermissionManager, permission_manager
from tools.vision.camera_manager import CameraManager

logger = logging.getLogger("JARVIS.API.Identity")

identity_router = APIRouter(prefix="/identity", tags=["identity"])


class AdminEnrollmentRequest(BaseModel):
    display_name: str = Field(..., min_length=1, description="Administrator's display name")
    pin: str = Field(..., min_length=4, description="Secret administrator PIN (at least 4 digits)")
    photo_path: Optional[str] = Field(None, description="Path to captured enrollment photo")
    capture_camera: bool = Field(False, description="Capture a fresh frame from Sony IMX708 camera directly")
    confirmed: bool = Field(False, description="Explicit confirmation of enrollment")


class UserEnrollmentRequest(BaseModel):
    display_name: str = Field(..., min_length=1)
    role: str = Field("USER", description="Role: USER or GUEST")
    admin_pin: str = Field(..., min_length=4)
    photo_path: Optional[str] = None
    capture_camera: bool = False


class PinVerificationRequest(BaseModel):
    pin: str = Field(..., min_length=1)


class IdentifyRequest(BaseModel):
    photo_path: Optional[str] = None
    capture_camera: bool = True


@identity_router.get("/status")
def get_identity_status():
    """Return status of administrator enrollment, active session, and lockout."""
    is_admin = user_manager.is_admin_enrolled()
    admin_user = user_manager.get_admin_user()
    is_locked, remaining_s = user_manager.is_pin_locked()
    active_user = permission_manager.get_active_user()

    return {
        "is_admin_enrolled": is_admin,
        "admin_name": admin_user.get("display_name") if admin_user else None,
        "active_user": active_user,
        "is_pin_locked": is_locked,
        "lockout_remaining_s": remaining_s,
        "total_users": len(user_manager.list_users()),
    }


@identity_router.post("/enroll_admin")
def enroll_admin(req: AdminEnrollmentRequest):
    """Enroll the primary administrator with face recognition template and secure PIN."""
    photo_path = req.photo_path

    if req.capture_camera or not photo_path:
        cam = CameraManager()
        cap = cam.capture_photo()
        if not cap.get("success"):
            raise HTTPException(status_code=500, detail=f"Camera capture failed: {cap.get('error')}")
        photo_path = cap.get("image_path")

    res = user_manager.enroll_admin(
        display_name=req.display_name,
        pin=req.pin,
        photo_path=photo_path,
        confirmed=req.confirmed,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Enrollment failed"))

    # Set as active session
    permission_manager.set_active_user(res)
    return res


@identity_router.post("/verify_pin")
def verify_pin(req: PinVerificationRequest):
    """Verify administrator PIN with brute-force rate-limiting."""
    ok, msg = user_manager.verify_admin_pin(req.pin)
    if not ok:
        raise HTTPException(status_code=401, detail=msg)
    return {"success": True, "message": msg}


@identity_router.post("/identify")
def identify_face(req: IdentifyRequest):
    """
    Detect and identify face in front of the camera.
    Returns matched user or GUEST.
    """
    photo_path = req.photo_path
    if req.capture_camera or not photo_path:
        cam = CameraManager()
        cap = cam.capture_photo()
        if not cap.get("success"):
            raise HTTPException(status_code=500, detail=f"Camera capture failed: {cap.get('error')}")
        photo_path = cap.get("image_path")

    res = user_manager.identify_user_from_image(photo_path)
    res["photo_path"] = photo_path

    if res.get("identified"):
        permission_manager.set_active_user(res)
    else:
        permission_manager.set_active_user({
            "user_id": "guest_session",
            "display_name": "Guest",
            "role": UserRole.GUEST.value,
        })

    return res


@identity_router.get("/users")
def list_users():
    """List all registered users (passwords and face embeddings are strictly redacted)."""
    return {"users": user_manager.list_users()}


@identity_router.post("/users/enroll")
def enroll_user(req: UserEnrollmentRequest):
    """Enroll a secondary user (requires admin PIN authorization)."""
    photo_path = req.photo_path
    if req.capture_camera or not photo_path:
        cam = CameraManager()
        cap = cam.capture_photo()
        if not cap.get("success"):
            raise HTTPException(status_code=500, detail=f"Camera capture failed: {cap.get('error')}")
        photo_path = cap.get("image_path")

    res = user_manager.enroll_user(
        display_name=req.display_name,
        role=req.role,
        photo_path=photo_path,
        admin_pin=req.admin_pin,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@identity_router.delete("/users/{user_id}")
def delete_user(user_id: str, admin_pin: str = Query(...)):
    """Delete a user account (requires admin PIN authorization)."""
    res = user_manager.delete_user(user_id=user_id, admin_pin=admin_pin)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
