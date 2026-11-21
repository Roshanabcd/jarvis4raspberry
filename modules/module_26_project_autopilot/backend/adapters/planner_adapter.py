"""Project planner & task execution adapter contract for Module 26."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ProjectPlannerAdapter(ABC):
    adapter_name: str = "abstract_planner"
    is_simulated: bool = True

    @abstractmethod
    def decompose_project(self, name: str, goal: str, tech_stack: List[str]) -> List[Dict[str, Any]]:
        """Return ordered milestones, each containing a list of task blueprints."""

    @abstractmethod
    def execute_task(self, project: Dict[str, Any], task: Dict[str, Any], dry_run: bool) -> str:
        """Execute (or simulate) a single project task and return an execution summary."""


class LocalProjectPlannerAdapter(ProjectPlannerAdapter):
    """Deterministic local planner & runner (no external LLM credentials required)."""

    adapter_name = "local_project_autopilot_planner"
    is_simulated = True

    def decompose_project(self, name: str, goal: str, tech_stack: List[str]) -> List[Dict[str, Any]]:
        stack_str = ", ".join(tech_stack) if tech_stack else "Python"
        return [
            {
                "title": "Milestone 1: Architecture & Workspace Setup",
                "objective": f"Define module boundaries, data schema, and baseline repo structure for {name} ({stack_str}).",
                "tasks": [
                    {
                        "key": "arch_spec",
                        "title": "Draft architecture specification & contracts",
                        "description": f"Specify interfaces and persistence models to satisfy goal: {goal}",
                        "depends_on_keys": [],
                        "requires_approval": False,
                        "estimated_minutes": 25,
                    },
                    {
                        "key": "scaffold_repo",
                        "title": "Initialize repository structure & configuration",
                        "description": f"Create isolated package layout, config loader, and environment templates for {stack_str}.",
                        "depends_on_keys": ["arch_spec"],
                        "requires_approval": False,
                        "estimated_minutes": 20,
                    },
                ],
            },
            {
                "title": "Milestone 2: Core Implementation & Verification",
                "objective": "Implement core services, REST/event interfaces, and automated regression tests.",
                "tasks": [
                    {
                        "key": "core_service",
                        "title": "Implement core service engine & persistence",
                        "description": f"Build deterministic domain logic and storage layer for {name}.",
                        "depends_on_keys": ["scaffold_repo"],
                        "requires_approval": False,
                        "estimated_minutes": 45,
                    },
                    {
                        "key": "auto_tests",
                        "title": "Write & execute automated unit and integration tests",
                        "description": "Validate API contracts, error paths, and persistence durability.",
                        "depends_on_keys": ["core_service"],
                        "requires_approval": False,
                        "estimated_minutes": 30,
                    },
                ],
            },
            {
                "title": "Milestone 3: Release Gate & Deployment",
                "objective": "Review security posture and execute gated production rollout.",
                "tasks": [
                    {
                        "key": "release_gate",
                        "title": "Human-approved release & deployment rollout",
                        "description": "Requires explicit operator approval before publishing build artifacts or deploying.",
                        "depends_on_keys": ["auto_tests"],
                        "requires_approval": True,
                        "estimated_minutes": 15,
                    }
                ],
            },
        ]

    def execute_task(self, project: Dict[str, Any], task: Dict[str, Any], dry_run: bool) -> str:
        mode = "DRY-RUN" if dry_run else "LOCAL-SIMULATED"
        return (
            f"[{mode}] Executed '{task['title']}' for project '{project['name']}' "
            f"(stack: {', '.join(project['tech_stack'])})."
        )
