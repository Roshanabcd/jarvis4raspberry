"""Comprehensive test suite for JARVIS OS — AI Coding Assistant.

Tests all security rules, static quality rules, AST edge cases, workspace sandboxing,
live HTTP endpoints, test synthesis validity, and mock LLM providers.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

try:
    from jarvis_ai_coding_assistant.analyzer import StaticCodeAnalyzer
    from jarvis_ai_coding_assistant.app import create_app
    from jarvis_ai_coding_assistant.config import CodingAssistantConfig
    from jarvis_ai_coding_assistant.engine import CodingAssistantEngine
    from jarvis_ai_coding_assistant.llm_provider import CodingLLMClient, LLMCompletion
    from jarvis_ai_coding_assistant.models import (
        AnalyzeRequest,
        ApplyPatchRequest,
        GenerateCodeRequest,
        RefactorRequest,
        TestSynthesisRequest,
    )
    from jarvis_ai_coding_assistant.storage import CodingAssistantStore
    from jarvis_ai_coding_assistant.workspace import WorkspaceManager, WorkspaceSecurityError
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from analyzer import StaticCodeAnalyzer  # type: ignore[no-redef]
    from app import create_app  # type: ignore[no-redef]
    from config import CodingAssistantConfig  # type: ignore[no-redef]
    from engine import CodingAssistantEngine  # type: ignore[no-redef]
    from llm_provider import CodingLLMClient, LLMCompletion  # type: ignore[no-redef]
    from models import (  # type: ignore[no-redef]
        AnalyzeRequest,
        ApplyPatchRequest,
        GenerateCodeRequest,
        RefactorRequest,
        TestSynthesisRequest,
    )
    from storage import CodingAssistantStore  # type: ignore[no-redef]
    from workspace import WorkspaceManager, WorkspaceSecurityError  # type: ignore[no-redef]


class TestComprehensiveStaticAnalyzer(unittest.TestCase):
    """Test all static security, syntax, and quality rules in StaticCodeAnalyzer."""

    def setUp(self) -> None:
        self.analyzer = StaticCodeAnalyzer()

    def test_all_security_rules(self) -> None:
        code_samples = {
            "SEC-001": 'API_KEY = "super_secret_token_12345"\n',
            "SEC-002": 'token = "sk-or-v1-abcdef1234567890abcdef1234567890"\n',
            "SEC-003": "x = '1 + 1'\neval(x)\nexec(x)\n",
            "SEC-004": "import os\nos.system('ls')\nos.popen('whoami')\n",
            "SEC-005": "import subprocess\nsubprocess.run('ls', shell=True)\n",
            "SEC-006": "import pickle\npickle.loads(b'data')\n",
            "SEC-007": "import yaml\nyaml.load('key: val')\n",
            "SEC-008": "import hashlib\nhashlib.md5(b'test')\nhashlib.sha1(b'test')\n",
            "SEC-009": "import requests\nrequests.get('https://example.com', verify=False)\n",
            "SEC-010": 'HOST = "0.0.0.0"\n',
            "SEC-011": "def query(db, user):\n    db.execute(f'SELECT * FROM users WHERE name = {user}')\n",
        }

        for expected_rule, sample in code_samples.items():
            score, grade, findings, _ = self.analyzer.analyze(sample, language="python")
            detected_rules = {f.rule_id for f in findings}
            self.assertIn(
                expected_rule,
                detected_rules,
                f"Rule {expected_rule} was not detected in sample:\n{sample}",
            )

    def test_all_quality_and_syntax_rules(self) -> None:
        # SYN-001
        syntax_err = "def broken(\n"
        score, grade, findings, _ = self.analyzer.analyze(syntax_err, language="python")
        self.assertIn("SYN-001", {f.rule_id for f in findings})
        self.assertEqual(grade, "F")

        # QUAL-001: bare except
        bare_except = "try:\n    x = 1\nexcept:\n    pass\n"
        _, _, findings, _ = self.analyzer.analyze(bare_except, language="python")
        self.assertIn("QUAL-001", {f.rule_id for f in findings})

        # QUAL-002: mutable default
        mutable_def = "def add_item(item, items=[]):\n    items.append(item)\n    return items\n"
        _, _, findings, _ = self.analyzer.analyze(mutable_def, language="python")
        self.assertIn("QUAL-002", {f.rule_id for f in findings})

        # QUAL-003: cyclomatic complexity > 10
        complex_code = "def complex_fn(a, b, c, d, e, f, g, h, i, j, k):\n"
        for var in ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"]:
            complex_code += f"    if {var}:\n        pass\n"
        _, _, findings, metrics = self.analyzer.analyze(complex_code, language="python")
        self.assertIn("QUAL-003", {f.rule_id for f in findings})
        self.assertGreater(metrics[0].cyclomatic_complexity, 10)

        # QUAL-004: length > 60 lines
        long_code = "def very_long_fn():\n" + ("    x = 1\n" * 65)
        _, _, findings, metrics = self.analyzer.analyze(long_code, language="python")
        self.assertIn("QUAL-004", {f.rule_id for f in findings})
        self.assertGreater(metrics[0].length_lines, 60)

    def test_javascript_rules(self) -> None:
        js_code = (
            "function dangerous(input) {\n"
            "  eval(input);\n"
            "  document.getElementById('out').innerHTML = input;\n"
            "}\n"
        )
        score, grade, findings, _ = self.analyzer.analyze(js_code, language="javascript")
        detected = {f.rule_id for f in findings}
        self.assertIn("SEC-JS-001", detected)
        self.assertIn("SEC-JS-002", detected)
        self.assertLess(score, 80)


class TestComprehensiveWorkspaceManager(unittest.TestCase):
    """Test workspace sandboxing, directory traversal prevention, and backups."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "workspace"
        self.root.mkdir(parents=True, exist_ok=True)
        self.config = CodingAssistantConfig(
            workspace_root=self.root,
            max_file_bytes=1000,
            allow_workspace_writes=True,
        )
        self.ws = WorkspaceManager(self.config)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sandboxing_path_traversal(self) -> None:
        traversal_attempts = [
            "../outside.txt",
            "../../etc/passwd",
            "/etc/shadow",
            "sub/../../../../secret",
            "",
            "   ",
        ]
        for path in traversal_attempts:
            with self.assertRaises((WorkspaceSecurityError, ValueError)):
                self.ws.resolve_safe_path(path)

    def test_file_size_limit(self) -> None:
        large_file = self.root / "large.txt"
        large_file.write_text("A" * 2000, encoding="utf-8")
        with self.assertRaises(ValueError):
            self.ws.read_file("large.txt")

    def test_patch_apply_to_directory_rejected(self) -> None:
        subdir = self.root / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(ValueError) as ctx:
            self.ws.apply_patch("subdir", "new content", dry_run=False)
        self.assertIn("directory", str(ctx.exception))

    def test_write_permissions_disabled(self) -> None:
        ro_config = CodingAssistantConfig(
            workspace_root=self.root,
            allow_workspace_writes=False,
        )
        ro_ws = WorkspaceManager(ro_config)
        with self.assertRaises(PermissionError):
            ro_ws.apply_patch("test.txt", "content", dry_run=False)


