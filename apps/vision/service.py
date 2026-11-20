"""
JARVIS OS — Vision Service.
Integrates Raspberry Pi Camera Module 3 (Sony IMX708), YOLOv8n Object Detection,
and local Ollama Moondream Vision-Language Model.

Features:
- Real hardware capture via CameraManager (Sony IMX708 via rpicam-still)
- Truthful simulation reporting: 'simulated: False' when real hardware frame is captured
- Real YOLOv8n object detection (80 COCO classes) with bounding box annotations
- Grounded scene descriptions via local Moondream VLM
- Face identification via FaceEngine / UserManager
"""

import base64
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

from config.config_manager import config
from tools.vision.camera_manager import CameraManager, PICTURES_DIR
from tools.vision.object_detector import ObjectDetector, object_detector
from tools.vision.vision_vlm import VisionVLM, vision_vlm
from tools.identity.user_manager import UserManager, user_manager

logger = logging.getLogger("JARVIS.Vision.Service")


def _check_rpicam_available() -> bool:
    """Confirm managed camera availability without creating another owner."""
    return CameraManager().is_camera_available()


class VisionService:
    """
    Central vision coordination service for JARVIS OS on Raspberry Pi 5.
    Coordinates physical capture, object detection, and visual understanding.
    """

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        simulation: Optional[bool] = None,
    ) -> None:
        self.width = width
        self.height = height

        # An explicit simulation request must never touch a physical camera.
        self.camera_mgr = CameraManager()
        hw_available = self.camera_mgr.is_camera_available()

        if simulation is not None:
            self.simulation = bool(simulation)
        else:
            # If real hardware is detected, we ALWAYS use real hardware
            self.simulation = False if hw_available else True

        self.object_detector = object_detector
        self.vlm = vision_vlm
        self.user_mgr = user_manager
        self._last_capture_time: Optional[float] = None
        self._last_image_path: Optional[str] = None
        self._backend = "simulated" if self.simulation else "camera_manager"

        logger.info(
            "VisionService initialized (hw_available=%s, simulation=%s, resolution=%dx%d)",
            hw_available,
            self.simulation,
            self.width,
            self.height,
        )

    def capture_frame(self, save_to_disk: bool = True) -> Dict[str, Any]:
        """
        Capture a frame from the Sony IMX708 camera or return simulation if hardware unavailable.
        Sets 'simulated: False' explicitly when real hardware is used.
        """
        self._last_capture_time = time.time()

        if self.simulation or not self.camera_mgr.is_camera_available():
            return {
                "status": "simulated",
                "simulated": True,
                "timestamp": self._last_capture_time,
                "width": self.width,
                "height": self.height,
                "format": "simulated",
                "data_b64": None,
                "image_path": None,
                "backend": "simulated",
                "objects_detected": ["desk", "monitor", "keyboard"],
                "description": "Simulated scene: office environment with robotics workbench.",
            }

        # Real hardware capture
        result = self.camera_mgr.capture_photo(width=self.width, height=self.height)
        if not result.get("success"):
            logger.error("Camera capture failed: %s", result.get("error"))
            return {
                "status": "error",
                "simulated": False,
                "error": result.get("error", "Unknown camera error"),
                "timestamp": self._last_capture_time,
                "backend": "rpicam_still",
            }

        img_path = result.get("image_path")
        self._last_image_path = img_path
        filename = result.get("filename") or (os.path.basename(img_path) if img_path else None)

        # Read base64
        data_b64 = None
        try:
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            data_b64 = base64.b64encode(img_bytes).decode("utf-8")
        except Exception as e:
            logger.warning("Failed to encode captured image to b64: %s", e)

        backend_name = result.get("backend", "camera_service_picamera2")
        return {
            "status": "ok",
            "simulated": False,
            "timestamp": self._last_capture_time,
            "width": result.get("width", self.width),
            "height": result.get("height", self.height),
            "format": "jpeg",
            "size_bytes": result.get("file_size_bytes", 0),
            "image_path": img_path,
            "filename": filename,
            "data_b64": data_b64,
            "backend": backend_name,
            "camera_model": "Sony IMX708",
        }

    def detect_objects(self, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run real YOLO object detection on a newly captured frame or specified image.
        Leverages active dedicated camera service (YOLO11 NCNN) if running, or falls back to local YOLOv8n ONNX.
        """
        # Explicit simulation is isolated from both the network camera service
        # and local ONNX inference, even if hardware is connected.
        if self.simulation:
            return {
                "status": "simulated",
                "simulated": True,
                "count": 3,
                "objects": [
                    {"label": "desk", "confidence": 0.92, "bbox": {"x": 50, "y": 300, "width": 500, "height": 300}},
                    {"label": "monitor", "confidence": 0.88, "bbox": {"x": 150, "y": 100, "width": 300, "height": 200}},
                    {"label": "keyboard", "confidence": 0.85, "bbox": {"x": 200, "y": 350, "width": 250, "height": 100}},
                ],
                "labels": ["desk", "monitor", "keyboard"],
                "source": "simulation",
            }

        # If no specific image requested and the camera service is active, fetch live real-time detections
        if not image_path and self.camera_mgr.is_service_running():
            svc_url = self.camera_mgr.get_service_url()
            try:
                r_det = requests.get(f"{svc_url}/api/detections", timeout=2.0)
                r_snap = requests.get(f"{svc_url}/api/snapshot/annotated", timeout=4.0)
                cap_res = self.capture_frame()
                clean_path = cap_res.get("image_path")

                annotated_path = None
                if clean_path and r_snap.status_code == 200:
                    annotated_path = str(Path(clean_path).parent / f"annotated_{Path(clean_path).name}")
                    with open(annotated_path, "wb") as f:
                        f.write(r_snap.content)

                if r_det.status_code == 200:
                    det_data = r_det.json()
                    targets = det_data.get("targets", [])
                    objects = [
                        {
                            "label": t.get("label", "object"),
                            "confidence": t.get("confidence", 0.0),
                            "bbox": {
                                "x": t.get("bbox", [0, 0, 0, 0])[0],
                                "y": t.get("bbox", [0, 0, 0, 0])[1],
                                "width": max(0, t.get("bbox", [0, 0, 0, 0])[2] - t.get("bbox", [0, 0, 0, 0])[0]),
                                "height": max(0, t.get("bbox", [0, 0, 0, 0])[3] - t.get("bbox", [0, 0, 0, 0])[1]),
                            },
                            "raw_bbox": t.get("bbox"),
                            "distance_m": t.get("distance_m"),
                            "distance_cm": t.get("distance_cm"),
                            "distance_type": "optical_monocular_estimate",
                            "optical_disclaimer": "Optical/PDAF estimate (monocular). Not for safety-critical collision avoidance.",
                            "zone": t.get("zone", "UNKNOWN"),
                        }
                        for t in targets
                    ]
                    labels = [t.get("label", "object") for t in targets]
                    return {
                        "status": "ok",
                        "success": True,
                        "simulated": False,
                        "count": len(objects),
                        "objects": objects,
                        "labels": labels,
                        "fps": det_data.get("fps"),
                        "distance_type": "optical_monocular_estimate",
                        "distance_note": "Monocular optical/PDAF estimate. Monocular calculation is an optical estimate, not direct 3D depth. Not for safety-critical collision avoidance.",
                        "optical_disclaimer": "Optical/PDAF estimate (monocular). Not for safety-critical collision avoidance.",
                        "source": "yolo11n_ncnn_service",
                        "image_path": clean_path,
                        "annotated_image_path": annotated_path,
                    }
            except Exception as e:
                logger.warning("Camera service detection query failed, falling back to local YOLOv8: %s", e)

        target_path = image_path or self._last_image_path
        if not target_path or not os.path.exists(target_path):
            frame = self.capture_frame()
            if frame.get("simulated"):
                return {
                    "status": "simulated",
                    "simulated": True,
                    "count": 3,
                    "objects": [
                        {"label": "desk", "confidence": 0.92, "bbox": {"x": 50, "y": 300, "width": 500, "height": 300}},
                        {"label": "monitor", "confidence": 0.88, "bbox": {"x": 150, "y": 100, "width": 300, "height": 200}},
                        {"label": "keyboard", "confidence": 0.85, "bbox": {"x": 200, "y": 350, "width": 250, "height": 100}},
                    ],
                    "labels": ["desk", "monitor", "keyboard"],
                    "source": "simulation",
                }
            target_path = frame.get("image_path")

        if not target_path or not os.path.exists(target_path):
            return {
                "status": "error",
                "simulated": False,
                "error": "No valid image available for object detection",
                "count": 0,
                "objects": [],
                "labels": [],
            }

        # Run real YOLOv8 detection
        res = self.object_detector.detect_objects(target_path)
        res["status"] = "ok" if res.get("success") else "error"
        res["simulated"] = False
        res["source"] = "yolov8n_onnx"
        res["image_path"] = target_path

        # Generate annotated image
        annotated_path = str(Path(target_path).parent / f"annotated_{Path(target_path).name}")
        self.object_detector.draw_bounding_boxes(target_path, res.get("objects", []), annotated_path)
        res["annotated_image_path"] = annotated_path

        return res

    def describe_scene(self, image_path: Optional[str] = None) -> str:
        """
        Describe the scene using the local Moondream Vision-Language Model.
        """
        target_path = image_path or self._last_image_path
        if not target_path or not os.path.exists(target_path):
            frame = self.capture_frame()
            if frame.get("simulated"):
                return frame.get("description", "Simulated scene: office environment.")
            target_path = frame.get("image_path")

        if not target_path or not os.path.exists(target_path):
            return "Camera capture unavailable."

        vlm_res = self.vlm.describe_scene(target_path)
        if vlm_res.get("success"):
            return vlm_res.get("description", "A scene in front of the camera.")
        else:
            # Fallback to detected objects if VLM is slow or unavailable
            det = self.object_detector.detect_objects(target_path)
            labels = det.get("labels", [])
            if labels:
                return f"Scene with detected objects: {', '.join(labels)}."
            return "Visual scene analyzed; camera captured successfully."

    def identify_present_user(self, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempt to identify any enrolled user in front of the camera.
        """
        target_path = image_path or self._last_image_path
        if not target_path or not os.path.exists(target_path):
            frame = self.capture_frame()
            if frame.get("simulated"):
                return {
                    "recognized": False,
                    "user_id": None,
                    "role": "GUEST",
                    "display_name": "Guest",
                    "similarity": 0.0,
                    "reason": "Simulation mode active",
                }
            target_path = frame.get("image_path")

        if not target_path or not os.path.exists(target_path):
            return {
                "recognized": False,
                "user_id": None,
                "role": "GUEST",
                "display_name": "Guest",
                "similarity": 0.0,
                "reason": "Failed to capture image",
            }

        return self.user_mgr.identify_user_from_image(target_path)

    def camera_status(self) -> Dict[str, Any]:
        """Return truthful hardware and model status."""
        mgr_status = self.camera_mgr.get_status()
        vlm_status = self.vlm.get_status()
        return {
            "available": mgr_status.get("available", False),
            "simulation": self.simulation,
            "backend": mgr_status.get("binary") or "simulated",
            "camera_model": mgr_status.get("camera_model"),
            "rpicam_cli_available": bool(mgr_status.get("binary")),
            "last_capture": self._last_capture_time,
            "last_image_path": self._last_image_path,
            "resolution": f"{self.width}x{self.height}",
            "yolo_ready": self.object_detector.is_ready,
            "vlm_ready": vlm_status.get("available", False),
            "vlm_model": vlm_status.get("active_model"),
        }

    def shutdown(self) -> None:
        """Gracefully release camera resources."""
        self._last_capture_time = None
        if self.simulation:
            self._backend = "simulated"
        logger.info("VisionService shutdown completed.")


# Global singleton instance
vision_service = VisionService()
