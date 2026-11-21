"""Unit tests for JARVIS Module 24 — EmailCalendarEngine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.config import EmailCalendarConfig
from backend.services.email_calendar_engine import EmailCalendarEngine, EmailCalendarError, triage_email


class TestEmailCalendarEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg = EmailCalendarConfig(db_path=str(Path(self._tmp.name) / "test_m24.db"))
        self.engine = EmailCalendarEngine(self.cfg)

    def tearDown(self) -> None:
        self.engine.db.close()
        self._tmp.cleanup()

    def test_email_triage_categories(self) -> None:
        self.assertEqual(triage_email("URGENT server outage", "Fix ASAP")[0], "urgent")
        self.assertEqual(triage_email("Meeting invite", "Zoom sync at 3pm")[0], "meeting_invite")
        self.assertEqual(triage_email("Weekly Digest", "Click to unsubscribe")[0], "newsletter")
        self.assertEqual(triage_email("Q4 Contract", "Please review and approve")[0], "action_required")

    def test_draft_reply_and_human_send_approval_gate(self) -> None:
        emails = self.engine.db.list_emails()
        self.assertGreaterEqual(len(emails), 3)

        draft = self.engine.draft_reply(emails[0]["email_id"], tone="concise")
        gated = self.engine.request_send_draft(draft["draft_id"])
        self.assertEqual(gated["status"], "awaiting_approval")

        # Approve and verify simulated dispatch
        dec = self.engine.decide_send_approval(gated["approval"]["approval_id"], approved=True, decided_by="roshan")
        self.assertEqual(dec["approval"]["status"], "approved")
        self.assertTrue(dec["delivery"]["simulated"])
        self.assertEqual(self.engine.db.get_draft(draft["draft_id"])["status"], "sent")

    def test_rejected_send_approval_blocks_delivery(self) -> None:
        draft = self.engine.create_draft({"to_address": "a@jarvis.local", "subject": "Test", "body": "Body"})
        gated = self.engine.request_send_draft(draft["draft_id"])
        dec = self.engine.decide_send_approval(gated["approval"]["approval_id"], approved=False, decided_by="roshan")
        self.assertEqual(dec["approval"]["status"], "rejected")
        self.assertIsNone(dec["delivery"])
        self.assertEqual(self.engine.db.get_draft(draft["draft_id"])["status"], "rejected")

    def test_calendar_conflict_free_slots_and_ics_export(self) -> None:
        self.engine.create_event({"title": "Design Sync", "date": "2026-11-21", "start_time": "10:00", "end_time": "11:00"})
        with self.assertRaises(EmailCalendarError) as ctx:
            self.engine.create_event({"title": "Overlap", "date": "2026-11-21", "start_time": "10:30", "end_time": "11:30"})
        self.assertEqual(ctx.exception.status_code, 409)

        slots = self.engine.find_free_slots("2026-11-21", duration_minutes=60)
        self.assertEqual(len(slots["free_slots"]), 2)
        self.assertEqual(slots["free_slots"][0]["start_time"], "09:00")
        self.assertEqual(slots["free_slots"][0]["end_time"], "10:00")

        ics = self.engine.export_ics("2026-11-21")
        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("SUMMARY:Design Sync", ics)
        self.assertIn("END:VCALENDAR", ics)


if __name__ == "__main__":
    unittest.main()
