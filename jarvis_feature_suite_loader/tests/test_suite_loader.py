"""End-to-end integration test mounting all 17 JARVIS feature modules in one FastAPI app."""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from jarvis_feature_suite_loader.app import create_app


class TestUnifiedSuiteLoader(unittest.TestCase):
    def test_mount_all_17_modules_and_verify_ui_and_health(self) -> None:
        client = TestClient(create_app())

        ui = client.get("/suite")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Unified Feature Suite Launchpad", ui.text)

        suite_health = client.get("/api/suite/health")
        self.assertEqual(suite_health.status_code, 200)
        body = suite_health.json()
        self.assertEqual(body["total_registered"], 17)
        self.assertEqual(body["mounted_count"], 17)

        for feat in body["features"]:
            self.assertEqual(feat["status"], "available", f"Failed to mount {feat['package']}: {feat['error']}")
            h = client.get(feat["health_path"])
            self.assertEqual(h.status_code, 200, f"Health check failed for {feat['package']}")
            u = client.get(feat["ui_path"])
            self.assertEqual(u.status_code, 200, f"UI route failed for {feat['package']}")


if __name__ == "__main__":
    unittest.main()
