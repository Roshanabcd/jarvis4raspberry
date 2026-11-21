"""FastAPI REST & streaming WebSocket API tests for Module 20."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from modules.module_20_realtime_conversational_ai.backend.app.config import ConversationalConfig
from modules.module_20_realtime_conversational_ai.backend.app.main import create_app


class TestConversationalAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.app = create_app(ConversationalConfig(db_path=str(Path(self._tmp.name) / "api20.db")))
        self.ctx = TestClient(self.app)
        self.client = self.ctx.__enter__()

    def tearDown(self) -> None:
        self.ctx.__exit__(None, None, None)
        self._tmp.cleanup()

    def test_health_manifest_personas_and_ui(self) -> None:
        h = self.client.get("/api/v1/conversational-ai/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["lip_sync_mode"], "approximate_syllable_viseme")
        self.assertEqual(self.client.get("/api/v1/conversational-ai/manifest").json()["module_number"], 20)
        self.assertEqual(len(self.client.get("/api/v1/conversational-ai/personas").json()["personas"]), 2)
        ui = self.client.get("/conversational-ai")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("ARIA", ui.text)
        self.assertIn("ATLAS", ui.text)

    def test_rest_chat_sessions_and_streaming_websocket(self) -> None:
        s = self.client.post("/api/v1/conversational-ai/sessions", json={"title": "Voice Test", "persona": "atlas"})
        self.assertEqual(s.status_code, 201)
        sid = s.json()["session_id"]

        r = self.client.post("/api/v1/conversational-ai/chat", json={"session_id": sid, "content": "Hello ATLAS", "persona": "atlas"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("ATLAS", r.json()["assistant_message"]["content"])

        with self.client.websocket_connect("/api/v1/conversational-ai/ws/chat") as ws:
            hello = ws.receive_json()
            self.assertEqual(hello["event"], "ws.connected")
            ws.send_json({"type": "chat", "session_id": sid, "content": "Status check", "persona": "aria"})
            got_completed = False
            for _ in range(120):
                evt = ws.receive_json()
                if evt.get("event") == "turn.completed":
                    got_completed = True
                    break
            self.assertTrue(got_completed)


if __name__ == "__main__":
    unittest.main()
