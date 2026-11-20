"""Automated tests for JARVIS OS — AI Study Planner (unittest & pytest compatible)."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_ai_study_planner.app import create_app
from jarvis_ai_study_planner.config import StudyPlannerConfig
from jarvis_ai_study_planner.sm2 import compute_sm2


class TestAIStudyPlanner(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "study_planner.db"
        self.config = StudyPlannerConfig(db_path=self.db_path, provider="offline")
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sm2_algorithm_progression_and_reset(self) -> None:
        base = date(2026, 11, 20)
        r1, i1, ef1, d1 = compute_sm2(quality=4, repetitions=0, interval_days=1, ease_factor=2.5, today=base)
        self.assertEqual((r1, i1, d1), (1, 1, "2026-11-21"))

        r2, i2, ef2, d2 = compute_sm2(quality=5, repetitions=r1, interval_days=i1, ease_factor=ef1, today=base)
        self.assertEqual((r2, i2, d2), (2, 6, "2026-11-26"))

        r3, i3, ef3, _ = compute_sm2(quality=1, repetitions=r2, interval_days=i2, ease_factor=ef2, today=base)
        self.assertEqual((r3, i3), (0, 1))
        self.assertGreaterEqual(ef3, 1.3)

    def test_plan_milestones_sm2_review_and_export(self) -> None:
        health = self.client.get("/api/study-planner/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["feature"], "AI Study Planner")

        ui = self.client.get("/study-planner")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS OS — AI STUDY PLANNER", ui.text)

        created = self.client.post(
            "/api/study-planner/plans",
            json={
                "title": "Embedded Linux & Raspberry Pi 5",
                "goal": "Master systemd, GPIO HAL, and FastAPI services",
                "syllabus_topics": ["systemd Units", "GPIO & PWM", "SQLite WAL"],
                "daily_minutes": 45,
                "days_available": 9,
            },
        )
        self.assertEqual(created.status_code, 200)
        plan = created.json()
        plan_id = plan["id"]
        self.assertEqual(len(plan["milestones"]), 3)
        self.assertEqual(len(plan["schedule"]), 9)

        # Complete first milestone
        first_ms_id = plan["milestones"][0]["id"]
        upd = self.client.patch(
            f"/api/study-planner/milestones/{first_ms_id}",
            json={"status": "completed"},
        )
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(upd.json()["status"], "completed")

        # Review a due SM-2 flashcard
        due = self.client.get("/api/study-planner/flashcards", params={"due_only": "true"})
        self.assertEqual(due.status_code, 200)
        self.assertEqual(due.json()["total"], 3)
        card_id = due.json()["cards"][0]["id"]

        rev = self.client.post(
            f"/api/study-planner/flashcards/{card_id}/review",
            json={"quality": 5},
        )
        self.assertEqual(rev.status_code, 200)
        self.assertEqual(rev.json()["repetitions"], 1)

        # Export Markdown
        exp = self.client.get(f"/api/study-planner/plans/{plan_id}/export")
        self.assertEqual(exp.status_code, 200)
        self.assertIn("Study Plan: Embedded Linux", exp.text)

        # Progress check
        prog = self.client.get("/api/study-planner/progress")
        self.assertEqual(prog.status_code, 200)
        self.assertEqual(prog.json()["completed_milestones"], 1)
        self.assertEqual(prog.json()["due_cards_today"], 2)


if __name__ == "__main__":
    unittest.main()
