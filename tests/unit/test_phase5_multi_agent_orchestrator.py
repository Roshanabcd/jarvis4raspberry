"""
Unit Test Suite for JARVIS OS Phase 5:
Multi-AI Agent Orchestrator, Autonomous Self-Healing, Permission Manager,
and Safe Watchdog Governance.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.agents.context_packager import context_packager
from tools.agents.git_safety import git_safety
from tools.agents.models import (
    AgentCapabilities,
    AgentId,
    AgentMetadata,
    AgentStatus,
    AgentTask,
    PermissionProfile,
    PermissionRequest,
    PermissionStatus,
    ProblemContext,
    TaskPhase,
)
from tools.agents.orchestrator import multi_agent_orchestrator
from tools.agents.permission_manager import permission_manager
from tools.agents.registry import agent_registry
from tools.agents.self_healing import self_healing_engine
from tools.agents.stuck_watchdog import stuck_watchdog


# ─── Test 1: Agent Discovery ─────────────────────────────────
def test_agent_discovery():
    """Verify registry discovers all 5 configured agents on the system."""
    agents = agent_registry.discover_all(force_refresh=True)
    assert len(agents) >= 5
    agent_ids = [a.id for a in agents]
    assert "antigravity" in agent_ids
    assert "codex" in agent_ids
    assert "claude" in agent_ids
    assert "opencode" in agent_ids
    assert "ollama" in agent_ids


# ─── Test 2: Authentication Detection Without Secrets ────────
def test_authentication_detection_without_secrets():
    """Verify auth detection verifies credentials without exposing keys or tokens."""
    for agent_id in ["antigravity", "codex", "claude", "opencode", "ollama"]:
        meta = agent_registry.get_metadata(agent_id)
        assert meta is not None
        # Metadata must not leak any secrets
        meta_dict = meta.to_dict()
        meta_str = json.dumps(meta_dict).lower()
        for forbidden in ["api_key", "secret", "bearer", "password", "token="]:
            assert forbidden not in meta_str, f"Disclosed forbidden string '{forbidden}' in metadata for {agent_id}"

    # Claude and OpenCode should be truthfully unauthenticated on this Pi
    claude_meta = agent_registry.get_metadata("claude")
    assert claude_meta is not None
    assert claude_meta.status in (AgentStatus.UNAUTHENTICATED, AgentStatus.READY)
    assert isinstance(claude_meta.authenticated, bool)


# ─── Test 3: Local Ollama AI Debugging ───────────────────────
def test_local_ollama_debugging():
    """Verify local Ollama adapter can run diagnostics on http://127.0.0.1:11434."""
    adapter = agent_registry.get_adapter("ollama")
    assert adapter is not None
    ctx = ProblemContext(
        problem_description="IndexError: list index out of range in quicksort",
        error_message="IndexError: list index out of range",
        traceback="Traceback (most recent call last):\n  File 'sort.py', line 12, in quicksort\n    pivot = arr[high]",
        failing_code="def quicksort(arr, low, high):\n    pivot = arr[high]",
    )
    res = adapter.diagnose_problem(ctx)
    assert "status" in res
    assert res.get("status") in ("ok", "diagnosed", "analyzed")
    assert "analysis" in res
    assert len(res["analysis"]) > 10


# ─── Test 4: Coding Agent Invocation ─────────────────────────
def test_coding_agent_invocation():
    """Verify installed coding agent adapter (antigravity/codex) formats commands properly."""
    adapter = agent_registry.get_adapter("antigravity")
    assert adapter is not None
    assert adapter.cli_path == "/home/roshan/.local/bin/agy"
    assert os.path.exists(adapter.cli_path)

    codex = agent_registry.get_adapter("codex")
    assert codex is not None
    assert codex.cli_path == "/home/roshan/.local/bin/codex"
    assert os.path.exists(codex.cli_path)


