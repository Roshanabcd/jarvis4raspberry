"""Meeting intelligence synthesis adapter contract & offline local adapter for Module 25."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class MeetingSynthesisAdapter(ABC):
    adapter_name: str = "abstract"
    is_simulated: bool = True

    @abstractmethod
    def generate_executive_overview(
        self,
        meeting: Dict[str, Any],
        segments: List[Dict[str, Any]],
        decisions: List[str],
        action_items: List[Dict[str, Any]],
        risks: List[str],
    ) -> str:
        raise NotImplementedError


class LocalMeetingSynthesisAdapter(MeetingSynthesisAdapter):
    """Offline deterministic meeting summarizer (swap with live LLM or Module 22 router)."""

    adapter_name = "local_meeting_synthesizer"
    is_simulated = True

    def generate_executive_overview(
        self,
        meeting: Dict[str, Any],
        segments: List[Dict[str, Any]],
        decisions: List[str],
        action_items: List[Dict[str, Any]],
        risks: List[str],
    ) -> str:
        speakers = sorted({s["speaker"] for s in segments})
        return (
            f"[LOCAL MEETING SUMMARY] \"{meeting['title']}\" ({meeting['meeting_date']}) "
            f"recorded {len(segments)} transcript segment(s) across {len(speakers)} speaker(s) ({', '.join(speakers) or 'none'}). "
            f"Extracted {len(decisions)} decision(s), {len(action_items)} action item(s), and {len(risks)} risk/blocker(s)."
        )
