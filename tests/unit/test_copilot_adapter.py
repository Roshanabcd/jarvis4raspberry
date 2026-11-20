"""
Unit tests for GitHub Copilot CLI Adapter in JARVIS OS.
Validates CLI discovery, granular sandboxed tool flags, secret scrubbing, and execution handling.
"""
from __future__ import annotations

import json
import os
import subprocess
from unittest.mock import MagicMock, patch
import pytest

from tools.agents.adapters.copilot_adapter import CopilotAdapter
from tools.agents.models import AgentMetadata, AgentStatus, AgentTask, ProblemContext
from tools.agents.registry import agent_registry


def test_copilot_adapter_discovery_and_attributes():
    """Verify Copilot adapter discovers executable, version, and capabilities."""
    adapter = CopilotAdapter()
    meta = adapter.discover()

    assert meta.id == "copilot"
    assert meta.display_name == "GitHub Copilot"
    assert meta.installed is True
    assert meta.authenticated is True
    assert meta.status == AgentStatus.READY
    assert meta.capabilities.supports_noninteractive is True
    assert meta.capabilities.supports_file_editing is True
    assert meta.capabilities.supports_sandbox is True
    assert "GPT-5.6 Luna" in meta.capabilities.models


def test_copilot_adapter_no_secret_leaks():
    """Verify copilot metadata never leaks any credentials or forbidden strings."""
    adapter = CopilotAdapter()
    meta = adapter.discover()
    meta_str = json.dumps(meta.to_dict()).lower()

    for forbidden in ["api_key", "secret", "bearer", "password", "token="]:
        assert forbidden not in meta_str, f"Disclosed forbidden string '{forbidden}' in copilot metadata"


def test_copilot_adapter_sandboxed_command_construction():
    """Verify execute_task builds command with sandboxed tool rules and add-dir."""
    adapter = CopilotAdapter()
    task = AgentTask(title="Refactor helper", problem_context=ProblemContext(original_request="Fix bug"))
    context = ProblemContext(
        original_request="Fix division by zero",
        error_message="ZeroDivisionError",
        traceback="line 4, in divide",
        working_dir="/home/roshan/.gemini/antigravity/scratch/jarvis-os",
    )

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_proc.communicate.return_value = ("Success output", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        result = adapter.execute_task(task, context)

        assert result["status"] == "ok"
        assert result["exit_code"] == 0
        assert result["agent_id"] == "copilot"

        # Check command arguments
        cmd_called = mock_popen.call_args[0][0]
        assert cmd_called[0] == adapter.cli_path
        assert "-p" in cmd_called
        assert "--silent" in cmd_called
        assert "--allow-tool=write" in cmd_called
        assert "--allow-tool=shell(git:*)" in cmd_called
        assert any(arg.startswith("--add-dir=") for arg in cmd_called)


def test_copilot_adapter_timeout_handling():
    """Verify execute_task handles subprocess timeout gracefully."""
    adapter = CopilotAdapter()
    task = AgentTask(title="Long task", problem_context=ProblemContext(original_request="Stuck task"))
    context = ProblemContext(
        original_request="Hanging process",
        error_message="Timeout",
        working_dir="/tmp",
    )

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd=["copilot"], timeout=120)
        mock_popen.return_value = mock_proc

        result = adapter.execute_task(task, context)

        assert result["status"] == "error"
        assert "timed out" in result["message"]


def test_copilot_adapter_registered_in_registry():
    """Verify copilot adapter is properly registered in global agent registry."""
    adapter = agent_registry.get_adapter("copilot")
    assert adapter is not None
    assert isinstance(adapter, CopilotAdapter)
