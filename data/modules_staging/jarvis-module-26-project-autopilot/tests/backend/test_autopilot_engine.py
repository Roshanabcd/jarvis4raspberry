"""Unit tests for ProjectAutopilotEngine (Module 26)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend.app.config import ProjectAutopilotConfig
from backend.services.autopilot_engine import AutopilotError, ProjectAutopilotEngine


class TestProjectAutopilotEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ProjectAutopilotConfig(
            db_path=os.path.join(self._tmp.name, "test_m26.db"),
            workspace_root=os.path.join(self._tmp.name, "workspaces"),
        )
        self.engine = ProjectAutopilotEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_auto_plan_dependency_execution_and_approval_gate(self) -> None:
        bundle = self.engine.create_project(
            {
                "name": "JARVIS Telemetry",
                "goal": "Build edge telemetry collector with health alerts.",
                "tech_stack": ["Python", "FastAPI"],
                "dry_run": True,
                "auto_plan": True,
            }
        )
        pid = bundle["project"]["project_id"]
        self.assertEqual(len(bundle["milestones"]), 3)
        self.assertEqual(len(bundle["tasks"]), 5)

        # Advance up to 10 steps — should execute first 4 tasks and pause on release_gate
        step1 = self.engine.advance_project(pid, max_steps=10)
        self.assertEqual(step1["executed_count"], 4)
        self.assertEqual(len(step1["paused_for_approval"]), 1)
        self.assertEqual(step1["project"]["status"], "awaiting_approval")

        gated_task_id = step1["paused_for_approval"][0]["task_id"]
        approved = self.engine.decide_approval(gated_task_id, "approve", reviewer="roshan", note="LGTM")
        self.assertEqual(approved["status"], "approved")

        step2 = self.engine.advance_project(pid, max_steps=5)
        self.assertEqual(step2["executed_count"], 1)
        self.assertEqual(step2["progress_pct"], 100.0)
        self.assertEqual(step2["project"]["status"], "completed")

    def test_scaffold_workspace_and_blueprint_export(self) -> None:
        bundle = self.engine.create_project(
            {
                "name": "../Unsafe/../Demo App",
                "goal": "Verify slug sanitization and safe workspace scaffolding.",
                "tech_stack": ["Python"],
                "auto_plan": True,
            }
        )
        pid = bundle["project"]["project_id"]
        scaf = self.engine.scaffold_workspace(pid, include_tests=True)
        ws_path = Path(scaf["workspace_path"]).resolve()
        root_path = Path(self.engine.config.workspace_root).resolve()
        self.assertIn(root_path, ws_path.parents)
        self.assertTrue((ws_path / "README.md").is_file())
        self.assertTrue((ws_path / "src" / "main.py").is_file())
        self.assertTrue((ws_path / "tests" / "test_smoke.py").is_file())

        md = self.engine.export_blueprint_markdown(pid)
        self.assertIn("# Project Autopilot Blueprint:", md)
        self.assertIn("[APPROVAL GATE]", md)

    def test_missing_project_raises_404(self) -> None:
        with self.assertRaises(AutopilotError) as ctx:
            self.engine.advance_project("prj_missing")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
