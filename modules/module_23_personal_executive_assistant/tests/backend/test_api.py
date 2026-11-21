"""FastAPI REST & WebSocket API tests for JARVIS Module 23."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_23_personal_executive_assistant.backend.app.config import ExecutiveAssistantConfig
from modules.module_23_personal_executive_assistant.backend.app.main import create_app


class TestExecutiveAssistantAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ExecutiveAssistantConfig(db_path=str(Path(self._tmp.name) / "api_m23.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.executive_assistant.db.close()
        self._tmp.cleanup()

    def test_health_manifest_and_ui(self) -> None:
        h = self.client.get("/api/v1/executive-assistant/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-23-personal-executive-assistant")

        m = self.client.get("/api/v1/executive-assistant/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["module_number"], 23)

        ui = self.client.get("/executive-assistant")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("PERSONAL EXECUTIVE ASSISTANT", ui.text)

    def test_end_to_end_executive_workflow_api(self) -> None:
        g = self.client.post("/api/v1/executive-assistant/goals", json={"title": "Q4 Delivery", "progress_pct": 20})
        self.assertEqual(g.status_code, 201)

        t = self.client.post(
            "/api/v1/executive-assistant/tasks",
            json={"title": "Review PR #42", "urgent": True, "important": True, "estimated_minutes": 30},
        )
        self.assertEqual(t.status_code, 201)
        self.assertEqual(t.json()["quadrant"], "do_first")

        plan = self.client.post("/api/v1/executive-assistant/plan-day", json={"date": "2026-11-20", "max_tasks": 3})
        self.assertEqual(plan.status_code, 200)
        self.assertEqual(plan.json()["scheduled_count"], 1)

        # Overlapping block returns 409
        conflict = self.client.post(
            "/api/v1/executive-assistant/time-blocks",
            json={"date": "2026-11-20", "start_time": "09:05", "end_time": "09:20", "title": "Clash"},
        )
        self.assertEqual(conflict.status_code, 409)

        # Habit + check-in
        hab = self.client.post("/api/v1/executive-assistant/habits", json={"name": "Morning Walk"})
        self.assertEqual(hab.status_code, 201)
        hid = hab.json()["habit_id"]
        chk = self.client.post(f"/api/v1/executive-assistant/habits/{hid}/checkin", json={"date": "2026-11-20"})
        self.assertEqual(chk.status_code, 200)
        self.assertEqual(chk.json()["current_streak"], 1)

        # Briefing
        br = self.client.get("/api/v1/executive-assistant/briefing?date=2026-11-20")
        self.assertEqual(br.status_code, 200)
        self.assertIn("Review PR #42", br.json()["executive_summary"])

    def test_websocket_connection(self) -> None:
        with self.client.websocket_connect("/api/v1/executive-assistant/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
