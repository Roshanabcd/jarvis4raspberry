"""Core AI Study Planner engine: goal breakdown, personalized schedules, milestones, and SM-2 reviews."""

from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta
from typing import Any, Dict, List

from .config import StudyPlannerConfig
from .llm_provider import StudyLLMClient
from .models import (
    CreateFlashcardRequest,
    CreateStudyPlanRequest,
    FlashcardRecord,
    MilestoneItem,
    ReviewFlashcardRequest,
    StudyBlock,
    StudyPlanDetail,
    StudyProgressResponse,
)
from .sm2 import compute_sm2
from .storage import StudyPlannerStore


class StudyPlannerEngine:
    """Breaks learning goals into syllabus milestones, daily schedules, and SM-2 review decks."""

    def __init__(
        self,
        config: StudyPlannerConfig,
        store: StudyPlannerStore,
        llm: StudyLLMClient,
    ) -> None:
        self.config = config
        self.store = store
        self.llm = llm

    async def create_plan(self, req: CreateStudyPlanRequest) -> StudyPlanDetail:
        start = date.fromisoformat(req.start_date) if req.start_date else date.today()
        system_prompt = (
            "You are an academic study coach inside JARVIS OS. Return ONLY a JSON array of 4-8 syllabus milestones, "
            'each with keys: "title" (str), "description" (str), "estimated_minutes" (int).'
        )
        user_prompt = (
            f"Title: {req.title}\n"
            f"Goal: {req.goal}\n"
            f"Current level: {req.current_level}\n"
            f"Daily budget: {req.daily_minutes} minutes for {req.days_available} days\n"
            f"Syllabus topics: {', '.join(req.syllabus_topics) if req.syllabus_topics else 'Derive from goal'}\n"
        )

        res = await self.llm.complete(system_prompt, user_prompt)
        raw_milestones = self._parse_llm_milestones(res.text) if (not res.used_fallback and res.text) else []

        if not raw_milestones:
            raw_milestones = self._offline_milestones(req)

        # Assign target dates evenly across available days
        total_ms = len(raw_milestones)
        milestones_with_dates: List[Dict[str, Any]] = []
        for idx, m in enumerate(raw_milestones):
            day_offset = min(
                req.days_available - 1,
                max(0, round(((idx + 1) / total_ms) * req.days_available) - 1),
            )
            milestones_with_dates.append(
                {
                    "title": str(m["title"])[:180],
                    "description": str(m["description"])[:600],
                    "estimated_minutes": max(15, int(m.get("estimated_minutes", req.daily_minutes))),
                    "target_date": (start + timedelta(days=day_offset)).isoformat(),
                }
            )

        schedule = self._build_daily_schedule(
            milestones=milestones_with_dates,
            start=start,
            days_available=req.days_available,
            daily_minutes=req.daily_minutes,
        )
        plan_md = self._format_plan_markdown(req, milestones_with_dates, schedule)

        plan_id = self.store.create_plan(
            title=req.title,
            goal=req.goal,
            current_level=req.current_level,
            daily_minutes=req.daily_minutes,
            days_available=req.days_available,
            provider_used=res.provider_used,
            milestones=milestones_with_dates,
            schedule=schedule,
            plan_markdown=plan_md,
        )

        # Seed one starter spaced-repetition flashcard per milestone so SM-2 tracking works immediately
        for m in milestones_with_dates:
            self.store.create_flashcard(
                plan_id=plan_id,
                topic=m["title"],
                question=f"What are the core concepts and key takeaways of '{m['title']}'?",
                answer=m["description"],
                next_review_date=start.isoformat(),
            )

        plan_data = self.store.get_plan(plan_id)
        assert plan_data is not None
        return StudyPlanDetail(
            **{
                **plan_data,
                "milestones": [MilestoneItem(**m) for m in plan_data["milestones"]],
                "schedule": [StudyBlock(**s) for s in plan_data["schedule"]],
            }
        )

    @staticmethod
    def _parse_llm_milestones(text: str) -> List[Dict[str, Any]]:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                valid = [m for m in data if isinstance(m, dict) and m.get("title") and m.get("description")]
                return valid[:10]
        except json.JSONDecodeError:
            return []
        return []

    @staticmethod
    def _offline_milestones(req: CreateStudyPlanRequest) -> List[Dict[str, Any]]:
        total_budget = req.daily_minutes * req.days_available
        if req.syllabus_topics:
            topics = [t.strip() for t in req.syllabus_topics if t.strip()]
        else:
            topics = [
                f"Foundations & Core Mental Models ({req.title})",
                f"Guided Practice & Worked Examples ({req.title})",
                f"Hands-On Mini-Project / Problem Solving ({req.title})",
                f"Edge Cases, Debugging & Deep Mastery ({req.title})",
                f"Final Review, Timed Recall & Capstone Check ({req.title})",
            ]
        per_ms = max(30, math.floor(total_budget / max(1, len(topics))))
        return [
            {
                "title": topic,
                "description": (
                    f"Master '{topic}' at {req.current_level} level toward your goal: {req.goal.strip()}. "
                    "Summarize key concepts in your own words and solve 3 active-recall exercises."
                ),
                "estimated_minutes": per_ms,
            }
            for topic in topics
        ]

    @staticmethod
    def _build_daily_schedule(
        milestones: List[Dict[str, Any]],
        start: date,
        days_available: int,
        daily_minutes: int,
    ) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        n_ms = max(1, len(milestones))
        for day_idx in range(days_available):
            current_date = (start + timedelta(days=day_idx)).isoformat()
            ms_idx = min(n_ms - 1, int((day_idx / days_available) * n_ms))
            topic = milestones[ms_idx]["title"]

            if day_idx > 0 and (day_idx + 1) % 4 == 0:
                activity = "spaced_review"
                focus = f"Spaced-Repetition Review + Active Recall ({topic})"
            elif day_idx % 2 == 1:
                activity = "practice"
                focus = f"Applied Practice & Exercises: {topic}"
            else:
                activity = "deep_study"
                focus = f"Focused Concept Study: {topic}"

            blocks.append(
                {
                    "day_number": day_idx + 1,
                    "date": current_date,
                    "focus_topic": focus,
                    "minutes": daily_minutes,
                    "activity_type": activity,
                }
            )
        return blocks

    @staticmethod
    def _format_plan_markdown(
        req: CreateStudyPlanRequest,
        milestones: List[Dict[str, Any]],
        schedule: List[Dict[str, Any]],
    ) -> str:
        lines = [
            f"# Study Plan: {req.title}",
            "",
            f"- **Goal:** {req.goal}",
            f"- **Level:** {req.current_level}",
            f"- **Schedule Budget:** {req.daily_minutes} min/day for {req.days_available} days",
            "",
            "## Syllabus Milestones",
            "",
        ]
        for idx, m in enumerate(milestones, start=1):
            lines.append(
                f"{idx}. **{m['title']}** (Target: {m['target_date']} • ~{m['estimated_minutes']} min) — {m['description']}"
            )
        lines.extend(["", "## Daily Study Schedule", ""])
        for b in schedule:
            lines.append(
                f"- **Day {b['day_number']} ({b['date']})** [{b['activity_type']} • {b['minutes']} min]: {b['focus_topic']}"
            )
        return "\n".join(lines).strip() + "\n"

    def create_flashcard(self, req: CreateFlashcardRequest) -> FlashcardRecord:
        today = date.today().isoformat()
        row = self.store.create_flashcard(
            plan_id=req.plan_id,
            topic=req.topic,
            question=req.question,
            answer=req.answer,
            next_review_date=today,
        )
        return FlashcardRecord(**row)

    def review_flashcard(self, card_id: int, req: ReviewFlashcardRequest) -> FlashcardRecord:
        card = self.store.get_flashcard(card_id)
        if not card:
            raise KeyError(f"Flashcard {card_id} not found.")
        new_reps, new_interval, new_ef, next_date = compute_sm2(
            quality=req.quality,
            repetitions=int(card["repetitions"]),
            interval_days=int(card["interval_days"]),
            ease_factor=float(card["ease_factor"]),
        )
        updated = self.store.update_flashcard_sm2(
            card_id=card_id,
            repetitions=new_reps,
            interval_days=new_interval,
            ease_factor=new_ef,
            next_review_date=next_date,
        )
        assert updated is not None
        return FlashcardRecord(**updated)

    def get_progress(self) -> StudyProgressResponse:
        c = self.store.progress_counts()
        total_ms = c["total_milestones"]
        pct = round((c["completed_milestones"] / total_ms) * 100.0, 1) if total_ms else 0.0
        return StudyProgressResponse(
            total_plans=c["total_plans"],
            total_milestones=total_ms,
            completed_milestones=c["completed_milestones"],
            overall_completion_pct=pct,
            total_cards=c["total_cards"],
            due_cards_today=c["due_cards_today"],
            mastered_cards=c["mastered_cards"],
        )
