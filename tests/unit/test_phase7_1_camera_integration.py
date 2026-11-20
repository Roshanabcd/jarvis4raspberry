"""
JARVIS OS — Phase 7.1 Automated Acceptance & Regression Test Suite:
Real Camera Integration, Object Detection Repair, and Vision Dashboard Stabilization.

Verifies:
1. Single Camera Ownership architecture: camera service at 127.0.0.1:8082 owns Sony IMX708.
2. Endpoint /api/health and /api/status returning truthful hardware telemetry.
3. Raw JPEG snapshot retrieval from /api/snapshot with valid JPEG magic bytes (\\xff\\xd8) and 1280x720 dimensions.
4. CameraManager capturing fresh frames from active camera service without launching conflicting processes.
5. JARVIS API POST /api/vision/capture saving to /home/roshan/Pictures/ with simulated=False.
6. Path traversal security on GET /api/vision/image/{filename}.
7. Optical distance telemetry labeled as "optical_monocular_estimate" with safety disclaimer.
8. Concurrent MJPEG streaming and snapshot capture without pipeline handler or device busy conflicts.
"""

import io
import os
import unittest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from apps.core.main import app
from tools.identity.permission_manager import permission_manager
from tools.identity.user_manager import UserRole
from tools.vision.camera_manager import CameraManager, PICTURES_DIR
from apps.vision.service import vision_service


class TestPhase71CameraIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.cam_mgr = CameraManager()
        cls._prev_active_user = permission_manager._current_user
        permission_manager.set_active_user({
            "user_id": "test_user",
            "display_name": "Test User",
            "role": UserRole.USER.value,
        })

    @classmethod
    def tearDownClass(cls):
        permission_manager._current_user = cls._prev_active_user

    def test_01_camera_service_health(self):
        """Camera service running on 127.0.0.1:8082 must return HTTP 200 with IMX708 info."""
        if not self.cam_mgr.is_service_running():
            self.skipTest("Camera service (127.0.0.1:8082) is not active in this test run.")

        status = self.cam_mgr.get_service_status()
        self.assertIsNotNone(status, "Service status must not be None when service is active")
        self.assertEqual(status.get("status"), "ok")
        self.assertEqual(status.get("backend"), "picamera2")
        self.assertIn("IMX708", status.get("camera", ""))
        self.assertIn("fps", status)

    def test_02_camera_service_snapshot_raw_jpeg(self):
        """Camera service /api/snapshot must return valid 1280x720 JPEG with correct magic bytes."""
        if not self.cam_mgr.is_service_running():
            self.skipTest("Camera service is not active.")

        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8082/api/snapshot")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            content_type = resp.headers.get("Content-Type", "")
            self.assertEqual(content_type, "image/jpeg")
            data = resp.read()

        # Check JPEG magic bytes
        self.assertTrue(data.startswith(b"\xff\xd8"), "Snapshot must start with JPEG SOI \\xff\\xd8")
        self.assertTrue(data.endswith(b"\xff\xd9"), "Snapshot must end with JPEG EOI \\xff\\xd9")
        self.assertGreater(len(data), 20000, "JPEG payload should be at least 20KB for 1280x720")

        # Verify dimensions using PIL
        img = Image.open(io.BytesIO(data))
        self.assertEqual(img.size, (1280, 720), "Snapshot must match IMX708 stream resolution 1280x720")

    def test_03_camera_manager_service_capture(self):
        """CameraManager.capture_photo() must consume from service without launching rpicam-still."""
        res = self.cam_mgr.capture_photo()
        self.assertTrue(res.get("success"), f"Capture failed: {res.get('error')}")
        self.assertFalse(res.get("simulated", True), "Capture must not be simulated")
        self.assertEqual(res.get("backend"), "camera_service_picamera2")

        image_path = res.get("image_path")
        self.assertTrue(os.path.exists(image_path), f"File {image_path} does not exist")
        self.assertTrue(image_path.startswith(str(PICTURES_DIR)))
        self.assertGreater(res.get("file_size_bytes", 0), 20000)

    def test_04_jarvis_api_vision_capture_endpoint(self):
        """POST /api/vision/capture must return simulated=False and a valid image_url."""
        resp = self.client.post("/api/vision/capture")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertFalse(data.get("simulated", True))
        self.assertIn("filename", data)
        self.assertIn("image_url", data)
        self.assertTrue(data["filename"].startswith("JARVIS_Photo_"))
        self.assertTrue(data["image_url"].startswith("/api/vision/image/"))

    def test_05_api_image_serving_and_traversal_security(self):
        """GET /api/vision/image/{filename} must serve saved pictures and block path traversal."""
        # 1. Capture an image to get a known valid filename
        cap_resp = self.client.post("/api/vision/capture")
        self.assertEqual(cap_resp.status_code, 200)
        valid_filename = cap_resp.json()["filename"]

        # 2. Test successful fetch
        resp = self.client.get(f"/api/vision/image/{valid_filename}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "image/jpeg")
        self.assertTrue(resp.content.startswith(b"\xff\xd8"))

        # 3. Path traversal attacks
        bad_paths = [
            "../../etc/passwd",
            "..%2f..%2fetc%2fpasswd",
            "../apps/core/main.py",
            "subdir/test.jpg",
            "/etc/shadow",
        ]
        for bad in bad_paths:
            bad_resp = self.client.get(f"/api/vision/image/{bad}")
            self.assertIn(
                bad_resp.status_code,
                [400, 404],
                f"Path traversal '{bad}' was not blocked (got {bad_resp.status_code})"
            )

        # 4. Disallowed file extensions
        disallowed = ["malicious.sh", "script.py", "config.json"]
        for dis in disallowed:
            dis_resp = self.client.get(f"/api/vision/image/{dis}")
            self.assertIn(dis_resp.status_code, [400, 404])

        # 5. Non-existent jpg
        not_found = self.client.get("/api/vision/image/JARVIS_Photo_nonexistent_999999.jpg")
        self.assertEqual(not_found.status_code, 404)

    def test_06_optical_distance_labeling_and_disclaimer(self):
        """Object detection results must label distance as optical monocular estimate with disclaimer."""
        resp = self.client.post("/api/vision/detect", json={})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))

        for obj in data.get("objects", []):
            self.assertIn("distance_m", obj)
            self.assertIn("distance_cm", obj)
            self.assertEqual(
                obj.get("distance_type"),
                "optical_monocular_estimate",
                "Distance type must explicitly state optical_monocular_estimate"
            )
            self.assertIn("optical_disclaimer", obj)
            self.assertIn("Not for safety-critical collision avoidance", obj["optical_disclaimer"])

    def test_07_concurrent_stream_and_capture_no_device_conflict(self):
        """Simultaneous stream reading and snapshot capture must succeed without resource busy error."""
        if not self.cam_mgr.is_service_running():
            self.skipTest("Camera service is not active.")

        import urllib.request

        # Open the MJPEG stream briefly (read first few chunks)
        req = urllib.request.Request("http://127.0.0.1:8082/video_feed")
        stream_conn = urllib.request.urlopen(req, timeout=5)
        initial_chunk = stream_conn.read(1024)
        self.assertTrue(len(initial_chunk) > 0, "MJPEG stream should provide immediate bytes")

        # Perform 3 consecutive captures while stream connection is open
        for _ in range(3):
            cap_res = self.cam_mgr.capture_photo()
            self.assertTrue(cap_res.get("success"), f"Concurrent capture failed: {cap_res.get('error')}")
            self.assertFalse(cap_res.get("simulated", True))

        # Close stream
        stream_conn.close()


if __name__ == "__main__":
    unittest.main()
