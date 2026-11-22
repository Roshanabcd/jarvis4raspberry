"""Mail & Calendar provider adapter contract and SimulatedMailCalendarAdapter for Module 24."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from backend.models.database import utc_now_iso


class MailCalendarAdapter(ABC):
    adapter_name: str = "abstract"
    is_simulated: bool = True

    @abstractmethod
    def send_email(self, to_address: str, subject: str, body: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_reply_body(self, email: Dict[str, Any], tone: str, extra_notes: str) -> str:
        raise NotImplementedError


class SimulatedMailCalendarAdapter(MailCalendarAdapter):
    """Safe offline mail & calendar transport adapter (never transmits real SMTP/Gmail messages)."""

    adapter_name = "simulated_mail_calendar"
    is_simulated = True

    def send_email(self, to_address: str, subject: str, body: str) -> Dict[str, Any]:
        return {
            "simulated": True,
            "delivered": True,
            "to_address": to_address,
            "subject": subject,
            "message_id": f"<sim-{abs(hash((to_address, subject))) % 10**8}@jarvis.local>",
            "sent_at": utc_now_iso(),
            "note": "[SIMULATED] Message logged locally after human approval. Connect SMTP/Gmail API adapter for real delivery.",
        }

    def generate_reply_body(self, email: Dict[str, Any], tone: str, extra_notes: str) -> str:
        greeting = "Hi," if tone == "friendly" else "Hello,"
        closing = "Best,\nRoshan" if tone == "concise" else "Best regards,\nRoshan"
        note_line = f"\n\nAdditional note: {extra_notes.strip()}" if extra_notes.strip() else ""
        return (
            f"{greeting}\n\n"
            f"Thank you for your email regarding \"{email['subject']}\". "
            f"I have reviewed the details and will follow up with the next steps shortly.{note_line}\n\n"
            f"{closing}"
        )
