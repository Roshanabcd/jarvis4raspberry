"""
JARVIS Compound Task Orchestrator (Phase 1E)
Detects compound multi-task user requests, segments them into discrete sub-tasks,
executes deterministic tools and AI reasoning per task, and produces a single unified response.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.CompoundTaskOrchestrator")


class CompoundTaskOrchestrator:
    """Orchestrates multi-task prompts containing 2 or more distinct actions."""

    # Trigger patterns indicating potential compound requests
    COMPOUND_DELIMITER_REGEX = re.compile(
        r',\s*(?:and\s+|also\s+|then\s+)?|;\s*|\band\s+(?=(?:calculate|compute|tell|write|check|get|what\s+is|show)\b)',
        re.IGNORECASE
    )

    ACTION_VERBS_REGEX = re.compile(
        r'\b(?:tell|calculate|compute|write|check|get|what\s+is|show|find|search|read|save|remember|store)\b',
        re.IGNORECASE
    )

    @classmethod
    def is_compound_request(cls, text: str) -> bool:
        """Determine if a prompt contains multiple distinct operational clauses."""
        text_clean = text.strip()
        # If too short, cannot be compound
        if len(text_clean) < 25:
            return False

        # If it's a code block or markdown, don't split
        if "```" in text_clean:
            return False

        parts = cls.split_subtasks(text_clean)
        if len(parts) < 2:
            return False

        # Verify that at least 2 parts contain actionable verbs or inquiries
        action_count = sum(1 for p in parts if cls.ACTION_VERBS_REGEX.search(p))
        return action_count >= 2

    @classmethod
    def split_subtasks(cls, text: str) -> List[str]:
        """Split a compound prompt into clean sub-task strings."""
        raw_parts = cls.COMPOUND_DELIMITER_REGEX.split(text.strip())
        cleaned = []
        for p in raw_parts:
            s = p.strip().rstrip(".,;")
            if s:
                cleaned.append(s)
        return cleaned

    @classmethod
    def execute_compound(
        cls,
        text: str,
        brain: Any,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute sub-tasks sequentially and combine into a coherent markdown report.
        """
        subtasks = cls.split_subtasks(text)
        logger.info(f"Executing compound request with {len(subtasks)} sub-tasks: {subtasks}")

        from tools.calculator.calculator_tools import calculator_tools
        from tools.system.system_tools import system_tools
        from hardware.raspberry_pi.rpi_info import get_system_status

        sections: List[str] = []
        all_tools_used: List[Dict[str, Any]] = []

        for idx, task in enumerate(subtasks, start=1):
            task_lower = task.lower()

            # 1. Memory / RAM inquiry
            if re.search(r'\b(ram|memory)\b', task_lower) and not re.search(r'\b(write|script|code|program)\b', task_lower):
                mem = system_tools.get_memory_usage()
                all_tools_used.append({"tool": "get_memory_usage"})
                section = (
                    f"### {idx}. RAM Usage\n"
                    f"- **Memory Used:** {mem['ram_used_gb']} GB / {mem['ram_total_gb']} GB ({mem['ram_pct']}% used)\n"
                    f"- **Available RAM:** {mem['ram_avail_gb']} GB\n"
                    f"- **Swap Usage:** {mem['swap_used_gb']} GB / {mem['swap_total_gb']} GB ({mem['swap_pct']}%)"
                )
                sections.append(section)

            # 2. System Status / Uptime inquiry
            elif re.search(r'\b(uptime|system\s+status|health|cpu\s+usage)\b', task_lower) and not re.search(r'\b(write|script|code|program)\b', task_lower):
                uptime_data = system_tools.get_uptime()
                all_tools_used.append({"tool": "get_uptime"})
                section = (
                    f"### {idx}. System Uptime\n"
                    f"- **Uptime:** {uptime_data['uptime_formatted']}"
                )
                sections.append(section)

            # 3. Math calculation (percentage or arithmetic)
            elif re.search(r'\b(?:calculate|compute|what\s+is|math)\b.*\d|\d+.*\b(?:multiplied\s+by|times|divided\s+by|plus|minus|percent\s+of|%)\b', task_lower):
                # Clean math string
                math_query = re.sub(r'^(?:calculate|compute|what\s+is|find)\s+', '', task, flags=re.I).strip()
                res = calculator_tools.calculate(math_query)
                all_tools_used.append({"tool": "calculate"})
                if res.get("success"):
                    section = (
                        f"### {idx}. Calculation\n"
                        f"- **{math_query}** = **{res['result']}**"
                    )
                else:
                    section = (
                        f"### {idx}. Calculation\n"
                        f"- Error: {res.get('error', 'Unable to evaluate expression')}"
                    )
                sections.append(section)

            # 4. Programming / AI code generation / Open-ended reasoning
            else:
                provider = brain._get_provider()
                if provider:
                    ai_prompt = (
                        f"Provide a clear, complete, and correct response to: {task}. "
                        "Include full executable code and docstrings where applicable."
                    )
                    gen_result = provider.generate(
                        messages=[{"role": "user", "content": ai_prompt}],
                        system="You are JARVIS. Write clean, complete, robust code or technical explanations with full markdown."
                    )
                    ai_text = gen_result.get("text", "").strip()
                    title = "Code Implementation" if "def " in ai_text or "```" in ai_text else "Response"
                    section = f"### {idx}. {title}\n{ai_text}"
                    sections.append(section)
                    all_tools_used.append({"tool": "llm_code_generation", "model": gen_result.get("model")})
                else:
                    sections.append(f"### {idx}. Task: {task}\nAI provider unavailable for code generation.")

        unified_response = "\n\n".join(sections)
        return {
            "response": unified_response,
            "provider": "compound_orchestrator",
            "model": "hybrid_multi_task_agent",
            "tools_used": all_tools_used,
            "subtasks_count": len(subtasks),
        }