class TestComprehensiveSynthesizedCode(unittest.TestCase):
    """Verify that generated code and synthesized tests are syntactically valid and runnable."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "ws"
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = Path(self._tmp.name) / "test.db"
        self.config = CodingAssistantConfig(workspace_root=self.root, db_path=self.db)
        self.store = CodingAssistantStore(self.db)
        self.ws = WorkspaceManager(self.config)
        self.llm = CodingLLMClient(self.config)
        self.analyzer = StaticCodeAnalyzer()
        self.engine = CodingAssistantEngine(self.config, self.ws, self.store, self.llm, self.analyzer)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_offline_generated_code_compiles(self) -> None:
        req = GenerateCodeRequest(
            prompt="Read system memory metrics and return JSON status",
            language="python",
        )
        resp = self.engine.generate_code_sync(req) if hasattr(self.engine, "generate_code_sync") else None
        # Use offline generation directly
        code, explanation = self.engine._offline_generate_scaffold(req)
        # Verify it compiles as valid Python AST
        tree = ast.parse(code)
        self.assertIsNotNone(tree)
        self.assertIn("def ", code)

        # JavaScript scaffold check
        js_req = GenerateCodeRequest(prompt="Format timestamp", language="javascript")
        js_code, _ = self.engine._offline_generate_scaffold(js_req)
        self.assertIn("export function", js_code)

    def test_synthesized_pytest_runs_and_passes(self) -> None:
        sample_code = (
            "class DeviceManager:\n"
            "    def connect(self):\n"
            "        return True\n\n"
            "def calculate_checksum(data: str) -> int:\n"
            "    return len(data)\n\n"
            "async def fetch_telemetry(sensor_id: int):\n"
            "    return {'id': sensor_id, 'ok': True}\n"
        )
        test_code, notes = self.engine._offline_synthesize_pytest(
            code=sample_code,
            module_import_path="my_devices",
            file_path="devices.py",
            include_edge_cases=True,
        )
        # Verify generated test code parses as valid Python
        tree = ast.parse(test_code)
        self.assertIsNotNone(tree)

        # Test execution: write test code to a temporary file and run pytest on it!
        test_file = self.root / "test_synthesized.py"
        test_file.write_text(test_code, encoding="utf-8")

        import pytest
        result = pytest.main([str(test_file), "-q"])
        self.assertEqual(result, pytest.ExitCode.OK, "Synthesized pytest suite failed to pass!")


class TestComprehensiveEndToEndEndpoints(unittest.TestCase):
    """Full HTTP API test coverage."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "ws"
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = Path(self._tmp.name) / "coding.db"
        self.config = CodingAssistantConfig(
            workspace_root=self.root,
            db_path=self.db,
            provider="offline",
            allow_workspace_writes=True,
        )
        self.app = create_app(self.config)
        self.client = TestClient(self.app)

        # Create dummy workspace files
        (self.root / "main.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
        (self.root / "config.json").write_text('{"debug": true}\n', encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_root_redirect(self) -> None:
        res = self.client.get("/", follow_redirects=False)
        self.assertEqual(res.status_code, 307)
        self.assertEqual(res.headers["location"], "/coding-assistant")

    def test_full_generate_refactor_analyze_pipeline(self) -> None:
        # 1. Generate
        gen_res = self.client.post(
            "/api/coding-assistant/generate",
            json={"prompt": "Calculate battery level from ADC voltage", "language": "python"},
        )
        self.assertEqual(gen_res.status_code, 200)
        gen_data = gen_res.json()
        self.assertIn("def ", gen_data["code"])
        self.assertEqual(gen_data["provider_used"], "offline-local")

        # 2. Analyze
        ana_res = self.client.post(
            "/api/coding-assistant/analyze",
            json={"code": gen_data["code"], "language": "python"},
        )
        self.assertEqual(ana_res.status_code, 200)
        ana_data = ana_res.json()
        self.assertGreaterEqual(ana_data["score"], 80)

        # 3. Apply generated code to a new workspace file
        patch_res = self.client.post(
            "/api/coding-assistant/workspace/apply",
            json={
                "file_path": "battery.py",
                "new_content": gen_data["code"],
                "dry_run": False,
                "create_backup": True,
            },
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertTrue((self.root / "battery.py").exists())

        # 4. Refactor the applied file
        ref_res = self.client.post(
            "/api/coding-assistant/refactor",
            json={"file_path": "battery.py", "goal": "Add documentation and validation"},
        )
        self.assertEqual(ref_res.status_code, 200)

        # 5. Check history audit log
        hist_res = self.client.get("/api/coding-assistant/history")
        self.assertEqual(hist_res.status_code, 200)
        hist = hist_res.json()
        self.assertGreaterEqual(hist["total"], 3)


if __name__ == "__main__":
    unittest.main()
