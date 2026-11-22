"""Automated tests for JARVIS OS — AI Interview Bot (unittest & pytest compatible)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_ai_interview_bot.app import create_app
from jarvis_ai_interview_bot.config import InterviewBotConfig


class TestAIInterviewBot(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "interview_bot.db"
        self.config = InterviewBotConfig(
            db_path=self.db_path,
            provider="offline",
        )
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_and_ui(self) -> None:
        res = self.client.get("/api/interview-bot/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["feature"], "AI Interview Bot")
        self.assertEqual(body["provider"], "offline-rubric")

        ui = self.client.get("/interview-bot")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS OS — AI INTERVIEW BOT", ui.text)

    def test_full_adaptive_interview_loop_and_export(self) -> None:
        start = self.client.post(
            "/api/interview-bot/sessions/start",
            json={
                "candidate_name": "Roshan",
                "role": "Python / Backend Engineer",
                "mode": "mixed",
                "difficulty": "Mid",
                "total_questions": 2,
            },
        )
        self.assertEqual(start.status_code, 200)
        s_body = start.json()
        session_id = s_body["session_id"]
        self.assertEqual(s_body["current_question"]["turn_number"], 1)
        self.assertEqual(s_body["current_question"]["category"], "technical")

        # Turn 1: strong detailed answer
        ans1 = self.client.post(
            f"/api/interview-bot/sessions/{session_id}/answer",
            json={
                "answer": (
                    "First, I enable SQLite WAL mode with PRAGMA journal_mode=WAL and foreign key enforcement. "
                    "Second, I configure a 10s busy timeout and keep transactions short so concurrent reads never lock out writers. "
                    "Finally, I add targeted indexes on timestamp columns and verify edge cases with automated tests."
                )
            },
        )
        self.assertEqual(ans1.status_code, 200)
        a1 = ans1.json()
        self.assertEqual(a1["status"], "in_progress")
        self.assertEqual(a1["remaining_questions"], 1)
        self.assertGreaterEqual(a1["evaluation"]["rubric"]["overall_score"], 70)
        self.assertEqual(a1["next_question"]["turn_number"], 2)
        self.assertEqual(a1["next_question"]["category"], "behavioral")

        # Turn 2: STAR behavioral answer -> completes interview
        ans2 = self.client.post(
            f"/api/interview-bot/sessions/{session_id}/answer",
            json={
                "answer": (
                    "Situation: We had a tight deadline on a Raspberry Pi 5 robotics API. "
                    "Task: Choose between a heavy cloud queue and a local SQLite WAL store. "
                    "Action: I evaluated trade-offs across memory and latency, built a modular fallback, and ran 100% automated tests. "
                    "Result: Cut RAM usage by 40% and delivered zero downtime."
                )
            },
        )
        self.assertEqual(ans2.status_code, 200)
        a2 = ans2.json()
        self.assertEqual(a2["status"], "completed")
        self.assertEqual(a2["remaining_questions"], 0)
        self.assertIsNone(a2["next_question"])

        # Subsequent answer on completed session should fail cleanly with 400
        extra = self.client.post(
            f"/api/interview-bot/sessions/{session_id}/answer",
            json={"answer": "Extra answer after completion"},
        )
        self.assertEqual(extra.status_code, 400)

        # Fetch report & export markdown
        rep = self.client.get(f"/api/interview-bot/sessions/{session_id}/report")
        self.assertEqual(rep.status_code, 200)
        r_body = rep.json()
        self.assertEqual(r_body["status"], "completed")
        self.assertEqual(len(r_body["turns"]), 2)
        self.assertGreater(r_body["overall_score"], 0)

        exp = self.client.get(f"/api/interview-bot/sessions/{session_id}/export")
        self.assertEqual(exp.status_code, 200)
        self.assertIn("JARVIS OS — Interview Feedback Report", exp.text)

        # Session list
        listed = self.client.get("/api/interview-bot/sessions")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["total"], 1)


if __name__ == "__main__":
    unittest.main()
