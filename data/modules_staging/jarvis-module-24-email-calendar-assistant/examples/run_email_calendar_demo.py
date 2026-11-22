"""Runnable CLI demonstration for JARVIS Module 24 — Email & Calendar Assistant."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import EmailCalendarConfig
from backend.services.email_calendar_engine import EmailCalendarEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = EmailCalendarConfig(db_path=str(Path(tmp) / "demo_mail_cal.db"))
        engine = EmailCalendarEngine(cfg)

        emails = engine.db.list_emails()
        print(f"1. Triaged inbox loaded: {len(emails)} email(s). Top email: [{emails[0]['category']}] {emails[0]['subject']}")

        print("2. Drafting reply & queuing human send approval...")
        draft = engine.draft_reply(emails[0]["email_id"], tone="concise", extra_notes="Checksum verified.")
        gated = engine.request_send_draft(draft["draft_id"])
        print(f"   Send status: {gated['status']} | Approval ID: {gated['approval']['approval_id']}")

        print("3. Approving outbound email dispatch...")
        dec = engine.decide_send_approval(gated["approval"]["approval_id"], approved=True, decided_by="roshan")
        print(f"   Approval: {dec['approval']['status']} | Simulated delivery ID: {dec['delivery']['message_id']}")

        print("4. Scheduling meeting, finding free slots & exporting RFC 5545 .ics...")
        engine.create_event({"title": "JARVIS Sync", "date": "2026-11-21", "start_time": "10:00", "end_time": "11:00", "location": "Lab"})
        slots = engine.find_free_slots("2026-11-21", duration_minutes=60)
        ics = engine.export_ics("2026-11-21")
        print(f"   Free 60m slots found: {len(slots['free_slots'])} | ICS length: {len(ics)} bytes")
        engine.db.close()
        print("Demo complete.")


if __name__ == "__main__":
    main()
