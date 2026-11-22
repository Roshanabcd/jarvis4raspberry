"""
JARVIS OS — Integration Test Suite for Antigravity Auto-Approver Subsystem
Tests configuration updates, lifecycle hooks, background supervisor, REST endpoints, and fast-path intent.
"""

import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from apps.core.main import app
from tools.desktop.antigravity_approver import (
    apply_antigravity_settings,
    antigravity_supervisor,
    CONFIG_JSON_PATH,
    HOOKS_JSON_PATH,
    OUTSIDE_PROJECT_PATH,
)
from ai.brain import get_brain
from ai.local_engine import LocalIntelligenceEngine


client = TestClient(app)


def test_1_settings_application():
    """Verify Antigravity auto-execution settings are applied to all config files."""
    res = apply_antigravity_settings()
    assert res["success"] is True
    assert len(res["applied"]) >= 3
    assert len(res["errors"]) == 0

    # Verify config.json
    assert CONFIG_JSON_PATH.exists()
    with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["userSettings"]["autoExecutionPolicy"] == "CASCADE_COMMANDS_AUTO_EXECUTION_EAGER"

    # Verify outside-of-project.json
    assert OUTSIDE_PROJECT_PATH.exists()
    with open(OUTSIDE_PROJECT_PATH, "r", encoding="utf-8") as f:
        pcfg = json.load(f)
    assert pcfg["settings"]["autoExecutionPolicy"] == "CASCADE_COMMANDS_AUTO_EXECUTION_EAGER"


def test_2_hooks_json_structure():
    """Verify ~/.gemini/config/hooks.json has valid PreToolUse auto-allow format."""
    assert HOOKS_JSON_PATH.exists()
    with open(HOOKS_JSON_PATH, "r", encoding="utf-8") as f:
        hooks = json.load(f)
    assert "jarvis-auto-approve" in hooks
    pre_tool_use = hooks["jarvis-auto-approve"]["PreToolUse"]
    assert len(pre_tool_use) > 0
    assert pre_tool_use[0]["matcher"] == "*"
    assert pre_tool_use[0]["hooks"][0]["type"] == "command"
    assert "allow" in pre_tool_use[0]["hooks"][0]["command"]


def test_3_supervisor_lifecycle():
    """Verify supervisor daemon starts, reports status, and stops cleanly."""
    status = antigravity_supervisor.get_status()
    assert "running" in status
    assert "cdp_port" in status
    assert status["settings_applied"] is True

    start_res = antigravity_supervisor.start()
    assert start_res["status"] in ("started", "already_running")
    assert antigravity_supervisor.is_running() is True

    stop_res = antigravity_supervisor.stop()
    assert stop_res["status"] in ("stopped", "already_stopped")
    assert antigravity_supervisor.is_running() is False


def test_4_api_antigravity_endpoints():
    """Verify REST API endpoints for Antigravity settings and supervisor."""
    # 1. Apply settings
    r_apply = client.post("/api/computer/antigravity/apply-settings")
    assert r_apply.status_code == 200
    d_apply = r_apply.json()
    assert d_apply["success"] is True

    # 2. Status
    r_status = client.get("/api/computer/antigravity/auto-approve/status")
    assert r_status.status_code == 200
    d_status = r_status.json()
    assert "running" in d_status
    assert "total_approvals" in d_status

    # 3. Start supervisor
    r_start = client.post("/api/computer/antigravity/auto-approve/start?port=9333")
    assert r_start.status_code == 200

    # 4. Stop supervisor
    r_stop = client.post("/api/computer/antigravity/auto-approve/stop")
    assert r_stop.status_code == 200


def test_5_ai_intent_classification():
    """Verify natural language requests classify to antigravity_auto_approve."""
    engine = LocalIntelligenceEngine()
    test_phrases = [
        "auto accept antigravity",
        "auto approve antigravity commands",
        "accept option 1 in antigravity",
        "allow running this command in antigravity",
        "antigravity auto accept",
    ]
    for phrase in test_phrases:
        intent, ctx = engine.classify_intent(phrase)
        assert intent == "antigravity_auto_approve", f"Phrase '{phrase}' classified as '{intent}'"


def test_6_brain_chat_fastpath_integration():
    """Verify brain.chat() executes the antigravity_auto_approve fast path."""
    brain = get_brain()
    reply = brain.chat("auto accept antigravity")
    assert "response" in reply
    resp_text = reply["response"].lower()
    assert "jarvis" in resp_text
    assert ("antigravity" in resp_text or "option 1" in resp_text or "auto-execution" in resp_text)
