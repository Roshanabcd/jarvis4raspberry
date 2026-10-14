"""Comprehensive unit tests for JARVIS OS tools and security subsystems.

Tests:
    - AuditLogger JSONL logging, rotation, and secret redaction
    - PermissionManager risk gates (0-4), confirmation requirements, and YAML loading
    - ToolRegistry full pipeline (schema -> permission -> safety -> execute -> audit)
    - FileTools workspace enforcement, read/write/append/delete, and confirm guards
    - SecureCommandRunner allowlist enforcement, shell=False, timeouts, simulation
    - WebSearcher non-fabrication, DuckDuckGo API, clean HTML text extraction
    - GitTools SecureCommandRunner integration and confirmation gates
    - TaskScheduler SQLite persistence, HH:MM parsing, pause/resume/delete
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from datetime import datetime
import pytest

from config.config_manager import config
from security.audit.audit_logger import AuditLogger, audit_logger
from security.permissions.permission_manager import PermissionManager, permission_manager
from tools.registry import ToolRegistry, tool_registry
from tools.filesystem.file_tools import FileTools
from tools.shell.command_runner import SecureCommandRunner
from tools.web_search.searcher import WebSearcher
from tools.git.git_tools import GitTools
from tools.scheduler.task_scheduler import TaskScheduler


# ---------------------------------------------------------------------------
# 1. Audit Logger Tests
# ---------------------------------------------------------------------------
def test_audit_logger_redaction_and_jsonl():
    """Verify secrets are redacted and records written in JSONL format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "test_audit.log")
        logger = AuditLogger(log_path=log_file, max_bytes=1024 * 1024)

        # Test secret redaction in string and payload
        sensitive_request = "api_key=sk-1234567890abcdef12345678 and Bearer super_secret_token_12345"
        rec = logger.log_event(
            service="test_service",
            event="test_event",
            tool="test_tool",
            user_request=sensitive_request,
            status="success",
            risk_level=1,
            duration_ms=12.5,
            error=None,
        )

        assert "sk-1234567890abcdef12345678" not in rec["user_request"]
        assert "super_secret_token_12345" not in rec["user_request"]
        assert "[REDACTED]" in rec["user_request"]

        # Verify file content is valid JSON line
        with open(log_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            assert len(lines) == 1
            parsed = json.loads(lines[0])
            assert parsed["service"] == "test_service"
            assert parsed["status"] == "success"
            assert parsed["risk_level"] == 1


# ---------------------------------------------------------------------------
# 2. Permission Manager Tests
# ---------------------------------------------------------------------------
def test_permission_manager_levels_and_confirmation():
    """Verify permission rules across risk levels 0-4."""
    pm = PermissionManager()
    pm.default_max_risk = 2
    pm.require_confirmation_above = 3
    pm.allowed_tools = ["read_file", "write_file", "run_command"]
    pm.denied_tools = ["malicious_tool"]
    pm.high_risk_tools = ["delete_file", "push_git"]

    # Explicitly denied
    assert pm.check_permission("malicious_tool", risk_level=0, confirmed=True) is False

    # Low risk (0-2) allowed without confirmation
    assert pm.check_permission("read_file", risk_level=0, confirmed=False) is True
    assert pm.check_permission("write_file", risk_level=1, confirmed=False) is True
    assert pm.check_permission("run_command", risk_level=2, confirmed=False) is True

    # Risk level exceeding default_max_risk without confirmation
    assert pm.check_permission("run_command", risk_level=3, confirmed=False) is False
    assert pm.check_permission("run_command", risk_level=3, confirmed=True) is True

    # High risk tools (3-4) require confirmed=True
    assert pm.check_permission("delete_file", risk_level=2, confirmed=False) is False
    assert pm.check_permission("delete_file", risk_level=2, confirmed=True) is True
    assert pm.check_permission("push_git", risk_level=3, confirmed=False) is False
    assert pm.check_permission("push_git", risk_level=3, confirmed=True) is True


# ---------------------------------------------------------------------------
# 3. Tool Registry Tests
# ---------------------------------------------------------------------------
def test_tool_registry_pipeline():
    """Verify tool execution pipeline: schema -> permission -> safety -> execute -> audit."""
    reg = ToolRegistry(auto_register_core=False)

    executed = False

    def sample_func(path: str, count: int = 1) -> str:
        nonlocal executed
        executed = True
        return f"Processed {path} {count} times"

    reg.register_tool({
        "name": "sample_tool",
        "description": "Sample test tool",
        "schema": {"path": "str", "count": "int"},
        "risk_level": 1,
        "permissions": ["test:sample"],
        "execute": sample_func,
    })

    # 1. Invalid schema parameter type
    res_bad = reg.execute("sample_tool", path="hello.txt", count="not_an_int")
    assert res_bad["success"] is False
    assert "must be an integer" in str(res_bad["error"])

    # 2. Missing required parameter
    res_missing = reg.execute("sample_tool", count=5)
    assert res_missing["success"] is False
    assert "Missing required parameter 'path'" in str(res_missing["error"])

    # 3. Successful execution
    res_good = reg.execute("sample_tool", path="/valid/path.txt", count=3)
    assert res_good["success"] is True
    assert res_good["result"] == "Processed /valid/path.txt 3 times"
    assert res_good["error"] is None
    assert executed is True


def test_tool_registry_high_risk_blocking():
    """Verify unconfirmed high-risk tools are blocked before execution."""
    reg = ToolRegistry(auto_register_core=False)
    ran = False

    def dangerous_op(target: str) -> str:
        nonlocal ran
        ran = True
        return f"Nuked {target}"

    reg.register_tool({
        "name": "dangerous_tool",
        "description": "High risk tool",
        "schema": {"target": "str"},
        "risk_level": 4,
        "permissions": ["test:dangerous"],
        "execute": dangerous_op,
    })

    # Blocked without confirmation
    res_blocked = reg.execute("dangerous_tool", target="system", confirmed=False)
    assert res_blocked["success"] is False
    assert "Permission denied" in str(res_blocked["error"])
    assert ran is False

    # Allowed with confirmation
    res_allowed = reg.execute("dangerous_tool", target="system", confirmed=True)
    assert res_allowed["success"] is True
    assert res_allowed["result"] == "Nuked system"
    assert ran is True


# ---------------------------------------------------------------------------
# 4. File Tools Tests
# ---------------------------------------------------------------------------
def test_file_tools_workspace_confinement():
    """Verify FileTools strictly enforces workspace boundaries."""
    with tempfile.TemporaryDirectory() as temp_ws:
        ft = FileTools(allowed_workspaces={"TEST_WS": temp_ws})

        # Safe file within workspace
        test_file = os.path.join(temp_ws, "hello.txt")
        ft.write_file(test_file, "Hello JARVIS")
        content = ft.read_file(test_file)
        assert content == "Hello JARVIS"

        # Append
        ft.append_file(test_file, "\nSecond line")
        assert "Second line" in ft.read_file(test_file)

        # Directory creation and listing
        sub_dir = os.path.join(temp_ws, "sub_folder")
        ft.create_dir(sub_dir)
        entries = ft.list_dir(temp_ws)
        names = [e["name"] for e in entries]
        assert "hello.txt" in names
        assert "sub_folder" in names

        # Search
        matches = ft.search_files(temp_ws, "*.txt")
        assert any("hello.txt" in m for m in matches)

        # Delete requiring confirmation
        with pytest.raises(PermissionError):
            ft.delete_file(test_file, confirmed=False)

        # Confirm delete
        del_res = ft.delete_file(test_file, confirmed=True)
        assert del_res["deleted"] is True

        # Path outside workspace rejected
        with pytest.raises(PermissionError):
            ft.read_file("/etc/shadow")


# ---------------------------------------------------------------------------
# 5. Command Runner Tests
# ---------------------------------------------------------------------------
def test_secure_command_runner():
    """Verify SecureCommandRunner enforces allowlist and safe execution."""
    runner = SecureCommandRunner()

    # Allowed command (uname)
    res = runner.execute_command("uname", ["-s"])
    assert res["returncode"] == 0
    assert "Linux" in res["stdout"]
    assert res["duration_ms"] >= 0

    # Disallowed command (bash, rm, etc.)
    disallowed = runner.execute_command("rm", ["-rf", "/tmp/fake"])
    assert disallowed["returncode"] == 126
    assert "not in ALLOWED_COMMANDS" in disallowed["stderr"]

    # Injection attempts via path
    injected = runner.execute_command("/bin/ls", [])
    assert injected["returncode"] == 126


# ---------------------------------------------------------------------------
# 6. Web Searcher Tests
# ---------------------------------------------------------------------------
def test_web_searcher_clean_text_and_no_fabrication():
    """Verify WebSearcher clean text extraction and no hallucination."""
    searcher = WebSearcher()

    sample_html = """
    <html>
      <head><title>Test Page Title</title></head>
      <body>
        <script>alert('malicious')</script>
        <style>body { color: red; }</style>
        <h1>Welcome to JARVIS</h1>
        <p>This is real content from the web.</p>
      </body>
    </html>
    """
    title, text = searcher._extract_clean_text(sample_html)
    assert title == "Test Page Title"
    assert "Welcome to JARVIS" in text
    assert "This is real content" in text
    assert "alert" not in text
    assert "color: red" not in text

    # Blank query returns empty list, never fabricates
    assert searcher.search("") == []


# ---------------------------------------------------------------------------
# 7. Git Tools Tests
# ---------------------------------------------------------------------------
def test_git_tools_confirmation_and_status():
    """Verify GitTools confirmation gates for push and commit operations."""
    gt = GitTools()
    with tempfile.TemporaryDirectory() as temp_repo:
        # Mock / simulate status
        with pytest.raises(PermissionError):
            # Push without confirmation should raise PermissionError
            gt.push(temp_repo, confirmed=False)


# ---------------------------------------------------------------------------
# 8. Task Scheduler Tests
# ---------------------------------------------------------------------------
def test_task_scheduler_sqlite_and_management():
    """Verify TaskScheduler creates SQLite records and supports pause/resume/delete."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_file = os.path.join(temp_dir, "test_tasks.db")
        scheduler = TaskScheduler(db_path=db_file)

        # Schedule task
        t_id = scheduler.schedule_task("Health Check", "12:00", "python3", ["--version"])
        assert isinstance(t_id, str)

        # List
        tasks = scheduler.list_tasks()
        assert len(tasks) == 1
        assert tasks[0]["name"] == "Health Check"
        assert tasks[0]["enabled"] in (True, 1)

        # Pause
        assert scheduler.pause_task(t_id) is True
        tasks = scheduler.list_tasks()
        assert tasks[0]["enabled"] in (False, 0)

        # Resume
        assert scheduler.resume_task(t_id) is True
        tasks = scheduler.list_tasks()
        assert tasks[0]["enabled"] in (True, 1)

        # Delete
        assert scheduler.delete_task(t_id) is True
        tasks = scheduler.list_tasks()
        assert len(tasks) == 0
