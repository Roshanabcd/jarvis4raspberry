"""
Unit tests for background task execution and developer CLI escalation fallback.
"""
from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch
import pytest

from apps.tasks.background import Identity, Work, run_brain
from tools.developer.cli_bridge import DeveloperCliBridge, redact


def test_secret_redaction():
    """Verify secrets and keys are redacted from CLI output."""
    raw = "Found api_key=sk-1234567890abcdef in config, token: secret_tok_xyz123, PIN=1234"
    clean = redact(raw)
    assert "sk-1234567890abcdef" not in clean
    assert "secret_tok_xyz123" not in clean
    assert "1234" not in clean
    assert "[REDACTED]" in clean


def test_cli_bridge_detection():
    """Verify developer CLI detection finds agy and claude on system."""
    bridge = DeveloperCliBridge()
    detected = bridge.detect_clis()
    assert detected["has_developer_cli"] is True
    assert detected["primary"] in ("antigravity", "claude")


def test_background_task_run_brain_escalates_on_provider_failure():
    """Verify run_brain automatically escalates to developer CLI when brain.chat fails."""
    work = Work(job_id="tjob_test012345678901234567890123", transcript="Analyze recent errors", identity=Identity())
    progress_events = []

    # Mock resolve_identity to match work.identity
    with patch("apps.tasks.background.resolve_identity", return_value=work.identity):
        with patch("ai.brain.get_brain") as mock_get_brain:
            mock_brain = MagicMock()
            mock_get_brain.return_value = mock_brain
            # Simulate brain provider failure (e.g. unreachable model)
            mock_brain.chat.return_value = {
                "status": "failed",
                "error": "No active AI provider reachable",
                "response": "AI Provider Error: The AI model is unreachable",
            }

            # Mock developer CLI bridge diagnostic run
            with patch("tools.developer.cli_bridge.developer_cli_bridge.detect_clis", return_value={"has_developer_cli": True, "antigravity": {"installed": True}}):
                with patch("tools.developer.cli_bridge.developer_cli_bridge.run_diagnostic_cli", return_value={
                    "status": "ok",
                    "cli": "antigravity",
                    "output": "Diagnosis: all services running normally. Suggest rechecking network config.",
                }) as mock_cli_run:
                    result = run_brain(work, lambda e: progress_events.append(e))

                    assert mock_cli_run.called
                    assert result.get("status") == "succeeded"
                    assert "Developer CLI Escalation" in result.get("response", "")
                    assert "all services running normally" in result.get("response", "")
                    assert any(e.get("detail") == "Escalating to developer CLI (agy)" for e in progress_events)
