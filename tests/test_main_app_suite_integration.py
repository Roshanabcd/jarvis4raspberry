"""End-to-end integration test verifying that the main JARVIS OS FastAPI factory mounts all 42 modules without regressions."""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from apps.core.app_factory import create_app, noop_lifespan


class TestMainAppSuiteIntegration(unittest.TestCase):
    def test_main_app_mounts_all_42_modules_and_preserves_core_routes(self) -> None:
        app = create_app(lifespan_context=noop_lifespan, include_dashboard=True)
        client = TestClient(app)

        # 1. Verify existing core health and root routes
        core_health = client.get("/api/health")
        self.assertEqual(core_health.status_code, 200, "Core API health check must pass")

        # 2. Verify Unified Feature Suite Launchpad route
        suite_ui = client.get("/suite")
        self.assertEqual(suite_ui.status_code, 200)
        self.assertIn("UNIFIED EXTENSION CENTER", suite_ui.text)

        # 3. Verify Suite Health API returns all 43 modules
        suite_health = client.get("/api/suite/health")
        self.assertEqual(suite_health.status_code, 200)
        body = suite_health.json()
        self.assertEqual(body["total_registered"], 43)
        self.assertEqual(body["mounted_count"], 43)
        self.assertEqual(body["operational_count"], 43)

        # 4. Verify original modules are active (e.g. Module 1 AI Coding Assistant)
        m1_health = client.get("/api/coding-assistant/health")
        self.assertEqual(m1_health.status_code, 200)

        # 5. Verify new extension modules are active (e.g. Module 18 Orchestrator, Module 42 Extension Manager, Module 43 Screen Guardian)
        m18_health = client.get("/api/v1/orchestrator/health")
        self.assertEqual(m18_health.status_code, 200)

        m40_health = client.get("/api/v1/approvals/health")
        self.assertEqual(m40_health.status_code, 200)

        m42_health = client.get("/api/v1/extensions/health")
        self.assertEqual(m42_health.status_code, 200)

        m43_health = client.get("/api/v1/screen-guardian/health")
        self.assertEqual(m43_health.status_code, 200)

        m43_ui = client.get("/screen-guardian")
        self.assertEqual(m43_ui.status_code, 200)


if __name__ == "__main__":
    unittest.main()
