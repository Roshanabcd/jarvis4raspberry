"""Backend unit tests for ComputerAssistantEngine (Module 19)."""

from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from backend.app.config import ComputerAssistantConfig
from backend.services.assistant_engine import AssistantError, ComputerAssistantEngine


class TestComputerAssistantEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = ComputerAssistantConfig(
            db_path=str(Path(self._tmp.name) / "m19.db"),
            sandbox_dir=str(Path(self._tmp.name) / "sandbox"),
        )
        self.eng = ComputerAssistantEngine(config=cfg)

    def tearDown(self) -> None:
        self.eng.db.close()
        self._tmp.cleanup()

    def test_discover_apps_select_window_and_capture_png_screenshot(self) -> None:
        apps = self.eng.submit_action("discover_apps", {})
        self.assertEqual(apps["status"], "executed")
        self.assertGreaterEqual(len(apps["result"]["apps"]), 4)

        sel = self.eng.submit_action("select_window", {"window_id": "win-02"})
        self.assertEqual(sel["result"]["focused_window"]["window_id"], "win-02")

        shot_act = self.eng.submit_action("capture_screenshot", {})
        self.assertEqual(shot_act["status"], "executed")
        shot = self.eng.db.get_screenshot(shot_act["result"]["screenshot_id"])
        assert shot is not None
        raw = base64.b64decode(shot["image_b64"])
        self.assertTrue(raw.startswith(b"\x89PNG"), "Screenshot must be valid PNG bytes")

    def test_high_risk_approval_gate_and_sandboxed_file_io(self) -> None:
        pending = self.eng.submit_action("file_write", {"path": "sub/test.txt", "content": "JARVIS M19"})
        self.assertEqual(pending["status"], "awaiting_approval")
        apr_id = pending["approval"]["approval_id"]

        res = self.eng.decide_approval(apr_id, approved=True, decided_by="roshan")
        self.assertEqual(res["action"]["status"], "executed")

        read_act = self.eng.submit_action("file_read", {"path": "sub/test.txt"})
        self.assertEqual(read_act["result"]["content"], "JARVIS M19")

    def test_path_traversal_strictly_blocked(self) -> None:
        with self.assertRaises(AssistantError) as ctx:
            self.eng.submit_action("file_read", {"path": "../../etc/passwd"}, dry_run=True)
        self.assertEqual(ctx.exception.code, "PATH_TRAVERSAL_BLOCKED")

    def test_estop_blocks_all_actions_until_reset(self) -> None:
        self.eng.engage_estop("Safety drill", triggered_by="roshan")
        with self.assertRaises(AssistantError) as ctx:
            self.eng.submit_action("discover_apps", {})
        self.assertEqual(ctx.exception.code, "ESTOP_ACTIVE")

        self.eng.reset_estop("roshan")
        ok = self.eng.submit_action("discover_apps", {})
        self.assertEqual(ok["status"], "executed")

    def test_dry_run_mode_and_replay(self) -> None:
        self.eng.set_dry_run(True)
        dr = self.eng.submit_action("launch_app", {"app_id": "notes-pad"})
        self.assertEqual(dr["status"], "dry_run")
        self.assertTrue(dr["result"]["requires_approval_in_live_run"])

        self.eng.set_dry_run(False)
        click = self.eng.submit_action("mouse_click", {"x": 200, "y": 150})
        rep = self.eng.replay_actions([click["action_id"]], dry_run=True)
        self.assertEqual(rep["replayed_count"], 1)
        self.assertEqual(rep["actions"][0]["replayed_from"], click["action_id"])

    def test_permission_policy_enforcement(self) -> None:
        self.eng.update_policy({"allow_screenshot": False})
        with self.assertRaises(AssistantError) as ctx:
            self.eng.submit_action("capture_screenshot", {})
        self.assertEqual(ctx.exception.code, "PERMISSION_DENIED")


if __name__ == "__main__":
    unittest.main()
