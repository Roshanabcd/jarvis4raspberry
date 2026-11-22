"""Unit tests for JARVIS Module 23 — PersonalExecutiveEngine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.config import ExecutiveAssistantConfig
from backend.services.executive_engine import (
    ExecutiveAssistantError,
    PersonalExecutiveEngine,
    compute_quadrant,
)


class TestExecutiveEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg = ExecutiveAssistantConfig(db_path=str(Path(self._tmp.name) / "test_m23.db"))
        self.engine = PersonalExecutiveEngine(self.cfg)

    def tearDown(self) -> None:
        self.engine.db.close()
        self._tmp.cleanup()

    def test_eisenhower_quadrant_classification(self) -> None:
        self.assertEqual(compute_quadrant(True, True), "do_first")
        self.assertEqual(compute_quadrant(False, True), "schedule")
        self.assertEqual(compute_quadrant(True, False), "delegate")
        self.assertEqual(compute_quadrant(False, False), "eliminate")

    def test_time_block_conflict_detection(self) -> None:
        self.engine.create_time_block(
            {"date": "2026-11-20", "start_time": "10:00", "end_time": "11:00", "title": "Standup"}
        )
        with self.assertRaises(ExecutiveAssistantError) as ctx:
            self.engine.create_time_block(
                {"date": "2026-11-20", "start_time": "10:30", "end_time": "11:30", "title": "Overlap"}
            )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.code, "SCHEDULE_CONFLICT")

    def test_smart_day_auto_planner_avoids_meetings(self) -> None:
        self.engine.create_time_block(
            {"date": "2026-11-20", "start_time": "09:00", "end_time": "10:00", "title": "Morning Meeting", "block_type": "meeting"}
        )
        self.engine.create_task({"title": "Deep Work A", "urgent": True, "important": True, "estimated_minutes": 60})
        self.engine.create_task({"title": "Deep Work B", "urgent": False, "important": True, "estimated_minutes": 45})

        plan = self.engine.plan_day("2026-11-20", max_tasks=4)
        self.assertEqual(plan["scheduled_count"], 2)
        self.assertEqual(plan["created_blocks"][0]["start_time"], "10:10")
        self.assertEqual(plan["created_blocks"][0]["end_time"], "11:10")

    def test_habit_streak_and_goal_completion(self) -> None:
        g = self.engine.create_goal({"title": "Ship Module 23", "progress_pct": 50})
        g2 = self.engine.update_goal(g["goal_id"], 100)
        self.assertEqual(g2["status"], "completed")

        h = self.engine.create_habit("Read 20 pages")
        self.engine.checkin_habit(h["habit_id"], "2026-11-18")
        self.engine.checkin_habit(h["habit_id"], "2026-11-19")
        h_today = self.engine.checkin_habit(h["habit_id"], "2026-11-20")
        self.assertEqual(h_today["current_streak"], 3)

    def test_executive_briefing_synthesis(self) -> None:
        self.engine.create_task({"title": "Launch Review", "urgent": True, "important": True})
        self.engine.create_followup({"person": "Ops", "topic": "SSL Renewal", "due_date": "2026-11-19"})
        brief = self.engine.generate_briefing(target_date="2026-11-20")
        self.assertEqual(brief["quadrant_counts"]["do_first"], 1)
        self.assertEqual(len(brief["overdue_followups"]), 1)
        self.assertIn("Launch Review", brief["executive_summary"])


if __name__ == "__main__":
    unittest.main()
