"""Automated tests for JARVIS OS — Customer Support Bot (unittest & pytest compatible)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_customer_support_bot.app import create_app
from jarvis_customer_support_bot.config import SupportBotConfig


class TestCustomerSupportBot(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "support_bot.db"
        self.config = SupportBotConfig(db_path=self.db_path, provider="offline")
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_ui_kb_triage_and_escalation(self) -> None:
        health = self.client.get("/api/support-bot/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        ui = self.client.get("/support-bot")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS OS — CUSTOMER SUPPORT BOT", ui.text)

        # Seed a domain KB article
        kb = self.client.post(
            "/api/support-bot/kb",
            json={
                "title": "Password Reset Guide",
                "category": "account_access",
                "content": "To reset your password, click Forgot Password on the login screen and check your inbox.",
                "tags": ["password", "login", "reset"],
            },
        )
        self.assertEqual(kb.status_code, 200)

        # 1. Routine positive/neutral inquiry matched by KB -> no escalation
        r1 = self.client.post(
            "/api/support-bot/inquire",
            json={
                "customer_name": "Priya",
                "subject": "How to reset my password",
                "message": "Thanks! Can you remind me how to reset my login password?",
            },
        )
        self.assertEqual(r1.status_code, 200)
        b1 = r1.json()
        self.assertFalse(b1["triage"]["escalate"])
        self.assertIn("Password Reset Guide", b1["matched_kb_titles"])

        # 2. Urgent security breach -> P1_CRITICAL & escalated to security-oncall
        r2 = self.client.post(
            "/api/support-bot/inquire",
            json={
                "customer_name": "Sam",
                "subject": "URGENT unauthorized login",
                "message": "My account was hacked with an unauthorized breach! Fix immediately!!!",
            },
        )
        self.assertEqual(r2.status_code, 200)
        b2 = r2.json()
        self.assertTrue(b2["triage"]["escalate"])
        self.assertEqual(b2["triage"]["priority"], "P1_CRITICAL")
        self.assertEqual(b2["triage"]["escalation_team"], "security-oncall")
        self.assertEqual(b2["status"], "escalated")

        # 3. Resolve ticket and verify stats
        upd = self.client.patch(
            f"/api/support-bot/tickets/{b2['ticket_id']}",
            json={"status": "resolved"},
        )
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(upd.json()["status"], "resolved")

        stats = self.client.get("/api/support-bot/stats").json()
        self.assertEqual(stats["total_tickets"], 2)
        self.assertEqual(stats["resolved_tickets"], 1)


if __name__ == "__main__":
    unittest.main()
