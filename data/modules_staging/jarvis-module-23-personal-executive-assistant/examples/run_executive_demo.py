"""Runnable CLI demonstration for JARVIS Module 23 — Personal Executive Assistant."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import ExecutiveAssistantConfig
from backend.services.executive_engine import PersonalExecutiveEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = ExecutiveAssistantConfig(db_path=str(Path(tmp) / "demo_exec.db"))
        engine = PersonalExecutiveEngine(cfg)
        today = "2026-11-20"

        print("1. Creating quarterly goal & prioritized Eisenhower tasks...")
        g = engine.create_goal({"title": "Ship JARVIS OS Phase B Modules", "horizon": "quarterly", "progress_pct": 40})
        engine.create_task({"title": "Finalize Module 23 API", "priority": "p1", "urgent": True, "important": True, "estimated_minutes": 60, "goal_id": g["goal_id"]})
        engine.create_task({"title": "Plan Raspberry Pi 5 benchmark", "priority": "p2", "urgent": False, "important": True, "estimated_minutes": 45})

        print("2. Scheduling a fixed meeting and auto-planning open focus slots...")
        engine.create_time_block({"date": today, "start_time": "09:30", "end_time": "10:15", "title": "Architecture Sync", "block_type": "meeting"})
        plan = engine.plan_day(today, max_tasks=3)
        print(f"   Auto-scheduled {plan['scheduled_count']} focus block(s) around existing meetings.")

        print("3. Tracking habit streak & follow-up...")
        h = engine.create_habit("90m Deep Work")
        engine.checkin_habit(h["habit_id"], "2026-11-19")
        h_today = engine.checkin_habit(h["habit_id"], today)
        print(f"   Habit '{h_today['name']}' streak: {h_today['current_streak']} day(s)")
        engine.create_followup({"person": "Design Lead", "topic": "Approve JARVIS HUD icons", "due_date": today})

        print("4. Generating Daily Executive Briefing...")
        brief = engine.generate_briefing(target_date=today)
        print(f"   {brief['executive_summary']}")
        engine.db.close()
        print("Demo complete.")


if __name__ == "__main__":
    main()
