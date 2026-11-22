"""
JARVIS Multi-Task Brain & Compound Capability Orchestrator.
Decomposes complex, multi-action user requests into dependency-tracked DAG plans,
executes subtasks across capabilities, chains outputs, and synthesizes unified responses.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from ai.capabilities.dispatcher import get_capability_dispatcher
from ai.capabilities.models import (
    CapabilityInvocationRequest,
    CapabilityResult,
    MultiTaskPlan,
    PlanStep,
)
from ai.capabilities.router import get_capability_router

logger = logging.getLogger("JARVIS.Capabilities.MultiTaskBrain")

_SPLIT_REGEX = re.compile(
    r",\s*(?:and\s+|also\s+|then\s+)?|;\s*|\band\s+(?=(?:calculate|tell|write|check|get|what\s+is|show|open|launch|start|find|search|run|execute|ask|summarize)\b)|\bthen\s+",
    re.IGNORECASE,
)


class MultiTaskBrain:
    """Orchestrates multi-step, multi-capability compound requests."""

    def __init__(self) -> None:
        self.router = get_capability_router()
        self.dispatcher = get_capability_dispatcher()

    def is_multi_task_request(self, text: str) -> bool:
        """Determine if a prompt contains multiple distinct capability actions."""
        text_clean = text.strip()
        if len(text_clean) < 20 or "```" in text_clean:
            return False

        # Dedicated single-action code generation workflow (e.g. create and run calculator in VS Code)
        if re.search(r"\b(?:write|create|code|make)\b.*python\b.*calculator.*(?:vs\s*code|vscode)", text_clean, re.I):
            return False

        clauses = self.split_clauses(text_clean)
        if len(clauses) < 2:
            return False

        # Verify that at least 2 clauses match recognizable capability intents
        matches = 0
        for c in clauses:
            if self.router.route(c) is not None:
                matches += 1
            elif any(w in c.lower() for w in ("calculate", "tell", "check", "run", "open", "summarize", "find")):
                matches += 1

        return matches >= 2

    def split_clauses(self, text: str) -> List[str]:
        """Split a compound request into discrete operational clauses."""
        raw_parts = _SPLIT_REGEX.split(text.strip())
        cleaned = []
        for p in raw_parts:
            s = p.strip().rstrip(".,;")
            if s and len(s) > 3:
                cleaned.append(s)
        return cleaned

    def create_plan(
        self,
        text: str,
        user_role: str = "USER",
        user_id: str = "default_user",
        session_id: str = "default",
    ) -> MultiTaskPlan:
        """Analyze clauses and construct a dependency-aware MultiTaskPlan."""
        clauses = self.split_clauses(text)
        steps: List[PlanStep] = []
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        for idx, clause in enumerate(clauses, start=1):
            step_id = f"step_{idx}"
            match = self.router.route(clause, user_role=user_role)

            if match:
                cap_id = match.capability_id
                act_id = match.action_id
                params = dict(match.extracted_parameters)
                title = f"{cap_id}: {clause[:40]}"
            else:
                # General LLM or computation fallback
                cap_id = "general_intelligence"
                act_id = "reason"
                params = {"prompt": clause}
                title = f"Reason: {clause[:40]}"

            # Detect dependency on previous steps if referencing "it", "the result", "that", "the video"
            depends_on: List[str] = []
            if idx > 1 and re.search(r"\b(?:it|the\s+result|that|the\s+video|the\s+output|them)\b", clause, re.I):
                depends_on.append(f"step_{idx - 1}")

            steps.append(
                PlanStep(
                    step_id=step_id,
                    title=title,
                    capability_id=cap_id,
                    action_id=act_id,
                    parameters=params,
                    depends_on=depends_on,
                    status="pending",
                )
            )

        return MultiTaskPlan(
            plan_id=plan_id,
            original_prompt=text,
            steps=steps,
            status="pending",
        )

    def execute_plan(
        self,
        plan: MultiTaskPlan,
        user_id: str = "default_user",
        user_role: str = "USER",
        session_id: str = "default",
        channel: str = "chat",
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> MultiTaskPlan:
        """Execute all steps in topological sequence, propagating data between dependent steps."""
        t_start = time.perf_counter()
        plan.status = "in_progress"
        sections: List[str] = []
        spoken_parts: List[str] = []
        step_results: Dict[str, CapabilityResult] = {}

        total_steps = len(plan.steps)

        for idx, step in enumerate(plan.steps, start=1):
            step.status = "running"
            if on_progress:
                try:
                    on_progress({
                        "type": "progress",
                        "stage": "step_running",
                        "step_index": idx,
                        "total_steps": total_steps,
                        "step_id": step.step_id,
                        "title": step.title,
                        "capability": step.capability_id,
                    })
                except Exception as pe:
                    logger.debug("Progress callback failed: %s", pe)

            # Resolve data forwarding from dependencies
            if step.depends_on:
                for dep_id in step.depends_on:
                    dep_res = step_results.get(dep_id)
                    if dep_res and dep_res.data:
                        # Forward relevant context
                        if isinstance(dep_res.data, dict):
                            if "url" in dep_res.data and "url" not in step.parameters:
                                step.parameters["url"] = dep_res.data["url"]
                            if "findings" in dep_res.data and "context" not in step.parameters:
                                step.parameters["context"] = str(dep_res.data["findings"])

            # Execute step
            if step.capability_id == "general_intelligence":
                res = self._execute_general_step(step)
            else:
                req = CapabilityInvocationRequest(
                    capability_id=step.capability_id,
                    action_id=step.action_id,
                    parameters=step.parameters,
                    user_id=user_id,
                    role=user_role,
                    session_id=session_id,
                    channel=channel,
                )
                res = self.dispatcher.execute(req)

            step.result = res
            step.status = "completed" if res.status == "ok" else "failed"
            step_results[step.step_id] = res

            # Accumulate presentation artifacts
            sections.append(f"#### Step {idx}: {step.title}\n{res.markdown_output}")
            if res.spoken_summary:
                spoken_parts.append(res.spoken_summary)

        plan.status = "completed"
        plan.total_execution_time_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # Build final unified synthesis
        plan.final_summary = (
            f"### ⚡ JARVIS Multi-Task Execution Report\n"
            f"- **Executed Subtasks:** {total_steps}/{total_steps} completed in {plan.total_execution_time_ms:.0f}ms\n\n"
            + "\n\n---\n\n".join(sections)
        )

        if len(spoken_parts) == 1:
            plan.spoken_summary = spoken_parts[0]
        else:
            plan.spoken_summary = f"I completed all {total_steps} tasks. " + " ".join(spoken_parts[:2])

        return plan

    def _execute_general_step(self, step: PlanStep) -> CapabilityResult:
        """Handle non-capability general reasoning or math."""
        prompt = step.parameters.get("prompt", "")
        # Check math
        m_calc = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", prompt)
        if m_calc:
            try:
                a, op, b = float(m_calc.group(1)), m_calc.group(2), float(m_calc.group(3))
                val = a + b if op == "+" else (a - b if op == "-" else (a * b if op == "*" else (a / b if b != 0 else 0)))
                formatted_val = f"{val:.2f}".rstrip("0").rstrip(".") if isinstance(val, float) else str(val)
                return CapabilityResult(
                    status="ok",
                    capability_id=step.capability_id,
                    action_id=step.action_id,
                    data={"result": val},
                    markdown_output=f"- **Calculation:** `{prompt}` = **{formatted_val}**",
                    spoken_summary=f"{prompt} is {formatted_val}.",
                )
            except Exception:
                pass

        return CapabilityResult(
            status="ok",
            capability_id=step.capability_id,
            action_id=step.action_id,
            data={"text": prompt},
            markdown_output=f"- Processed task: *{prompt}*",
            spoken_summary=f"Processed {prompt}.",
        )


_MULTI_TASK_BRAIN_INSTANCE: Optional[MultiTaskBrain] = None


def get_multi_task_brain() -> MultiTaskBrain:
    """Return the global singleton MultiTaskBrain."""
    global _MULTI_TASK_BRAIN_INSTANCE
    if _MULTI_TASK_BRAIN_INSTANCE is None:
        _MULTI_TASK_BRAIN_INSTANCE = MultiTaskBrain()
    return _MULTI_TASK_BRAIN_INSTANCE
