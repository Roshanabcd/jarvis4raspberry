"""REST & WebSocket API tests for JARVIS Module 25 — AI Meeting Assistant."""

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from modules.module_25_ai_meeting_assistant.backend.app.config import MeetingAssistantConfig
from modules.module_25_ai_meeting_assistant.backend.app.main import create_app


class TestMeetingAssistantAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = MeetingAssistantConfig(db_path=os.path.join(self._tmp.name, "api_m25.db"))
        self.app = create_app(config=cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_manifest_status_and_ui(self) -> None:
        r_health = self.client.get("/api/v1/meeting-assistant/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["module_id"], "jarvis-module-25-ai-meeting-assistant")
        self.assertTrue(r_health.json()["simulated"])

        r_manifest = self.client.get("/api/v1/meeting-assistant/manifest")
        self.assertEqual(r_manifest.status_code, 200)
        self.assertEqual(r_manifest.json()["version"], "1.0.0")

        r_ui = self.client.get("/meeting-assistant")
        self.assertEqual(r_ui.status_code, 200)
        self.assertIn("AI Meeting Assistant", r_ui.text)

    def test_full_meeting_rest_workflow(self) -> None:
        create_res = self.client.post(
            "/api/v1/meeting-assistant/meetings",
            json={
                "title": "Product Launch Sync",
                "meeting_date": "2026-11-20",
                "participants": ["Roshan", "Asha"],
                "agenda": "Finalize release checklist",
            },
        )
        self.assertEqual(create_res.status_code, 201)
        mtg_id = create_res.json()["meeting_id"]

        seg_res = self.client.post(
            f"/api/v1/meeting-assistant/meetings/{mtg_id}/transcript",
            json={"speaker": "Roshan", "text": "We approved the modular architecture.", "timestamp_sec": 10},
        )
        self.assertEqual(seg_res.status_code, 201)

        bulk_res = self.client.post(
            f"/api/v1/meeting-assistant/meetings/{mtg_id}/transcript/bulk",
            json={"raw_transcript": "Asha: Action: I will verify backups by EOD.\nRoshan: Watch out for network delay risk."},
        )
        self.assertEqual(bulk_res.status_code, 201)
        self.assertEqual(bulk_res.json()["ingested_count"], 2)

        an_res = self.client.post(f"/api/v1/meeting-assistant/meetings/{mtg_id}/analyze")
        self.assertEqual(an_res.status_code, 200)
        body = an_res.json()
        self.assertEqual(len(body["action_items"]), 1)
        item_id = body["action_items"][0]["item_id"]

        patch_res = self.client.patch(
            f"/api/v1/meeting-assistant/action-items/{item_id}",
            json={"status": "done"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "done")

        md_res = self.client.get(f"/api/v1/meeting-assistant/meetings/{mtg_id}/minutes.md")
        self.assertEqual(md_res.status_code, 200)
        self.assertIn("# Meeting Minutes: Product Launch Sync", md_res.text)

        search_res = self.client.get("/api/v1/meeting-assistant/search", params={"q": "backups"})
        self.assertEqual(search_res.status_code, 200)
        self.assertEqual(search_res.json()["count"], 1)

    def test_websocket_connects(self) -> None:
        with self.client.websocket_connect("/api/v1/meeting-assistant/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
