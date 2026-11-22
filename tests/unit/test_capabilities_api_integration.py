"""Integration tests for Capabilities REST API & Brain Integration."""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from apps.core.app_factory import create_app, noop_lifespan


class TestCapabilitiesApiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Create minimal test app with capabilities, chat, and voice routers
        specs = (
            ("apps.api.capabilities_api", "capabilities_router", "", ("capabilities",)),
            ("apps.api.chat_api", "chat_router", "/api", ("chat",)),
            ("apps.api.voice_api", "voice_router", "/api", ("voice",)),
        )
        cls.app = create_app(router_specs=specs, lifespan_context=noop_lifespan, include_dashboard=False)
        cls.client = TestClient(cls.app)

    def test_list_capabilities_endpoint(self) -> None:
        """GET /api/capabilities returns total >= 45 and capability list."""
        res = self.client.get("/api/capabilities")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertGreaterEqual(data["total"], 45)

    def test_get_capability_detail_endpoint(self) -> None:
        """GET /api/capabilities/{id} returns details for specific capability."""
        res = self.client.get("/api/capabilities/youtube-summarizer")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["capability"]["id"], "youtube-summarizer")

    def test_route_endpoint(self) -> None:
        """POST /api/capabilities/route returns match for natural language prompt."""
        res = self.client.post("/api/capabilities/route", json={
            "prompt": "Ask Claude to diagnose the repository",
            "role": "USER",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "matched")
        self.assertEqual(data["match"]["capability_id"], "developer-cli:claude")

    def test_invoke_endpoint(self) -> None:
        """POST /api/capabilities/invoke executes capability."""
        res = self.client.post("/api/capabilities/invoke", json={
            "capability_id": "system-telemetry",
            "action_id": "get_status",
            "role": "USER",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("System Telemetry", data["markdown_output"])

    def test_multi_task_endpoint(self) -> None:
        """POST /api/capabilities/multi-task executes compound request."""
        res = self.client.post("/api/capabilities/multi-task", json={
            "prompt": "Check system telemetry and find free calendar slots",
            "role": "USER",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("JARVIS Multi-Task Execution Report", data["final_summary"])

    def test_chat_endpoint_triggers_capability(self) -> None:
        """POST /api/chat seamlessly triggers capability without card opening."""
        res = self.client.post("/api/chat", json={
            "message": "Search documents for company travel refund policy",
            "use_tools": True,
            "role": "USER",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Document QA", data["response"])
        self.assertEqual(data["provider"], "capability_router")

    def test_chat_endpoint_triggers_multi_task(self) -> None:
        """POST /api/chat triggers MultiTaskBrain for compound request."""
        res = self.client.post("/api/chat", json={
            "message": "Check system telemetry and find free calendar slots",
            "use_tools": True,
            "role": "USER",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("JARVIS Multi-Task Execution Report", data["response"])
        self.assertEqual(data["provider"], "multi_task_brain")


if __name__ == "__main__":
    unittest.main()
