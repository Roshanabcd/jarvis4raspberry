"""
JARVIS OS — Vision REST API.
Exposes endpoints for camera capture, YOLOv8n object detection, Moondream VLM scene
description, and visual question answering.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from apps.vision.service import vision_service
from tools.identity.permission_manager import permission_manager
from tools.vision.camera_manager import CameraManager

logger = logging.getLogger("JARVIS.API.Vision")

vision_router = APIRouter(prefix="/vision", tags=["vision"])


def _require_vision_permission(tool_name: str) -> None:
    """Enforce role-based access on vision hardware actions.

    Raises HTTP 403 when the active session lacks permission for the tool.
    Read-only telemetry (/vision/status) is intentionally left ungated.
    """
    allowed, reason = permission_manager.check_tool_permission(tool_name)
    if not allowed:
        logger.warning("Vision access denied for %s: %s", tool_name, reason)
        raise HTTPException(status_code=403, detail=reason)


class VisualQARequest(BaseModel):
    question: str = Field(..., min_length=2, description="Question about what the camera sees")
    image_path: Optional[str] = Field(None, description="Path to image (optional; uses camera if omitted)")


class ObjectDetectionRequest(BaseModel):
    image_path: Optional[str] = Field(None, description="Path to image (optional; uses camera if omitted)")
    conf_threshold: Optional[float] = Field(0.35, ge=0.1, le=0.95)


@vision_router.get("/status")
def get_camera_status():
    """Return truthful status of camera hardware, YOLOv8n detector, and Moondream VLM."""
    return vision_service.camera_status()


@vision_router.get("/capture")
@vision_router.post("/capture")
def capture_photo():
    """
    Capture a real photograph from the Sony IMX708 camera.
    Saves image into /home/roshan/Pictures/JARVIS_Photo_YYYYMMDD_HHMMSS.jpg.
    """
    _require_vision_permission("camera_capture")
    frame = vision_service.capture_frame()
    if frame.get("status") == "error":
        raise HTTPException(status_code=500, detail=frame.get("error", "Camera capture error"))
    filename = frame.get("filename") or (os.path.basename(frame["image_path"]) if frame.get("image_path") else None)
    return {
        "status": frame.get("status", "ok"),
        "success": frame.get("status", "ok") == "ok",
        "simulated": frame.get("simulated", False),
        "image_path": frame.get("image_path"),
        "filename": filename,
        "image_url": f"/api/vision/image/{filename}" if filename else None,
        "width": frame.get("width"),
        "height": frame.get("height"),
        "timestamp": frame.get("timestamp"),
        "camera_model": frame.get("camera_model", "Sony IMX708"),
        "data_b64": frame.get("data_b64"),
        "data": frame,
    }


@vision_router.get("/describe")
def describe_scene(image_path: Optional[str] = Query(None)):
    """Describe what is currently visible to the camera using local Moondream VLM."""
    _require_vision_permission("camera_describe")
    desc = vision_service.describe_scene(image_path=image_path)
    return {
        "description": desc,
        "image_path": image_path or vision_service._last_image_path,
        "model": vision_service.vlm.get_active_model(),
    }


@vision_router.post("/detect")
def detect_objects(req: Optional[ObjectDetectionRequest] = None):
    """
    Run YOLOv8n object detection on a captured image.
    Returns 80 COCO class labels, bounding box coordinates, confidence scores,
    and path to annotated visualization image.
    """
    _require_vision_permission("detect_objects")
    img_path = req.image_path if req else None
    conf = req.conf_threshold if req else 0.35

    res = vision_service.detect_objects(image_path=img_path)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("error", "Object detection error"))
    return res


@vision_router.post("/qa")
def visual_qa(req: VisualQARequest):
    """Answer a natural language question about what the camera sees."""
    _require_vision_permission("camera_describe")
    target_path = req.image_path or vision_service._last_image_path
    if not target_path or not os.path.exists(target_path):
        frame = vision_service.capture_frame()
        target_path = frame.get("image_path")

    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=500, detail="No camera image available for visual QA")

    qa_res = vision_service.vlm.visual_qa(target_path, req.question)
    return qa_res


@vision_router.get("/image/latest")
def get_latest_image():
    """Serve the latest captured photograph file directly as an image response."""
    img_path = vision_service._last_image_path
    if not img_path or not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="No captured image found")
    return FileResponse(img_path, media_type="image/jpeg")


@vision_router.get("/image/annotated")
def get_latest_annotated():
    """Serve the latest annotated object detection image."""
    img_path = vision_service._last_image_path
    if not img_path:
        raise HTTPException(status_code=404, detail="No captured image found")
    annotated_path = str(os.path.join(os.path.dirname(img_path), f"annotated_{os.path.basename(img_path)}"))
    if not os.path.exists(annotated_path):
        raise HTTPException(status_code=404, detail="No annotated image found")
    return FileResponse(annotated_path, media_type="image/jpeg")


@vision_router.get("/image/{filename}")
def get_image_by_filename(filename: str):
    """
    Securely serve captured photos from /home/roshan/Pictures.
    Strictly prevents directory traversal and restricts to allowed image extensions.
    """
    # 1. Reject path separators and dot-dot traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename: directory traversal prohibited")

    # 2. Strict extension check
    allowed_exts = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Invalid file type: only JPEG/PNG images are permitted")

    # 3. Path boundary verification
    safe_dir = Path("/home/roshan/Pictures").resolve()
    target_path = (safe_dir / filename).resolve()

    if not target_path.is_relative_to(safe_dir):
        raise HTTPException(status_code=403, detail="Access denied: path outside authorized directory")

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail=f"Image file '{filename}' not found")

    return FileResponse(str(target_path), media_type="image/jpeg")


@vision_router.get("/stream")
def get_camera_stream():
    """
    Proxies live MJPEG stream from dedicated camera service (127.0.0.1:8082/video_feed)
    to dashboard clients on port 8000, keeping port 8082 loopback-protected.
    """
    service_url = vision_service.camera_mgr.get_service_url()
    stream_url = f"{service_url}/video_feed"

    def iter_stream():
        try:
            with requests.get(stream_url, stream=True, timeout=10.0) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk
        except Exception as e:
            logger.debug("Camera stream proxy disconnected: %s", e)

    return StreamingResponse(
        iter_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"},
    )


@vision_router.get("/detections")
def get_live_detections():
    """Return live detections telemetry from dedicated camera service."""
    if not vision_service.camera_mgr.is_service_running():
        return {
            "status": "offline",
            "service_active": False,
            "targets": [],
            "message": "Camera service is offline on 127.0.0.1:8082",
        }
    svc_url = vision_service.camera_mgr.get_service_url()
    try:
        r = requests.get(f"{svc_url}/api/detections", timeout=1.0)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.warning("Failed to fetch live detections: %s", e)
    return {
        "status": "error",
        "service_active": False,
        "targets": [],
        "message": "Failed to query camera service detections",
    }
