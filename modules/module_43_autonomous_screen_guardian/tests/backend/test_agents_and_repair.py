"""Tests 10-12, 14-18: Coding agent discovery, banned CLI flags, approval gate,
real disposable buggy Python repo repair + focused unittest verification,
honest unfixable outcome reporting, live repair cancellation, and protected path rejection.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

from modules.module_43_autonomous_screen_guardian.backend.adapters.coding_agents import discover_cli_agents, validate_cli_args
from modules.module_43_autonomous_screen_guardian.backend.app.config import ScreenGuardianConfig
from modules.module_43_autonomous_screen_guardian.backend.services.guardian_service import ScreenGuardianService
from modules.module_43_autonomous_screen_guardian.backend.services.repair_engine import RepairEngineError


class TestAgentsAndRepair(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="m43_test_rep_")
        self.tmp_path = Path(self._tmp.name)
        self.repo_dir = self.tmp_path / "buggy_repo"
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        (self.repo_dir / "tests").mkdir(parents=True, exist_ok=True)

        self.untrusted_dir = self.tmp_path / "untrusted_repo"
        self.untrusted_dir.mkdir(parents=True, exist_ok=True)

        self.config = ScreenGuardianConfig(
            db_path=str(self.tmp_path / "data" / "guardian.db"),
            trusted_workspaces=[str(self.repo_dir.resolve())],
        )
        self.service = ScreenGuardianService(config=self.config)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_10_cli_agent_discovery_reports_honest_availability(self) -> None:
        agents = discover_cli_agents()
        by_id = {a["agent_id"]: a for a in agents}
        self.assertIn("antigravity_cli", by_id)
        self.assertIn("openai_codex_cli", by_id)
        self.assertIn("github_copilot_cli", by_id)
        self.assertIn("reference_local_repair_agent", by_id)
        self.assertTrue(by_id["reference_local_repair_agent"]["available"])
        # Each external agent must honestly report boolean availability and non-empty note
        for aid in ("antigravity_cli", "openai_codex_cli", "github_copilot_cli"):
            self.assertIsInstance(by_id[aid]["available"], bool)
            self.assertTrue(by_id[aid]["note"])

    def test_11_banned_permission_bypass_flags_are_strictly_blocked(self) -> None:
        for flag in ("--dangerously-skip-permissions", "--skip-permissions", "--no-sandbox"):
            with self.assertRaises(PermissionError):
                validate_cli_args(["codex", flag, "fix"])
            with self.assertRaises(PermissionError):
                self.service.repair.create_repair_request(
                    {
                        "workspace_path": str(self.repo_dir),
                        "agent_id": "reference_local_repair_agent",
                        "mode": "assisted_repair",
                        "summary": "Attempt unsafe flag",
                        "test_command": [sys.executable, flag],
                    }
                )

    def test_12_assisted_repair_requires_explicit_approval_before_execution(self) -> None:
        job = self.service.repair.create_repair_request(
            {
                "workspace_path": str(self.repo_dir),
                "agent_id": "reference_local_repair_agent",
                "mode": "assisted_repair",
                "summary": "Fix divide by zero",
                "error_context": "ZeroDivisionError: division by zero",
            }
        )
        self.assertEqual(job["status"], "awaiting_approval")
        self.assertEqual(job["outcome"], "approval_required")

        with self.assertRaises(RepairEngineError) as ctx:
            asyncio.run(self.service.repair.execute_repair(job["repair_id"]))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.code, "APPROVAL_REQUIRED")

        rejected = self.service.repair.approve_repair(job["repair_id"], "reject", reviewer="operator", notes="Not now")
        self.assertEqual(rejected["status"], "cancelled")
        self.assertEqual(rejected["approval_status"], "rejected")

    def test_14_and_15_real_buggy_repo_repaired_and_verified_via_focused_tests(self) -> None:
        # Write real buggy Python code and a real failing unit test
        (self.repo_dir / "math_ops.py").write_text(
            "def divide(a, b):\n    return a / b\n",
            encoding="utf-8",
        )
        (self.repo_dir / "tests" / "test_math_ops.py").write_text(
            "import unittest\n"
            "from math_ops import divide\n\n"
            "class TestMathOps(unittest.TestCase):\n"
            "    def test_divide_zero_returns_zero(self):\n"
            "        self.assertEqual(divide(10, 0), 0.0)\n"
            "    def test_divide_normal(self):\n"
            "        self.assertEqual(divide(10, 2), 5.0)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8",
        )

        # Record a real detected error first
        analysis = asyncio.run(
            self.service.analyze_frame(
                ocr_text_override="Traceback (most recent call last):\n  File 'math_ops.py', line 2\nZeroDivisionError: division by zero",
                source_app="Terminal",
            )
        )
        error_id = analysis["errors"][0]["error_id"]

        # Suggest-fix dry run must NOT modify files
        dry_job = self.service.repair.create_repair_request(
            {
                "error_id": error_id,
                "workspace_path": str(self.repo_dir),
                "agent_id": "reference_local_repair_agent",
                "mode": "suggest_fix",
                "summary": "Preview fix for ZeroDivisionError",
                "error_context": "ZeroDivisionError: division by zero",
            }
        )
        dry_res = asyncio.run(self.service.repair.execute_repair(dry_job["repair_id"], target_files=["math_ops.py"]))
        self.assertEqual(dry_res["outcome"], "approval_required")
        self.assertIn("if b == 0:", dry_res["diff_text"])
        self.assertNotIn("if b == 0:", (self.repo_dir / "math_ops.py").read_text(encoding="utf-8"))

        # Assisted repair -> approve -> execute -> verified_fixed
        job = self.service.repair.create_repair_request(
            {
                "error_id": error_id,
                "workspace_path": str(self.repo_dir),
                "agent_id": "reference_local_repair_agent",
                "mode": "assisted_repair",
                "summary": "Apply and verify ZeroDivisionError fix",
                "error_context": "ZeroDivisionError: division by zero",
            }
        )
        self.service.repair.approve_repair(job["repair_id"], "approve", reviewer="roshan")
        result = asyncio.run(
            self.service.repair.execute_repair(
                job["repair_id"],
                target_files=["math_ops.py"],
                test_command=[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            )
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["outcome"], "verified_fixed")
        self.assertTrue(result["test_results"]["passed"])
        self.assertEqual(result["test_results"]["exit_code"], 0)
        self.assertIn("if b == 0:", result["diff_text"])
        self.assertIn("math_ops.py", result["changed_files"])

        # Linked error must now be resolved ONLY after verification passed
        err_after = self.service.db.get_error(error_id)
        self.assertIsNotNone(err_after)
        self.assertEqual(err_after["status"], "resolved")

    def test_16_unfixable_bug_stays_not_fixed_and_error_unresolved(self) -> None:
        (self.repo_dir / "mystery.py").write_text("def broken():\n    return 1\n", encoding="utf-8")
        (self.repo_dir / "tests" / "test_mystery.py").write_text(
            "import unittest\n"
            "from mystery import broken\n\n"
            "class TestMystery(unittest.TestCase):\n"
            "    def test_impossible(self):\n"
            "        self.assertEqual(broken(), 999)\n",
            encoding="utf-8",
        )
        analysis = asyncio.run(
            self.service.analyze_frame(
                ocr_text_override="AssertionError: 1 != 999 in test_mystery.py",
                source_app="Terminal",
            )
        )
        error_id = analysis["errors"][0]["error_id"]

        job = self.service.repair.create_repair_request(
            {
                "error_id": error_id,
                "workspace_path": str(self.repo_dir),
                "agent_id": "reference_local_repair_agent",
                "mode": "trusted_workspace_autopilot",
                "summary": "Attempt autopilot repair on unfixable bug",
                "error_context": "AssertionError: 1 != 999",
            }
        )
        result = asyncio.run(
            self.service.repair.execute_repair(
                job["repair_id"],
                target_files=["mystery.py"],
                test_command=[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            )
        )
        self.assertEqual(result["outcome"], "not_fixed")
        self.assertFalse(result["test_results"]["passed"])
        err_after = self.service.db.get_error(error_id)
        self.assertIsNotNone(err_after)
        self.assertNotEqual(err_after["status"], "resolved")

    def test_17_live_repair_cancellation_stops_active_subprocess(self) -> None:
        (self.repo_dir / "slow.py").write_text("def ok():\n    return True\n", encoding="utf-8")
        job = self.service.repair.create_repair_request(
            {
                "workspace_path": str(self.repo_dir),
                "agent_id": "reference_local_repair_agent",
                "mode": "trusted_workspace_autopilot",
                "summary": "Long verification command to test cancellation",
                "error_context": "RuntimeError: test cancel",
            }
        )

        async def _run_and_cancel():
            task = self.service.repair.start_background_repair(
                job["repair_id"],
                target_files=["slow.py"],
                test_command=[sys.executable, "-c", "import time; time.sleep(15)"],
            )
            await asyncio.sleep(0.25)
            cancelled = await self.service.repair.cancel_repair(job["repair_id"])
            self.assertTrue(task.done())
            return cancelled

        cancelled = asyncio.run(_run_and_cancel())
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(cancelled["outcome"], "execution_failed")

    def test_18_protected_and_unauthorized_workspaces_rejected_403(self) -> None:
        for bad_path, expected_code in [("/etc", "PROTECTED_PATH_REJECTED"), (str(self.untrusted_dir), "UNAUTHORIZED_WORKSPACE")]:
            with self.assertRaises(RepairEngineError) as ctx:
                self.service.repair.create_repair_request(
                    {
                        "workspace_path": bad_path,
                        "agent_id": "reference_local_repair_agent",
                        "mode": "assisted_repair",
                        "summary": "Should be blocked",
                    }
                )
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertEqual(ctx.exception.code, expected_code)


if __name__ == "__main__":
    unittest.main()
