"""Personal Executive Assistant Engine (Module 23).

Provides:
- Goals/OKR tracking
- Eisenhower Matrix priority classification (do_first, schedule, delegate, eliminate)
- Time-blocked scheduling with overlap conflict detection & smart day auto-planner
- Habit streak computation
- Delegation & follow-up tracking with overdue detection
- Actionable Daily Executive Briefing synthesis
"""

from __future__ import annotations

import time
import uuid
from datetime import date as dt_date, timedelta
from typing import Any, Dict, List, Optional

from backend.adapters.executive_adapter import ExecutiveSynthesisAdapter, LocalRuleExecutiveAdapter
from backend.app.config import ExecutiveAssistantConfig
from backend.models.database import ExecutiveAssistantDB, utc_now_iso


class ExecutiveAssistantError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def compute_quadrant(urgent: bool, important: bool) -> str:
    if urgent and important:
        return "do_first"
    if not urgent and important:
        return "schedule"
    if urgent and not important:
        return "delegate"
    return "eliminate"


def _hhmm_to_min(hhmm: str) -> int:
    try:
        parts = hhmm.strip().split(":")
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return h * 60 + m
    except Exception as exc:
        raise ExecutiveAssistantError("INVALID_TIME", f"Invalid HH:MM time '{hhmm}'.", 422) from exc


def _min_to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def compute_streak(checkin_dates: List[str], reference_date: str) -> int:
    if not checkin_dates:
        return 0
    date_set = set(checkin_dates)
    try:
        cur = dt_date.fromisoformat(reference_date)
    except ValueError:
        cur = dt_date.today()
    streak = 0
    if cur.isoformat() not in date_set:
        cur = cur - timedelta(days=1)
    while cur.isoformat() in date_set:
        streak += 1
        cur = cur - timedelta(days=1)
    return streak


