"""Project Autopilot Engine (Module 26).

Provides:
- Autonomous goal-to-milestone/task plan decomposition
- Dependency-graph enforcement (tasks only run once all upstream dependencies complete)
- Human-in-the-loop approval checkpoints for gated/high-impact tasks
- Dry-run vs. live local execution modes with structured execution logs
- Safe sandboxed starter project scaffolding confined inside WORKSPACE_ROOT
- Shareable Markdown project blueprint export
"""

from __future__ import annotations

import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.adapters.planner_adapter import LocalProjectPlannerAdapter, ProjectPlannerAdapter
from backend.app.config import ProjectAutopilotConfig
from backend.models.database import ProjectAutopilotDB, utc_now_iso


class AutopilotError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug[:60] or "project"


class ProjectAutopilotEngine:
    def __init__(
        self,
        config: Optional[ProjectAutopilotConfig] = None,
        db: Optional[ProjectAutopilotDB] = None,
        adapter: Optional[ProjectPlannerAdapter] = None,
    ) -> None:
        self.config = config or ProjectAutopilotConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or ProjectAutopilotDB(self.config.db_path)
        self.adapter = adapter or LocalProjectPlannerAdapter()
        self._started_at = time.monotonic()

    def _require_project(self, project_id: str) -> Dict[str, Any]:
        proj = self.db.get_project(project_id)
        if not proj:
            raise AutopilotError("PROJECT_NOT_FOUND", f"Project '{project_id}' not found.", 404)
        return proj

    def _require_task(self, task_id: str) -> Dict[str, Any]:
        task = self.db.get_task(task_id)
        if not task:
            raise AutopilotError("TASK_NOT_FOUND", f"Task '{task_id}' not found.", 404)
        return task

    def _log(self, project_id: str, level: str, message: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        return self.db.add_log(f"log_{uuid.uuid4().hex[:10]}", project_id, level, message, task_id=task_id)

    def create_project(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        project_id = f"prj_{uuid.uuid4().hex[:10]}"
        proj = self.db.create_project(
            {
                "project_id": project_id,
                "name": payload["name"].strip(),
                "slug": _slugify(payload["name"]),
                "goal": payload["goal"].strip(),
                "tech_stack": list(payload.get("tech_stack") or ["Python", "FastAPI"]),
                "dry_run": bool(payload.get("dry_run", True)),
                "status": "planned",
                "workspace_path": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._log(project_id, "INFO", f"Project '{proj['name']}' initialized (dry_run={proj['dry_run']}).")

        if payload.get("auto_plan", True):
            self.generate_plan(project_id)
        return self.get_project_bundle(project_id)

    def generate_plan(self, project_id: str) -> Dict[str, Any]:
        proj = self._require_project(project_id)
        blueprint = self.adapter.decompose_project(proj["name"], proj["goal"], proj["tech_stack"])
        key_to_task_id: Dict[str, str] = {}
        now = utc_now_iso()

        existing_count = len(self.db.list_milestones(project_id))
        for idx, ms in enumerate(blueprint, start=existing_count + 1):
            ms_id = f"ms_{uuid.uuid4().hex[:10]}"
            self.db.create_milestone(
                {
                    "milestone_id": ms_id,
                    "project_id": project_id,
                    "order_index": idx,
                    "title": ms["title"],
                    "objective": ms["objective"],
                    "status": "pending",
                    "created_at": now,
                }
            )
            for t in ms["tasks"]:
                tid = f"tsk_{uuid.uuid4().hex[:10]}"
                key_to_task_id[t["key"]] = tid
                deps = [key_to_task_id[k] for k in t.get("depends_on_keys", []) if k in key_to_task_id]
                req_appr = bool(t.get("requires_approval", False))
                self.db.create_task(
                    {
                        "task_id": tid,
                        "project_id": project_id,
                        "milestone_id": ms_id,
                        "title": t["title"],
                        "description": t.get("description", ""),
                        "depends_on": deps,
                        "requires_approval": req_appr,
                        "approval_status": "pending_approval" if req_appr else "not_required",
                        "status": "pending",
                        "estimated_minutes": int(t.get("estimated_minutes", 30)),
                        "output_summary": None,
                        "created_at": now,
                        "updated_at": now,
                    }
                )

        self._log(project_id, "INFO", f"Generated {len(blueprint)} milestones via {self.adapter.adapter_name}.")
        return self.get_project_bundle(project_id)

    def add_task(self, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._require_project(project_id)
        ms_ids = {m["milestone_id"] for m in self.db.list_milestones(project_id)}
        if payload["milestone_id"] not in ms_ids:
            raise AutopilotError("MILESTONE_NOT_FOUND", f"Milestone '{payload['milestone_id']}' not found in project.", 404)
        now = utc_now_iso()
        req_appr = bool(payload.get("requires_approval", False))
        task = self.db.create_task(
            {
                "task_id": f"tsk_{uuid.uuid4().hex[:10]}",
                "project_id": project_id,
                "milestone_id": payload["milestone_id"],
                "title": payload["title"].strip(),
                "description": payload.get("description", "").strip(),
                "depends_on": list(payload.get("depends_on", [])),
                "requires_approval": req_appr,
                "approval_status": "pending_approval" if req_appr else "not_required",
                "status": "pending",
                "estimated_minutes": int(payload.get("estimated_minutes", 30)),
                "output_summary": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._log(project_id, "INFO", f"Added custom task '{task['title']}'.", task_id=task["task_id"])
        return task

    def _sync_statuses(self, project_id: str) -> None:
        milestones = self.db.list_milestones(project_id)
        tasks = self.db.list_tasks(project_id=project_id)
        by_ms: Dict[str, List[Dict[str, Any]]] = {}
        for t in tasks:
            by_ms.setdefault(t["milestone_id"], []).append(t)

        for ms in milestones:
            ms_tasks = by_ms.get(ms["milestone_id"], [])
            if not ms_tasks:
                continue
            if all(t["status"] == "completed" for t in ms_tasks):
                self.db.update_milestone_status(ms["milestone_id"], "completed")
            elif any(t["status"] in ("completed", "awaiting_approval", "running") for t in ms_tasks):
                self.db.update_milestone_status(ms["milestone_id"], "in_progress")

        if tasks and all(t["status"] == "completed" for t in tasks):
            self.db.update_project(project_id, status="completed")
        elif any(t["status"] == "awaiting_approval" for t in tasks):
            self.db.update_project(project_id, status="awaiting_approval")
        elif any(t["status"] == "completed" for t in tasks):
            self.db.update_project(project_id, status="in_progress")

    def advance_project(self, project_id: str, max_steps: int = 3, dry_run: Optional[bool] = None) -> Dict[str, Any]:
        proj = self._require_project(project_id)
        effective_dry_run = proj["dry_run"] if dry_run is None else dry_run
        executed: List[Dict[str, Any]] = []
        paused_for_approval: List[Dict[str, Any]] = []

        for _ in range(max_steps):
            tasks = self.db.list_tasks(project_id=project_id)
            completed_ids = {t["task_id"] for t in tasks if t["status"] == "completed"}

            ready = [
                t
                for t in tasks
                if t["status"] in ("pending", "approved")
                and all(dep in completed_ids for dep in t["depends_on"])
            ]
            if not ready:
                break

            task = ready[0]
            if task["requires_approval"] and task["approval_status"] != "approved":
                updated = self.db.update_task(
                    task["task_id"],
                    status="awaiting_approval",
                    approval_status="pending_approval",
                    output_summary="Paused at human approval checkpoint.",
                )
                self._log(
                    project_id,
                    "WARN",
                    f"Task '{task['title']}' paused awaiting human approval.",
                    task_id=task["task_id"],
                )
                paused_for_approval.append(updated)  # type: ignore[arg-type]
                break

            summary = self.adapter.execute_task(proj, task, dry_run=effective_dry_run)
            updated = self.db.update_task(task["task_id"], status="completed", output_summary=summary)
            self._log(project_id, "INFO", summary, task_id=task["task_id"])
            executed.append(updated)  # type: ignore[arg-type]

        self._sync_statuses(project_id)
        return {
            "project": self.db.get_project(project_id),
            "executed_count": len(executed),
            "executed_tasks": executed,
            "paused_for_approval": paused_for_approval,
            "progress_pct": self.compute_progress_pct(project_id),
        }

    def decide_approval(self, task_id: str, decision: str, reviewer: str = "operator", note: str = "") -> Dict[str, Any]:
        task = self._require_task(task_id)
        if not task["requires_approval"]:
            raise AutopilotError("APPROVAL_NOT_REQUIRED", f"Task '{task_id}' does not require approval.", 400)

        if decision == "approve":
            updated = self.db.update_task(
                task_id,
                status="approved",
                approval_status="approved",
                output_summary=f"Approved by {reviewer}." + (f" Note: {note}" if note else ""),
            )
            self._log(task["project_id"], "INFO", f"Task '{task['title']}' approved by {reviewer}.", task_id=task_id)
        else:
            updated = self.db.update_task(
                task_id,
                status="rejected",
                approval_status="rejected",
                output_summary=f"Rejected by {reviewer}." + (f" Note: {note}" if note else ""),
            )
            self._log(task["project_id"], "WARN", f"Task '{task['title']}' rejected by {reviewer}.", task_id=task_id)

        self._sync_statuses(task["project_id"])
        return updated  # type: ignore[return-value]

    def scaffold_workspace(self, project_id: str, include_tests: bool = True) -> Dict[str, Any]:
        proj = self._require_project(project_id)
        root = Path(self.config.workspace_root).resolve()
        target = (root / f"{proj['slug']}_{proj['project_id'][-6:]}").resolve()
        if root not in target.parents:
            raise AutopilotError("INVALID_WORKSPACE_PATH", "Resolved workspace escapes sandbox root.", 400)

        target.mkdir(parents=True, exist_ok=True)
        (target / "src").mkdir(exist_ok=True)
        created_files: List[str] = []

        readme = target / "README.md"
        readme.write_text(
            f"# {proj['name']}\n\n**Goal**: {proj['goal']}\n\n**Tech Stack**: {', '.join(proj['tech_stack'])}\n",
            encoding="utf-8",
        )
        created_files.append("README.md")

        main_py = target / "src" / "main.py"
        main_py.write_text(
            f'"""Starter entrypoint scaffolded by JARVIS Module 26 — Project Autopilot."""\n\n'
            f'def main() -> str:\n    return "Project {proj["name"]} initialized."\n\n'
            f'if __name__ == "__main__":\n    print(main())\n',
            encoding="utf-8",
        )
        created_files.append("src/main.py")

        if include_tests:
            (target / "tests").mkdir(exist_ok=True)
            test_py = target / "tests" / "test_smoke.py"
            test_py.write_text(
                'import unittest\nfrom src.main import main\n\n'
                'class TestSmoke(unittest.TestCase):\n'
                '    def test_main(self):\n'
                '        self.assertIn("initialized", main())\n',
                encoding="utf-8",
            )
            created_files.append("tests/test_smoke.py")

        self.db.update_project(project_id, workspace_path=str(target))
        self._log(project_id, "INFO", f"Scaffolded {len(created_files)} starter files in sandbox workspace.")
        return {"project_id": project_id, "workspace_path": str(target), "created_files": created_files}

    def compute_progress_pct(self, project_id: str) -> float:
        tasks = self.db.list_tasks(project_id=project_id)
        if not tasks:
            return 0.0
        done = sum(1 for t in tasks if t["status"] == "completed")
        return round((done / len(tasks)) * 100.0, 1)

    def get_project_bundle(self, project_id: str) -> Dict[str, Any]:
        proj = self._require_project(project_id)
        milestones = self.db.list_milestones(project_id)
        tasks = self.db.list_tasks(project_id=project_id)
        logs = self.db.list_logs(project_id, limit=40)
        return {
            "project": proj,
            "progress_pct": self.compute_progress_pct(project_id),
            "milestones": milestones,
            "tasks": tasks,
            "logs": logs,
        }

    def export_blueprint_markdown(self, project_id: str) -> str:
        bundle = self.get_project_bundle(project_id)
        proj = bundle["project"]
        tasks_by_ms: Dict[str, List[Dict[str, Any]]] = {}
        for t in bundle["tasks"]:
            tasks_by_ms.setdefault(t["milestone_id"], []).append(t)

        lines = [
            f"# Project Autopilot Blueprint: {proj['name']}",
            f"- **Project ID**: `{proj['project_id']}`",
            f"- **Status**: `{proj['status']}` ({bundle['progress_pct']}% complete)",
            f"- **Tech Stack**: {', '.join(proj['tech_stack'])}",
            f"- **Execution Mode**: {'Dry-Run' if proj['dry_run'] else 'Standard'} (Planner Simulated: `{self.adapter.is_simulated}`)",
            "",
            "## Goal",
            proj["goal"],
            "",
            "## Milestones & Tasks",
        ]
        for ms in bundle["milestones"]:
            lines.append(f"### {ms['title']} (`{ms['status']}`)")
            lines.append(ms["objective"])
            for t in tasks_by_ms.get(ms["milestone_id"], []):
                mark = "x" if t["status"] == "completed" else " "
                gate = " [APPROVAL GATE]" if t["requires_approval"] else ""
                lines.append(f"- [{mark}] **{t['title']}**{gate} — `{t['status']}` ({t['estimated_minutes']}m)")
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def get_status(self) -> Dict[str, Any]:
        projects = self.db.list_projects()
        tasks = self.db.list_tasks()
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "projects_count": len(projects),
            "total_tasks": len(tasks),
            "completed_tasks": sum(1 for t in tasks if t["status"] == "completed"),
            "awaiting_approval_tasks": sum(1 for t in tasks if t["status"] == "awaiting_approval"),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