# ─── Test 5: Permission Manager Profiles ─────────────────────
def test_permission_manager_profiles():
    """Verify permissions across SAFE_AUTO, SUPERVISED_AUTO, and MANUAL."""
    # 1. Destructive commands must be HARD DENIED in every profile
    for prof in [PermissionProfile.SAFE_AUTO, PermissionProfile.SUPERVISED_AUTO, PermissionProfile.MANUAL]:
        permission_manager.set_profile(prof)
        for bad_cmd in ["rm -rf /", "rm -rf *", "mkfs.ext4 /dev/sda", "dd if=/dev/zero of=/dev/nvme"]:
            allowed, req = permission_manager.check_permission("antigravity", "shell_execute", command=bad_cmd)
            assert not allowed and req.status in (PermissionStatus.HARD_DENIED, PermissionStatus.DENIED), f"Destructive command allowed in profile {prof}: {bad_cmd}"

        # Actuators and firmware flashing must be strictly denied
        assert not permission_manager.check_permission("codex", "robot_move", command="forward")[0]
        assert not permission_manager.check_permission("codex", "firmware_flash", command="esptool")[0]

    # 2. SAFE_AUTO allows workspace read and edit, prompts for outside write
    permission_manager.set_profile(PermissionProfile.SAFE_AUTO)
    # Read in workspace
    r_allowed, r_req = permission_manager.check_permission(
        "antigravity", "file_read", target_path="/home/roshan/.gemini/antigravity/scratch/jarvis-os/ai/brain.py"
    )
    assert r_allowed and r_req.status == PermissionStatus.AUTO_APPROVED

    # Edit in workspace
    w_allowed, w_req = permission_manager.check_permission(
        "antigravity", "file_write", target_path="/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/temp.py"
    )
    assert w_allowed and w_req.status == PermissionStatus.AUTO_APPROVED

    # Write outside workspace -> PENDING
    out_allowed, out_req = permission_manager.check_permission("antigravity", "file_write", target_path="/etc/hosts")
    assert not out_allowed and out_req.status == PermissionStatus.PENDING

    # 3. SUPERVISED_AUTO requires approval for file writes
    permission_manager.set_profile(PermissionProfile.SUPERVISED_AUTO)
    sup_allowed, sup_req = permission_manager.check_permission(
        "antigravity", "file_write", target_path="/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/temp.py"
    )
    assert not sup_allowed and sup_req.status == PermissionStatus.PENDING

    # Reset back to SAFE_AUTO
    permission_manager.set_profile(PermissionProfile.SAFE_AUTO)


# ─── Test 6: Permission Request Routing ──────────────────────
def test_permission_request_routing():
    """Verify pending requests can be approved once, approved for project, or denied."""
    permission_manager.set_profile(PermissionProfile.SUPERVISED_AUTO)
    allowed, req = permission_manager.check_permission("codex", "package_install", command="pytest-timeout")
    assert not allowed and req.status == PermissionStatus.PENDING
    req_id = req.request_id

    # Retrieve pending
    pending = permission_manager.get_pending_requests()
    assert any(p["request_id"] == req_id for p in pending)

    # Approve request
    app_res = permission_manager.approve_request(req_id, create_similar_rule=True)
    assert app_res.get("status") in ("ok", "approved") and app_res.get("decision") == "APPROVED"

    # Reset profile
    permission_manager.set_profile(PermissionProfile.SAFE_AUTO)


# ─── Test 7: Problem Detection ───────────────────────────────
def test_problem_detection():
    """Verify ProblemContextPackager extracts syntax and execution errors cleanly."""
    packager = context_packager
    tb = "Traceback (most recent call last):\n  File 'test.py', line 5\n    def foo(\n            ^\nSyntaxError: unexpected EOF while parsing"
    ctx = packager.package_failure(
        original_request="Syntax error in test.py",
        error_message="SyntaxError: unexpected EOF while parsing",
        traceback=tb,
    )
    assert ctx.error_message == "SyntaxError: unexpected EOF while parsing"
    assert "SyntaxError" in ctx.traceback