class PersonalExecutiveEngine:
    def __init__(
        self,
        config: Optional[ExecutiveAssistantConfig] = None,
        db: Optional[ExecutiveAssistantDB] = None,
        adapter: Optional[ExecutiveSynthesisAdapter] = None,
    ) -> None:
        self.config = config or ExecutiveAssistantConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or ExecutiveAssistantDB(self.config.db_path)
        self.adapter = adapter or LocalRuleExecutiveAdapter()
        self._started_at = time.monotonic()

    # --- Goals ---
    def create_goal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        return self.db.create_goal(
            {
                "goal_id": f"goal_{uuid.uuid4().hex[:10]}",
                "title": payload["title"],
                "horizon": payload.get("horizon", "quarterly"),
                "priority": payload.get("priority", "high"),
                "target_date": payload.get("target_date"),
                "progress_pct": int(payload.get("progress_pct", 0)),
                "status": "completed" if int(payload.get("progress_pct", 0)) >= 100 else "active",
                "created_at": now,
                "updated_at": now,
            }
        )

    def update_goal(self, goal_id: str, progress_pct: int, status: Optional[str] = None) -> Dict[str, Any]:
        updated = self.db.update_goal(goal_id, progress_pct, status=status)
        if not updated:
            raise ExecutiveAssistantError("GOAL_NOT_FOUND", f"Goal '{goal_id}' not found.", 404)
        return updated

    # --- Tasks ---
    def create_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        urgent = bool(payload.get("urgent", False))
        important = bool(payload.get("important", True))
        return self.db.create_task(
            {
                "task_id": f"tsk_{uuid.uuid4().hex[:10]}",
                "title": payload["title"],
                "description": payload.get("description", ""),
                "priority": payload.get("priority", "p2"),
                "urgent": urgent,
                "important": important,
                "quadrant": compute_quadrant(urgent, important),
                "due_date": payload.get("due_date"),
                "estimated_minutes": int(payload.get("estimated_minutes", 45)),
                "goal_id": payload.get("goal_id"),
                "status": "todo",
                "created_at": now,
                "updated_at": now,
            }
        )

    def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        updated = self.db.update_task_status(task_id, status)
        if not updated:
            raise ExecutiveAssistantError("TASK_NOT_FOUND", f"Task '{task_id}' not found.", 404)
        return updated

    # --- Time Blocks & Smart Auto-Planner ---
    def create_time_block(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        start_m = _hhmm_to_min(payload["start_time"])
        end_m = _hhmm_to_min(payload["end_time"])
        if end_m <= start_m:
            raise ExecutiveAssistantError("INVALID_RANGE", "end_time must be after start_time.", 422)

        existing = self.db.list_time_blocks(date=payload["date"])
        for b in existing:
            b_start = _hhmm_to_min(b["start_time"])
            b_end = _hhmm_to_min(b["end_time"])
            if start_m < b_end and end_m > b_start:
                raise ExecutiveAssistantError(
                    "SCHEDULE_CONFLICT",
                    f"Time block {payload['start_time']}-{payload['end_time']} overlaps with '{b['title']}' ({b['start_time']}-{b['end_time']}).",
                    409,
                    {"conflicting_block_id": b["block_id"]},
                )

        return self.db.create_time_block(
            {
                "block_id": f"blk_{uuid.uuid4().hex[:10]}",
                "date": payload["date"],
                "start_time": _min_to_hhmm(start_m),
                "end_time": _min_to_hhmm(end_m),
                "title": payload["title"],
                "block_type": payload.get("block_type", "deep_work"),
                "task_id": payload.get("task_id"),
                "created_at": utc_now_iso(),
            }
        )

    def plan_day(self, target_date: str, max_tasks: int = 4) -> Dict[str, Any]:
        existing = self.db.list_time_blocks(date=target_date)
        occupied = sorted([(_hhmm_to_min(b["start_time"]), _hhmm_to_min(b["end_time"])) for b in existing])
        already_scheduled_tasks = {b["task_id"] for b in existing if b.get("task_id")}

        quadrant_rank = {"do_first": 0, "schedule": 1, "delegate": 2, "eliminate": 3}
        open_tasks = [
            t for t in self.db.list_tasks()
            if t["status"] in ("todo", "in_progress") and t["task_id"] not in already_scheduled_tasks
        ]
        open_tasks.sort(key=lambda t: (quadrant_rank.get(t["quadrant"], 3), t["priority"]))

        day_start = self.config.workday_start_hour * 60
        day_end = self.config.workday_end_hour * 60
        created_blocks: List[Dict[str, Any]] = []

        for t in open_tasks[:max_tasks]:
            dur = int(t["estimated_minutes"])
            cursor = day_start
            placed = False
            for s, e in occupied:
                if cursor + dur <= s:
                    blk = self.create_time_block(
                        {
                            "date": target_date,
                            "start_time": _min_to_hhmm(cursor),
                            "end_time": _min_to_hhmm(cursor + dur),
                            "title": f"Focus: {t['title']}",
                            "block_type": "deep_work",
                            "task_id": t["task_id"],
                        }
                    )
                    created_blocks.append(blk)
                    occupied.append((cursor, cursor + dur))
                    occupied.sort()
                    placed = True
                    break
                cursor = max(cursor, e + 10)  # 10-min buffer
            if not placed and cursor + dur <= day_end:
                blk = self.create_time_block(
                    {
                        "date": target_date,
                        "start_time": _min_to_hhmm(cursor),
                        "end_time": _min_to_hhmm(cursor + dur),
                        "title": f"Focus: {t['title']}",
                        "block_type": "deep_work",
                        "task_id": t["task_id"],
                    }
                )
                created_blocks.append(blk)
                occupied.append((cursor, cursor + dur))
                occupied.sort()

        return {
            "date": target_date,
            "scheduled_count": len(created_blocks),
            "created_blocks": created_blocks,
            "all_blocks": self.db.list_time_blocks(date=target_date),
        }

    # --- Habits ---
    def create_habit(self, name: str, cadence: str = "daily") -> Dict[str, Any]:
        return self.db.create_habit(
            {"habit_id": f"hab_{uuid.uuid4().hex[:10]}", "name": name, "cadence": cadence, "created_at": utc_now_iso()}
        )

    def checkin_habit(self, habit_id: str, checkin_date: str) -> Dict[str, Any]:
        ok = self.db.record_habit_checkin(habit_id, checkin_date)
        if not ok:
            raise ExecutiveAssistantError("HABIT_NOT_FOUND", f"Habit '{habit_id}' not found.", 404)
        habits = self.list_habits_with_streaks(reference_date=checkin_date)
        return next(h for h in habits if h["habit_id"] == habit_id)

    def list_habits_with_streaks(self, reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
        ref = reference_date or dt_date.today().isoformat()
        habits = self.db.list_habits()
        for h in habits:
            h["current_streak"] = compute_streak(h["checkin_dates"], ref)
        return habits

    # --- Follow-ups ---
    def create_followup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        return self.db.create_followup(
            {
                "followup_id": f"fup_{uuid.uuid4().hex[:10]}",
                "person": payload["person"],
                "topic": payload["topic"],
                "due_date": payload["due_date"],
                "status": "open",
                "created_at": now,
                "updated_at": now,
            }
        )

    def update_followup(self, followup_id: str, status: str) -> Dict[str, Any]:
        updated = self.db.update_followup(followup_id, status)
        if not updated:
            raise ExecutiveAssistantError("FOLLOWUP_NOT_FOUND", f"Follow-up '{followup_id}' not found.", 404)
        return updated

    # --- Executive Briefing & Status ---
    def generate_briefing(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        ref = target_date or dt_date.today().isoformat()
        tasks = [t for t in self.db.list_tasks() if t["status"] in ("todo", "in_progress")]
        q_counts = {"do_first": 0, "schedule": 0, "delegate": 0, "eliminate": 0}
        for t in tasks:
            q_counts[t["quadrant"]] = q_counts.get(t["quadrant"], 0) + 1

        quadrant_rank = {"do_first": 0, "schedule": 1, "delegate": 2, "eliminate": 3}
        top_priorities = sorted(tasks, key=lambda t: (quadrant_rank.get(t["quadrant"], 3), t["priority"]))[:5]
        blocks = self.db.list_time_blocks(date=ref)
        goals = self.db.list_goals()
        habits = self.list_habits_with_streaks(reference_date=ref)
        open_fups = self.db.list_followups(status="open")
        overdue_fups = [f for f in open_fups if f["due_date"] <= ref]

        ctx = {
            "date": ref,
            "simulated_synthesis": self.adapter.is_simulated,
            "quadrant_counts": q_counts,
            "top_priorities": top_priorities,
            "time_blocks": blocks,
            "active_goals": [g for g in goals if g["status"] == "active"],
            "habits": habits,
            "overdue_followups": overdue_fups,
        }
        ctx["executive_summary"] = self.adapter.synthesize_briefing(ctx)
        return ctx

    def get_status(self) -> Dict[str, Any]:
        tasks = self.db.list_tasks()
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "goals_count": len(self.db.list_goals()),
            "open_tasks_count": sum(1 for t in tasks if t["status"] in ("todo", "in_progress")),
            "completed_tasks_count": sum(1 for t in tasks if t["status"] == "done"),
            "habits_count": len(self.db.list_habits()),
            "open_followups_count": len(self.db.list_followups(status="open")),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
