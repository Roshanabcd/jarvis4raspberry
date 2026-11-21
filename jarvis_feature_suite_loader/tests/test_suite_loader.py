"""End-to-end integration test mounting all 42 JARVIS feature modules in one FastAPI app."""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from jarvis_feature_suite_loader.app import create_app


class TestUnifiedSuiteLoader(unittest.TestCase):
    def test_mount_all_42_modules_and_verify_ui_and_health(self) -> None:
        client = TestClient(create_app())

        # 1. Check Launchpad UI
        ui = client.get("/suite")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS", ui.text)

        # 2. Check Suite Health API
        suite_health = client.get("/api/suite/health")
        self.assertEqual(suite_health.status_code, 200)
        body = suite_health.json()
        self.assertEqual(body["total_registered"], 43)
        self.assertEqual(body["mounted_count"], 43)
        self.assertEqual(body["operational_count"], 43)
        self.assertEqual(body["discovered_count"], 43)
        self.assertEqual(body["installed_count"], 43)

        # 3. Check every single module's health and UI endpoint
        for feat in body["features"]:
            self.assertEqual(feat["status"], "available", f"Failed to mount {feat['package']}: {feat.get('error')}")
            self.assertEqual(feat["operational_status"], "operational")
            h = client.get(feat["health_path"])
            self.assertEqual(h.status_code, 200, f"Health check failed for {feat['package']} at {feat['health_path']}")
            u = client.get(feat["ui_path"])
            self.assertEqual(u.status_code, 200, f"UI route failed for {feat['package']} at {feat['ui_path']}")

        # 4. Check Diagnostics API
        diag = client.get("/api/suite/diagnostics")
        self.assertEqual(diag.status_code, 200)
        diag_body = diag.json()
        self.assertEqual(diag_body["total_modules"], 43)
        self.assertIn("cpu_percent", diag_body)
        self.assertIn("ram_used_mb", diag_body)

        # 5. Check Module Toggle API
        toggle = client.post("/api/suite/modules/multi_agent_orchestrator/toggle")
        self.assertEqual(toggle.status_code, 200)
        self.assertEqual(toggle.json()["state"], "disabled")

        toggle_back = client.post("/api/suite/modules/multi_agent_orchestrator/toggle")
        self.assertEqual(toggle_back.status_code, 200)
        self.assertEqual(toggle_back.json()["state"], "enabled")


if __name__ == "__main__":
    unittest.main()
