"""FastAPI REST & WebSocket API tests for JARVIS Module 24."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import EmailCalendarConfig
from backend.app.main import create_app


class TestEmailCalendarAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = EmailCalendarConfig(db_path=str(Path(self._tmp.name) / "api_m24.db"))
        self.app = create_app(cfg)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.email_calendar.db.close()
        self._tmp.cleanup()

    def test_health_manifest_and_ui(self) -> None:
        h = self.client.get("/api/v1/email-calendar/health")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.json()["module_id"], "jarvis-module-24-email-calendar-assistant")
        self.assertTrue(h.json()["simulated"])

        m = self.client.get("/api/v1/email-calendar/manifest")
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["module_number"], 24)

        ui = self.client.get("/email-calendar")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("EMAIL &amp; CALENDAR ASSISTANT", ui.text)

    def test_email_send_gate_and_calendar_ics_api(self) -> None:
        em = self.client.post(
            "/api/v1/email-calendar/emails",
            json={"sender": "boss@jarvis.local", "subject": "URGENT approval", "body": "Please review ASAP."},
        )
        self.assertEqual(em.status_code, 201)
        eid = em.json()["email_id"]
        self.assertEqual(em.json()["category"], "urgent")

        dr = self.client.post(f"/api/v1/email-calendar/emails/{eid}/draft-reply", json={"tone": "concise"})
        self.assertEqual(dr.status_code, 201)
        did = dr.json()["draft_id"]

        snd = self.client.post(f"/api/v1/email-calendar/drafts/{did}/send")
        self.assertEqual(snd.status_code, 200)
        self.assertEqual(snd.json()["status"], "awaiting_approval")
        aid = snd.json()["approval"]["approval_id"]

        dec = self.client.post(
            f"/api/v1/email-calendar/approvals/{aid}/decide",
            json={"approved": True, "decided_by": "operator"},
        )
        self.assertEqual(dec.status_code, 200)
        self.assertEqual(dec.json()["approval"]["status"], "approved")

        ev = self.client.post(
            "/api/v1/email-calendar/calendar/events",
            json={"title": "Sprint Review", "date": "2026-11-22", "start_time": "14:00", "end_time": "15:00"},
        )
        self.assertEqual(ev.status_code, 201)

        ics = self.client.get("/api/v1/email-calendar/calendar/export.ics?date=2026-11-22")
        self.assertEqual(ics.status_code, 200)
        self.assertIn("SUMMARY:Sprint Review", ics.text)

    def test_websocket_connection(self) -> None:
        with self.client.websocket_connect("/api/v1/email-calendar/ws/events") as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["event_type"], "ws.connected")
            self.assertIn("status", msg)


if __name__ == "__main__":
    unittest.main()