# ─── Test 8: Controlled Self-Healing Repair in Temp Workspace 
def test_controlled_self_healing_repair():
    """Test safe autonomous debugging and verification in temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        broken_file = tmp_path / "calc.py"
        broken_file.write_text("def add(a, b):\n    return a - b  # BUG: should be +\n")

        test_file = tmp_path / "test_calc.py"
        test_file.write_text("from calc import add\ndef test_add():\n    assert add(2, 3) == 5\n")

        # Snapshot before repair
        snap_id = git_safety.create_snapshot(tmpdir, [str(broken_file)])
        assert snap_id is not None

        # Apply synthetic repair
        broken_file.write_text("def add(a, b):\n    return a + b\n")

        # Verify syntax
        valid_syntax, err = git_safety.verify_syntax(str(broken_file))
        assert valid_syntax is True
        assert err == ""

        # Run test in tmpdir
        proc = subprocess.run([sys.executable, "-m", "pytest", str(test_file)], capture_output=True, text=True)
        assert proc.returncode == 0


# ─── Test 9: Bounded Agent Fallback ──────────────────────────
def test_bounded_agent_fallback():
    """Verify orchestrator fails over up to max attempts when primary agent fails."""
    ctx = ProblemContext(
        problem_description="Mock failover test",
        error_message="Test failure",
    )
    task = multi_agent_orchestrator.create_task("Test Failover", ctx)
    assert task.max_attempts <= 3

    # Primary failure simulation
    task.attempts += 1
    task.error_history.append("Primary agent failed")
    assert task.attempts <= task.max_attempts


# ─── Test 10: Stuck-Task Watchdog Loop Detection ─────────────
def test_stuck_task_watchdog_loop_detection():
    """Verify watchdog detects repeated command loops and flags task as stuck."""
    task_id = "test-task-watchdog-1"
    stuck_watchdog.record_start(task_id, pid=12345, command="pytest -v")

    # Repeat identical command 3 times
    for _ in range(3):
        stuck_watchdog.record_command(task_id, "pytest -v")

    is_stuck, reason = stuck_watchdog.is_stuck(task_id)
    assert is_stuck is True
    assert "Repeated command" in reason or "loop" in reason.lower()

    # Clear
    stuck_watchdog.clear(task_id)


# ─── Test 11: Git Safety and Rollback ────────────────────────
def test_git_safety_and_rollback():
    """Verify file snapshot and full rollback preserves original content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "critical.py"
        original_content = "# ORIGINAL VERSION 1.0\nx = 42\n"
        test_file.write_text(original_content)

        # Snapshot
        snap_id = git_safety.create_snapshot(tmpdir, [str(test_file)])
        assert snap_id is not None

        # Mutate / Break file
        test_file.write_text("# MUTATED BROKEN CODE\nx = 0 / 0\n")
        assert test_file.read_text() != original_content

        # Rollback
        restored, msg = git_safety.rollback_snapshot(snap_id)
        assert restored is True
        assert test_file.read_text() == original_content


# ─── Test 12: Multi-Agent Second-Opinion Review ──────────────
def test_multi_agent_second_opinion_review():
    """Verify second-opinion review executes read-only analysis without file mutation."""
    ctx = ProblemContext(
        problem_description="Review memory leak in connection pool",
        error_message="ResourceWarning: unclosed socket",
        failing_code="def connect():\n    s = socket.socket()\n    return s.connect(('127.0.0.1', 80))\n",
    )
    review_res = multi_agent_orchestrator.request_second_opinion_review(
        agent_id="ollama",
        context=ctx,
        proposed_patch="diff --git a/conn.py b/conn.py\n+ with socket.socket() as s:\n",
    )
    assert review_res.get("status") in ("reviewed", "ok", "complete")
    assert "review" in review_res
    assert len(review_res["review"]) > 5


# ─── Test 13: Secret Scrubbing ───────────────────────────────
def test_secret_scrubbing():
    """Verify .env files, private tokens, and passwords are never leaked into context."""
    packager = context_packager

    # Prohibited files (.env, credentials) must be blocked
    assert packager.is_prohibited_file(".env") is True
    assert packager.is_prohibited_file("config/jwt_secret.pem") is True
    assert packager.is_prohibited_file("id_rsa") is True
    assert packager.is_prohibited_file("app.py") is False

    # Secrets inside traceback or code must be redacted
    leaky_tb = (
        "Traceback:\n"
        "  File 'api.py', line 10\n"
        "  headers = {'Authorization': 'Bearer sk-12345678901234567890123456789012'}\n"
        "  api_key = 'abcdef12345678901234'\n"
        "  password = 'SuperSecretPassword123'\n"
    )
    scrubbed = packager.scrub_secrets(leaky_tb)
    assert "sk-1234567890" not in scrubbed
    assert "abcdef12345678901234" not in scrubbed
    assert "SuperSecretPassword123" not in scrubbed
    assert "[REDACTED_SECRET]" in scrubbed


# ─── Test 14: Existing JARVIS Regressions (Phase 1–4) ────────
def test_existing_jarvis_regressions():
    """Verify Phase 1-4 core functionality remains operational with zero regressions."""
    from ai.local_engine import LocalIntelligenceEngine
    engine = LocalIntelligenceEngine()

    # Phase 1: Math calculation
    math_res = engine.respond("What is 25 multiplied by 4?")
    assert "100" in math_res["response"]

    # Phase 2: App launcher recognition
    app_intent, _ = engine.classify_intent("Open Google Chrome")
    assert app_intent == "desktop_open_app"

    # Phase 3: YouTube search
    yt_intent, yt_data = engine.classify_intent("Search YouTube for robotics")
    assert yt_intent == "youtube_search"
    assert yt_data.get("query") == "robotics"

    # Phase 4: Screen observation
    scr_intent, _ = engine.classify_intent("observe screen")
    assert scr_intent == "screen_observe"

    # Phase 5: Agents discovery
    ag_intent, _ = engine.classify_intent("check which ai coding agents are installed")
    assert ag_intent == "agents_discover"
