"""Email & Calendar Assistant Engine (Module 24).

Provides:
- Deterministic email triage (urgent, action_required, meeting_invite, newsletter, general)
- Draft reply generation & mandatory human approval gate before outbound send
- Overlap-checked calendar scheduling, RSVP management, free-slot finder & RFC 5545 ICS export
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from modules.module_24_email_calendar_assistant.backend.adapters.mail_calendar_adapter import MailCalendarAdapter, SimulatedMailCalendarAdapter
from modules.module_24_email_calendar_assistant.backend.app.config import EmailCalendarConfig
from modules.module_24_email_calendar_assistant.backend.models.database import EmailCalendarDB, utc_now_iso

SEED_EMAILS: List[Dict[str, str]] = [
    {
        "sender": "ops-alerts@jarvis.local",
        "recipient": "operator@jarvis.local",
        "subject": "URGENT: Raspberry Pi 5 Backup Verification Needed",
        "body": "Please review the nightly backup checksum before 5:00 PM today.",
    },
    {
        "sender": "team-lead@jarvis.local",
        "recipient": "operator@jarvis.local",
        "subject": "Meeting Invite: JARVIS OS Architecture Sync",
        "body": "Can we meet tomorrow at 10:00 AM to review Module 24 integration?",
    },
    {
        "sender": "digest@ai-weekly.local",
        "recipient": "operator@jarvis.local",
        "subject": "Weekly AI Newsletter — Unsubscribe anytime",
        "body": "Top open-source local models and benchmarks from this week.",
    },
]


class EmailCalendarError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def triage_email(subject: str, body: str) -> tuple[str, int]:
    text = f"{subject} {body}".lower()
    if any(k in text for k in ("urgent", "asap", "critical", "outage", "deadline")):
        return "urgent", 95
    if any(k in text for k in ("meeting", "invite", "calendar", "schedule", "zoom", "sync")):
        return "meeting_invite", 80
    if any(k in text for k in ("unsubscribe", "newsletter", "digest", "promo")):
        return "newsletter", 20
    if any(k in text for k in ("please review", "action required", "approve", "follow up", "confirm")):
        return "action_required", 75
    return "general", 50


def _hhmm_to_min(hhmm: str) -> int:
    try:
        h, m = [int(x) for x in hhmm.strip().split(":")]
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return h * 60 + m
    except Exception as exc:
        raise EmailCalendarError("INVALID_TIME", f"Invalid HH:MM time '{hhmm}'.", 422) from exc


def _min_to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class EmailCalendarEngine:
    def __init__(
        self,
        config: Optional[EmailCalendarConfig] = None,
        db: Optional[EmailCalendarDB] = None,
        adapter: Optional[MailCalendarAdapter] = None,
        seed_demo_inbox: bool = True,
    ) -> None:
        self.config = config or EmailCalendarConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or EmailCalendarDB(self.config.db_path)
        self.adapter = adapter or SimulatedMailCalendarAdapter()
        self._started_at = time.monotonic()

        if seed_demo_inbox and not self.db.list_emails(include_archived=True):
            for e in SEED_EMAILS:
                self.ingest_email(e)

    # --- Email Triage & Drafts ---
    def ingest_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cat, score = triage_email(payload["subject"], payload["body"])
        return self.db.insert_email(
            {
                "email_id": f"eml_{uuid.uuid4().hex[:10]}",
                "sender": payload["sender"],
                "recipient": payload.get("recipient", "operator@jarvis.local"),
                "subject": payload["subject"],
                "body": payload["body"],
                "category": cat,
                "priority_score": score,
                "is_read": False,
                "archived": False,
                "received_at": utc_now_iso(),
            }
        )

    def draft_reply(self, email_id: str, tone: str = "professional", extra_notes: str = "") -> Dict[str, Any]:
        email = self.db.get_email(email_id)
        if not email:
            raise EmailCalendarError("EMAIL_NOT_FOUND", f"Email '{email_id}' not found.", 404)
        subj = email["subject"] if email["subject"].lower().startswith("re:") else f"Re: {email['subject']}"
        body = self.adapter.generate_reply_body(email, tone=tone, extra_notes=extra_notes)
        return self.create_draft(
            {"to_address": email["sender"], "subject": subj, "body": body, "in_reply_to": email_id}
        )

    def create_draft(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        return self.db.create_draft(
            {
                "draft_id": f"drf_{uuid.uuid4().hex[:10]}",
                "to_address": payload["to_address"],
                "subject": payload["subject"],
                "body": payload["body"],
                "in_reply_to": payload.get("in_reply_to"),
                "status": "draft",
                "created_at": now,
                "updated_at": now,
            }
        )

    def request_send_draft(self, draft_id: str) -> Dict[str, Any]:
        draft = self.db.get_draft(draft_id)
        if not draft:
            raise EmailCalendarError("DRAFT_NOT_FOUND", f"Draft '{draft_id}' not found.", 404)
        if draft["status"] == "sent":
            raise EmailCalendarError("ALREADY_SENT", f"Draft '{draft_id}' was already sent.", 409)

        if self.config.require_approval_for_send:
            self.db.update_draft_status(draft_id, "awaiting_approval")
            apr = self.db.create_approval(
                {
                    "approval_id": f"eap_{uuid.uuid4().hex[:10]}",
                    "draft_id": draft_id,
                    "to_address": draft["to_address"],
                    "subject": draft["subject"],
                    "created_at": utc_now_iso(),
                }
            )
            return {"status": "awaiting_approval", "approval": apr}

        res = self.adapter.send_email(draft["to_address"], draft["subject"], draft["body"])
        self.db.update_draft_status(draft_id, "sent")
        return {"status": "sent", "delivery": res}

    def decide_send_approval(self, approval_id: str, approved: bool, decided_by: str = "operator", comment: str = "") -> Dict[str, Any]:
        apr = self.db.get_approval(approval_id)
        if not apr:
            raise EmailCalendarError("APPROVAL_NOT_FOUND", f"Approval '{approval_id}' not found.", 404)
        if apr["status"] != "pending":
            raise EmailCalendarError("APPROVAL_DECIDED", f"Approval '{approval_id}' already '{apr['status']}'.", 409)

        status = "approved" if approved else "rejected"
        decided = self.db.decide_approval(approval_id, status, decided_by, comment)
        delivery = None
        draft = self.db.get_draft(apr["draft_id"])
        if approved and draft:
            delivery = self.adapter.send_email(draft["to_address"], draft["subject"], draft["body"])
            self.db.update_draft_status(draft["draft_id"], "sent")
        elif draft:
            self.db.update_draft_status(draft["draft_id"], "rejected")
        return {"approval": decided, "delivery": delivery}

    # --- Calendar Events, Free Slots & ICS Export ---
    def create_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        start_m = _hhmm_to_min(payload["start_time"])
        end_m = _hhmm_to_min(payload["end_time"])
        if end_m <= start_m:
            raise EmailCalendarError("INVALID_RANGE", "end_time must be after start_time.", 422)

        if not payload.get("allow_overlap", False):
            for ev in self.db.list_events(date=payload["date"]):
                ev_s = _hhmm_to_min(ev["start_time"])
                ev_e = _hhmm_to_min(ev["end_time"])
                if start_m < ev_e and end_m > ev_s:
                    raise EmailCalendarError(
                        "CALENDAR_CONFLICT",
                        f"Event overlaps with '{ev['title']}' ({ev['start_time']}-{ev['end_time']}).",
                        409,
                        {"conflicting_event_id": ev["event_id"]},
                    )

        now = utc_now_iso()
        return self.db.create_event(
            {
                "event_id": f"evt_{uuid.uuid4().hex[:10]}",
                "title": payload["title"],
                "date": payload["date"],
                "start_time": _min_to_hhmm(start_m),
                "end_time": _min_to_hhmm(end_m),
                "location": payload.get("location", ""),
                "attendees": list(payload.get("attendees", [])),
                "description": payload.get("description", ""),
                "rsvp_status": "accepted",
                "created_at": now,
                "updated_at": now,
            }
        )

    def update_rsvp(self, event_id: str, rsvp_status: str) -> Dict[str, Any]:
        updated = self.db.update_event_rsvp(event_id, rsvp_status)
        if not updated:
            raise EmailCalendarError("EVENT_NOT_FOUND", f"Event '{event_id}' not found.", 404)
        return updated

    def find_free_slots(self, target_date: str, duration_minutes: int = 30) -> Dict[str, Any]:
        events = self.db.list_events(date=target_date)
        busy = sorted([(_hhmm_to_min(e["start_time"]), _hhmm_to_min(e["end_time"])) for e in events])
        day_start = self.config.workday_start_hour * 60
        day_end = self.config.workday_end_hour * 60

        slots: List[Dict[str, Any]] = []
        cursor = day_start
        for s, e in busy:
            if s - cursor >= duration_minutes:
                slots.append({"start_time": _min_to_hhmm(cursor), "end_time": _min_to_hhmm(s), "duration_minutes": s - cursor})
            cursor = max(cursor, e)
        if day_end - cursor >= duration_minutes:
            slots.append({"start_time": _min_to_hhmm(cursor), "end_time": _min_to_hhmm(day_end), "duration_minutes": day_end - cursor})
        return {"date": target_date, "requested_minutes": duration_minutes, "free_slots": slots}

    def export_ics(self, target_date: Optional[str] = None) -> str:
        events = self.db.list_events(date=target_date)
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//JARVIS OS//Module 24 Email & Calendar Assistant//EN",
        ]
        for ev in events:
            d = ev["date"].replace("-", "")
            s = ev["start_time"].replace(":", "") + "00"
            e = ev["end_time"].replace(":", "") + "00"
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{ev['event_id']}@jarvis.local",
                    f"DTSTART:{d}T{s}",
                    f"DTEND:{d}T{e}",
                    f"SUMMARY:{ev['title']}",
                    f"LOCATION:{ev['location']}",
                    f"DESCRIPTION:{ev['description']}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def get_status(self) -> Dict[str, Any]:
        emails = self.db.list_emails()
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "inbox_count": len(emails),
            "unread_count": sum(1 for e in emails if not e["is_read"]),
            "urgent_count": sum(1 for e in emails if e["category"] == "urgent"),
            "drafts_count": len(self.db.list_drafts()),
            "pending_send_approvals": len(self.db.list_approvals(status="pending")),
            "calendar_events_count": len(self.db.list_events()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
