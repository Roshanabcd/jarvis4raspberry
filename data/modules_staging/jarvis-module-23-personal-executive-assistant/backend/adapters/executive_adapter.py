"""Executive briefing synthesis adapter contract & local deterministic adapter for Module 23."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ExecutiveSynthesisAdapter(ABC):
    adapter_name: str = "abstract"
    is_simulated: bool = True

    @abstractmethod
    def synthesize_briefing(self, context: Dict[str, Any]) -> str:
        raise NotImplementedError


class LocalRuleExecutiveAdapter(ExecutiveSynthesisAdapter):
    """Offline deterministic executive briefing synthesizer (swap with live LLM adapter via Module 22)."""

    adapter_name = "local_rule_executive_synthesizer"
    is_simulated = True

    def synthesize_briefing(self, context: Dict[str, Any]) -> str:
        date = context["date"]
        do_first = context["quadrant_counts"].get("do_first", 0)
        blocks = len(context["time_blocks"])
        overdue = len(context["overdue_followups"])
        top_titles = [t["title"] for t in context["top_priorities"][:3]]
        focus_str = "; ".join(top_titles) if top_titles else "No urgent tasks queued"
        return (
            f"[LOCAL EXECUTIVE BRIEF | {date}] "
            f"You have {do_first} Do-First task(s), {blocks} scheduled time block(s), "
            f"and {overdue} overdue follow-up(s). Top focus: {focus_str}."
        )
