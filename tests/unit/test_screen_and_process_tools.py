"""
Unit tests for Desktop Screen Inspection and Safe Read-Only Process Inspector.
Verifies intent classification, process inspector redaction, and tool executor alias handling.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from ai.local_engine import LocalIntelligenceEngine
from tools.system.process_inspector import ProcessInspector


def test_intent_screen_observe_disambiguation():
    """Verify screen inspection queries route to screen_observe and NOT camera_capture."""
    engine = LocalIntelligenceEngine()

    screen_queries = [
        "Inspect the current screen and tell me what is displayed.",
        "inspect the screen and tell me what is displayed",
        "what is displayed on my screen",
        "what is on the screen right now",
        "describe my screen",
        "screen inspect",
    ]

    for q in screen_queries:
        intent, _ = engine.classify_intent(q)
        assert intent == "screen_observe", f"Expected 'screen_observe' for '{q}', got '{intent}'"


def test_intent_running_apps_processes():
    """Verify running apps queries route to running_apps_processes and NOT general telemetry."""
    engine = LocalIntelligenceEngine()

    proc_queries = [
        "can you see what are the things is running on my pc",
        "what are running software on my pc",
        "what is running on my pc",
        "what apps are running on my computer",
        "running software on my pc",
        "list running software",
    ]

    for q in proc_queries:
        intent, _ = engine.classify_intent(q)
        assert intent == "running_apps_processes", f"Expected 'running_apps_processes' for '{q}', got '{intent}'"


def test_process_inspector_security_redaction():
    """Verify process inspector collects processes without leaking cmdline args or env vars."""
    inspector = ProcessInspector()
    top = inspector.get_top_processes(limit=5)

    assert "top_cpu" in top
    assert "top_ram" in top
    assert "total_process_count" in top
    assert top["total_process_count"] > 0

    for p in top["top_cpu"] + top["top_ram"]:
        assert "pid" in p
        assert "name" in p
        assert "user" in p
        assert "cpu_pct" in p
        assert "memory_mb" in p
        # Strict security constraint: cmdline and environ MUST NOT be present in process dict
        assert "cmdline" not in p
        assert "environ" not in p


def test_process_inspector_overview_markdown():
    """Verify get_running_overview formats a clean markdown report."""
    inspector = ProcessInspector()
    overview = inspector.get_running_overview(limit=5)

    assert overview["status"] == "ok"
    assert "windows" in overview
    assert "processes" in overview
    assert "services" in overview
    assert "markdown" in overview
    md = overview["markdown"]
    assert "Running Software & Desktop Processes" in md
    assert "Core JARVIS Services" in md
    assert "Top Running Processes" in md


def test_tool_executor_alias_resolution():
    """Verify ToolExecutor handles common LLM aliases like capture_image and inspect_screen."""
    from ai.tools.executor import ToolExecutor
    executor = ToolExecutor()

    # 1. capture_image with screen context routes to screen capture
    with patch.object(executor, "_tool_screen_capture", return_value={"status": "ok", "target": "screen"}) as mock_screen:
        res = executor.execute("capture_image", {"target": "desktop screen"})
        assert mock_screen.called
        assert "screen" in res

    # 2. inspect_screen routes to screen capture
    with patch.object(executor, "_tool_screen_capture", return_value={"status": "ok", "target": "screen"}) as mock_screen:
        res = executor.execute("inspect_screen", {})
        assert mock_screen.called

    # 3. running_apps_processes routes to process inspector
    with patch("tools.system.process_inspector.process_inspector.get_running_overview", return_value={"status": "ok", "markdown": "proc_overview"}) as mock_proc:
        res = executor.execute("running_apps_processes", {})
        assert mock_proc.called
        assert "proc_overview" in res
