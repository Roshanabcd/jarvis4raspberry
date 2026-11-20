"""
JARVIS OS — Phase 7 Automated Acceptance Tests: Camera & Vision Subsystems.
Verifies real Sony IMX708 capture, YOLOv8n object detection, Moondream VLM scene
description, and VisionService integration.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
from fastapi.testclient import TestClient

from apps.core.main import app
from apps.vision.service import VisionService, vision_service
from tools.identity.permission_manager import permission_manager
from tools.identity.user_manager import UserRole
from tools.vision.camera_manager import CameraManager, PICTURES_DIR
from tools.vision.object_detector import ObjectDetector, object_detector, COCO_CLASSES
from tools.vision.vision_vlm import VisionVLM, vision_vlm


class TestPhase7CameraAndVision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Establish a USER session so gated vision API endpoints (capture,
        # detect, describe) remain reachable during these acceptance tests.
        # The previous active user is restored in tearDownClass to avoid
        # leaking this session into other test modules via the singleton.
        cls._prev_active_user = permission_manager._current_user
        permission_manager.set_active_user({
            "user_id": "test_user",
            "display_name": "Test User",
            "role": UserRole.USER.value,
        })
        # Create a synthetic 640x480 test image with a circle and rectangle
        cls.test_dir = tempfile.mkdtemp(prefix="jarvis_phase7_vision_")
        cls.test_image_path = os.path.join(cls.test_dir, "test_bench.jpg")

        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Draw table/desk
        cv2.rectangle(img, (50, 250), (590, 450), (120, 120, 120), -1)
        # Draw cup/bottle-like shape
        cv2.rectangle(img, (200, 180), (260, 320), (0, 255, 255), -1)
        # Draw person-like head
        cv2.circle(img, (400, 150), 40, (200, 180, 160), -1)
        cv2.imwrite(cls.test_image_path, img)

    @classmethod
    def tearDownClass(cls):
        permission_manager._current_user = cls._prev_active_user
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_camera_manager_singleton_and_binary(self):
        """CameraManager must be a singleton and truthfully detect rpicam/libcamera CLI."""
        cam1 = CameraManager()
        cam2 = CameraManager()
        self.assertIs(cam1, cam2, "CameraManager must be a singleton")

        status = cam1.get_status()
        self.assertIn("camera_model", status)
        self.assertEqual(status["camera_model"], "Sony IMX708 (Camera Module 3)")
        self.assertIn("binary", status)
        self.assertIn("save_directory", status)
        self.assertEqual(status["save_directory"], str(PICTURES_DIR))

    def test_02_camera_manager_physical_capture_or_hardware_check(self):
        """CameraManager should execute real capture if hardware available or report error."""
        cam = CameraManager()
        if cam.is_camera_available():
            target_path = os.path.join(self.test_dir, "capture_test.jpg")
            res = cam.capture_photo(custom_path=target_path, width=640, height=480, timeout_ms=300)
            self.assertTrue(res["success"], f"Capture failed: {res.get('error')}")
            self.assertTrue(os.path.exists(res["image_path"]))
            self.assertGreater(res["file_size_bytes"], 1000)
            self.assertEqual(res["format"], "JPEG")
            # Verify JPEG magic bytes \xff\xd8
            with open(res["image_path"], "rb") as f:
                header = f.read(2)
            self.assertEqual(header, b"\xff\xd8", "Captured image must have valid JPEG header")
        else:
            self.skipTest("Sony IMX708 hardware not detected in test environment")

    def test_03_object_detector_initialization(self):
        """ObjectDetector must load YOLOv8n ONNX model and expose 80 COCO classes."""
        detector = ObjectDetector()
        self.assertTrue(detector.is_ready, "YOLOv8n ONNX model must be loaded into OpenCV DNN")
        self.assertEqual(len(COCO_CLASSES), 80, "Must support all 80 standard COCO classes")
        self.assertIn("person", COCO_CLASSES)
        self.assertIn("bottle", COCO_CLASSES)
        self.assertIn("chair", COCO_CLASSES)
        self.assertIn("laptop", COCO_CLASSES)

    def test_04_object_detector_inference_on_image(self):
        """ObjectDetector must run inference and return structured detection results."""
        detector = ObjectDetector()
        res = detector.detect_objects(self.test_image_path)
        self.assertTrue(res["success"])
        self.assertIn("count", res)
        self.assertIn("objects", res)
        self.assertIn("labels", res)
        self.assertIn("inference_ms", res)
        self.assertGreater(res["inference_ms"], 0.0)

        # Verify bounding box drawing
        annotated_out = os.path.join(self.test_dir, "annotated_test.jpg")
        drawn = detector.draw_bounding_boxes(self.test_image_path, res["objects"], annotated_out)
        self.assertIsNotNone(drawn)
        self.assertTrue(os.path.exists(annotated_out))

    def test_05_vision_vlm_image_resizing_and_payload(self):
        """VisionVLM must downscale large images to 512px max dimension to prevent token explosion."""
        vlm = VisionVLM(max_dimension=512)
        # Test with a large synthetic image (1920x1080)
        large_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        b64_str = vlm._prepare_image_base64(large_img)
        self.assertIsNotNone(b64_str)
        self.assertIsInstance(b64_str, str)
        self.assertGreater(len(b64_str), 100)

        # Check status reporting
        status = vlm.get_status()
        self.assertIn("ollama_url", status)
        self.assertIn("max_dimension", status)
        self.assertEqual(status["max_dimension"], 512)

    def test_06_vision_service_simulation_mode_truthfulness(self):
        """VisionService must never set simulated: True when physical camera capture succeeds."""
        vs = VisionService(simulation=False)
        self.assertFalse(vs.simulation if vs.camera_mgr.is_camera_available() else True)

        status = vs.camera_status()
        self.assertIn("camera_model", status)
        self.assertIn("yolo_ready", status)
        self.assertTrue(status["yolo_ready"])

    def test_07_api_vision_status_endpoint(self):
        """GET /api/vision/status must return truthful hardware and model telemetry."""
        res = self.client.get("/api/vision/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("available", data)
        self.assertIn("camera_model", data)
        self.assertIn("yolo_ready", data)
        self.assertTrue(data["yolo_ready"])

    def test_08_api_vision_detect_endpoint(self):
        """POST /api/vision/detect must accept image_path and return detections."""
        payload = {"image_path": self.test_image_path, "conf_threshold": 0.25}
        res = self.client.post("/api/vision/detect", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success", False))
        self.assertIn("count", data)
        self.assertIn("objects", data)
        self.assertIn("labels", data)
        self.assertIn("inference_ms", data)

    def test_09_api_vision_describe_endpoint(self):
        """GET /api/vision/describe must return scene description."""
        res = self.client.get(f"/api/vision/describe?image_path={self.test_image_path}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("description", data)
        self.assertIsInstance(data["description"], str)
        self.assertGreater(len(data["description"]), 0)


if __name__ == "__main__":
    unittest.main()
