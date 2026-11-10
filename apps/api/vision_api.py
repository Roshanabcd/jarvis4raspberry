"""
JARVIS OS — Vision REST API.
Exposes endpoints for camera capture, YOLOv8n object detection, Moondream VLM scene
description, and visual question answering.
"""

import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from apps.vision.service import vision_service
from tools.vision.camera_manager import CameraManager

vision_router = APIRouter(prefix="/vision", tags=["vision"])


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
    frame = vision_service.capture_frame()
    if frame.get("status") == "error":
        raise HTTPException(status_code=500, detail=frame.get("error", "Camera capture error"))
    return {
        "status": frame.get("status", "ok"),
        "simulated": frame.get("simulated", False),
        "image_path": frame.get("image_path"),
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
    img_path = req.image_path if req else None
    conf = req.conf_threshold if req else 0.35

    res = vision_service.detect_objects(image_path=img_path)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("error", "Object detection error"))
    return res


@vision_router.post("/qa")
def visual_qa(req: VisualQARequest):
    """Answer a natural language question about what the camera sees."""
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
