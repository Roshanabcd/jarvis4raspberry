"""End-to-end tests for JARVIS Real-Time Object Detection, tracking, ROI zones, and WebSocket streaming."""

from __future__ import annotations

import base64
import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from jarvis_object_detection.app import create_app
from jarvis_object_detection.config import ObjectDetectionConfig


def _make_frame_with_box(x1: int, y1: int, x2: int, y2: int) -> str:
    """Create a 320x240 light frame containing a distinct dark rectangular object."""
    img = Image.new("RGB", (320, 240), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([x1, y1, x2, y2], fill=(20, 25, 35))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


class TestObjectDetection(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_objdet.db"
        cfg = ObjectDetectionConfig(db_path=db_path, enable_yolo=False)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/object-detection")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Real-Time Object Detection", ui.text)

        health = self.client.get("/api/object-detection/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

    def test_detection_tracking_velocity_and_zone_alert(self) -> None:
        # Define ROI intrusion zone covering center of frame
        z = self.client.post(
            "/api/object-detection/zones",
            json={"name": "Center Lab Zone", "x1": 0.25, "y1": 0.20, "x2": 0.80, "y2": 0.85},
        )
        self.assertEqual(z.status_code, 200)

        # Frame 1: object centered around x=0.40
        f1 = self.client.post(
            "/api/object-detection/detect",
            json={"image_base64": _make_frame_with_box(95, 70, 160, 160), "stream_id": "cam_1"},
        )
        self.assertEqual(f1.status_code, 200)
        d1 = f1.json()
        self.assertGreaterEqual(d1["object_count"], 1)
        tid1 = d1["detections"][0]["track_id"]
        self.assertIn("Center Lab Zone", d1["detections"][0]["in_zones"])
        self.assertGreaterEqual(len(d1["triggered_alerts"]), 1)

        # Frame 2: object moves slightly right -> should keep same track_id with positive velocity_x
        f2 = self.client.post(
            "/api/object-detection/detect",
            json={"image_base64": _make_frame_with_box(115, 70, 180, 160), "stream_id": "cam_1"},
        )
        self.assertEqual(f2.status_code, 200)
        d2 = f2.json()
        self.assertEqual(d2["detections"][0]["track_id"], tid1)
        self.assertGreater(d2["detections"][0]["velocity_x"], 0.0)

        # Analytics updated
        an = self.client.get("/api/object-detection/analytics")
        self.assertEqual(an.status_code, 200)
        self.assertEqual(an.json()["total_frames_processed"], 2)

    def test_websocket_live_stream(self) -> None:
        with self.client.websocket_connect("/api/object-detection/ws/stream") as ws:
            conn = ws.receive_json()
            self.assertEqual(conn["event"], "connected")

            ws.send_json({"image_base64": _make_frame_with_box(80, 60, 160, 150), "stream_id": "ws_cam"})
            reply = ws.receive_json()
            self.assertGreaterEqual(reply["object_count"], 1)
            self.assertGreater(reply["estimated_fps"], 0.0)


if __name__ == "__main__":
    unittest.main()
