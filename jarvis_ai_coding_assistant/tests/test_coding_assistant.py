"""Automated tests for JARVIS OS — AI Coding Assistant (unittest & pytest compatible)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_ai_coding_assistant.app import create_app
from jarvis_ai_coding_assistant.config import CodingAssistantConfig


class TestAICodingAssistant(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name) / "jarvis_ws"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.sample_file = self.workspace / "sensor_reader.py"
        self.sample_file.write_text(
            "import yaml\n\n"
            "def read_temp(raw, cache=[]):\n"
            "    try:\n"
            "        data = yaml.load(raw)\n"
            "        if data == None:\n"
            "            return 0.0\n"
            "        return float(data.get('temp', 0.0))\n"
            "    except:\n"
            "        return -1.0\n",
            encoding="utf-8",
        )
        self.db_path = Path(self._tmp.name) / "coding_assistant.db"
        self.config = CodingAssistantConfig(
            workspace_root=self.workspace,
            db_path=self.db_path,
            provider="offline",
            allow_workspace_writes=True,
        )
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_and_ui(self) -> None:
        res = self.client.get("/api/coding-assistant/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["feature"], "AI Coding Assistant")
        self.assertEqual(body["provider"], "offline-local")

        ui = self.client.get("/coding-assistant")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("JARVIS OS — AI CODING ASSISTANT", ui.text)

    def test_workspace_list_read_and_traversal_block(self) -> None:
        res = self.client.get("/api/coding-assistant/workspace/files")
        self.assertEqual(res.status_code, 200)
        paths = [f["path"] for f in res.json()["files"]]
        self.assertIn("sensor_reader.py", paths)

        file_res = self.client.get("/api/coding-assistant/workspace/file", params={"path": "sensor_reader.py"})
        self.assertEqual(file_res.status_code, 200)
        self.assertEqual(file_res.json()["language"], "python")

        blocked = self.client.get("/api/coding-assistant/workspace/file", params={"path": "../../etc/passwd"})
        self.assertEqual(blocked.status_code, 403)

    def test_static_security_analysis_detects_vulnerabilities(self) -> None:
        unsafe_code = (
            'API_KEY = "sk-or-v1-1234567890abcdef1234567890abcdef"\n'
            "import os\n"
            "def run_cmd(user_input, items=[]):\n"
            "    os.system('echo ' + user_input)\n"
            "    return eval(user_input)\n"
        )
        res = self.client.post(
            "/api/coding-assistant/analyze",
            json={"code": unsafe_code, "language": "python"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        rule_ids = {f["rule_id"] for f in body["findings"]}
        self.assertIn("SEC-001", rule_ids)
        self.assertIn("SEC-003", rule_ids)
        self.assertIn("SEC-004", rule_ids)
        self.assertIn("QUAL-002", rule_ids)
        self.assertLess(body["score"], 50)

    def test_generate_code_offline_scaffold(self) -> None:
        res = self.client.post(
            "/api/coding-assistant/generate",
            json={"prompt": "Read Raspberry Pi 5 CPU temperature", "language": "python"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["provider_used"], "offline-local")
        self.assertIn("def ", body["code"])
        self.assertIsNotNone(body["manual_prompt_fallback"])

    def test_refactor_and_safe_patch_apply(self) -> None:
        res = self.client.post(
            "/api/coding-assistant/refactor",
            json={"file_path": "sensor_reader.py", "goal": "Fix bare except and unsafe yaml.load"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("yaml.safe_load", body["refactored_code"])
        self.assertIn("except Exception as exc:", body["refactored_code"])
        self.assertIn("is None", body["refactored_code"])
        self.assertIn("-        data = yaml.load(raw)", body["unified_diff"])

        # Dry-run should not modify file
        dry = self.client.post(
            "/api/coding-assistant/workspace/apply",
            json={"file_path": "sensor_reader.py", "new_content": body["refactored_code"], "dry_run": True},
        )
        self.assertEqual(dry.status_code, 200)
        self.assertFalse(dry.json()["applied"])
        self.assertIn("yaml.load(raw)", self.sample_file.read_text(encoding="utf-8"))

        # Live apply should write file and create a backup
        applied = self.client.post(
            "/api/coding-assistant/workspace/apply",
            json={"file_path": "sensor_reader.py", "new_content": body["refactored_code"], "dry_run": False},
        )
        self.assertEqual(applied.status_code, 200)
        self.assertTrue(applied.json()["applied"])
        self.assertIsNotNone(applied.json()["backup_path"])
        self.assertIn("yaml.safe_load", self.sample_file.read_text(encoding="utf-8"))

    def test_synthesize_tests_and_history(self) -> None:
        res = self.client.post(
            "/api/coding-assistant/tests/synthesize",
            json={"file_path": "sensor_reader.py", "framework": "pytest"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("read_temp", body["discovered_symbols"])
        self.assertIn("def test_read_temp_happy_path", body["test_code"])

        hist = self.client.get("/api/coding-assistant/history")
        self.assertEqual(hist.status_code, 200)
        self.assertGreaterEqual(hist.json()["total"], 1)


if __name__ == "__main__":
    unittest.main()
