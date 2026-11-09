"""
JARVIS OS — Phase 2 Acceptance Test Suite
Comprehensive tests verifying real desktop application launching, browser navigation,
VS Code & Antigravity IDE project opening, bounded file & content search,
interactive terminal execution, process tracking, security confirmation gates,
and multi-step agent orchestration on Raspberry Pi 5.
"""
from __future__ import annotations

import os
import subprocess
import time
import pytest

from ai.brain import JARVISBrain
from tools.desktop.action_engine import desktop_action_engine
from tools.desktop.app_launcher import app_launcher
from tools.desktop.browser_controller import browser_controller
from tools.desktop.file_search import file_search
from tools.desktop.program_runner import program_runner
from tools.desktop.project_manager import project_manager
from tools.desktop.window_manager import window_manager
from tools.terminal.terminal_manager import terminal_engine


@pytest.fixture(scope="module")
def brain():
    return JARVISBrain()


class TestPhase2DesktopAgent:
    """Test suite covering the 12 acceptance criteria of Phase 2."""

    def test_case_1_terminal_execution(self, brain):
        """Test 1: User says 'Run python3 --version in the terminal.'"""
        res = brain.chat("Run python3 --version in the terminal.")
        assert res is not None
        assert "Python" in res["response"]
        assert "0" in res["response"] or "SUCCESS" in res["response"]
        assert any(t["tool"] == "terminal_execute" for t in res["tools_used"])

    def test_case_2_application_opening_chrome(self, brain):
        """Test 2: Open Google Chrome with process/action verification."""
        res = brain.chat("Open Google Chrome.")
        assert res is not None
        assert "chrome" in res["response"].lower() or "launched" in res["response"].lower()
        assert any(t["tool"] == "desktop_open_app" for t in res["tools_used"])

    def test_case_3_browser_navigation(self, brain):
        """Test 3: Open YouTube in Chrome with real URL resolution."""
        res = brain.chat("Open YouTube in Google Chrome.")
        assert res is not None
        assert "youtube.com" in res["response"]
        assert "Chrome" in res["response"]
        assert any(t["tool"] == "desktop_open_url" for t in res["tools_used"])

    def test_case_4_firefox_launch(self, brain):
        """Test 4: Open Firefox with honest verification."""
        res = brain.chat("Open Firefox.")
        assert res is not None
        assert "firefox" in res["response"].lower()
        assert any(t["tool"] == "desktop_open_app" for t in res["tools_used"])

    def test_case_5_vscode_launch(self, brain):
        """Test 5: Open VS Code."""
        res = brain.chat("Open VS Code.")
        assert res is not None
        assert "code" in res["response"].lower() or "launched" in res["response"].lower()
        assert any(t["tool"] == "desktop_open_app" for t in res["tools_used"])

    def test_case_6_antigravity_project_open(self, brain):
        """Test 6: Open my JARVIS project in Antigravity."""
        res = brain.chat("Open my JARVIS project in Antigravity.")
        assert res is not None
        assert "jarvis-os" in res["response"]
        assert "ANTIGRAVITY" in res["response"]
        assert any(t["tool"] == "desktop_open_project" for t in res["tools_used"])

    def test_case_7_file_search_bounded(self, brain):
        """Test 7: Find all Python files in my UnityGameWorkspace folder."""
        res = brain.chat("Find all Python files in my UnityGameWorkspace folder.")
        assert res is not None
        assert "controller.py" in res["response"] or "build.py" in res["response"]
        assert any(t["tool"] == "desktop_search_files" for t in res["tools_used"])

    def test_case_8_program_execution_real_output(self, brain):
        """Test 8: Run harmless Python program with real stdout, exit code, and runtime."""
        res = brain.chat("Run my Python program in the UnityGameWorkspace folder.")
        assert res is not None
        assert "Exit Code" in res["response"] and "0" in res["response"]
        assert "Building Unity GameProject assets" in res["response"]
        assert any(t["tool"] == "desktop_run_program" for t in res["tools_used"])

    def test_case_9_failed_command_honest_reporting(self):
        """Test 9: Run harmless command producing non-zero exit code (SystemExit 2)."""
        res = terminal_engine.execute_command('python3 -c "raise SystemExit(2)"', session_id="test_fail")
        assert res["exit_code"] == 2
        assert res["status"] == "FAILED"

    def test_case_10_multi_step_desktop_task(self, brain):
        """Test 10: Multi-step desktop task decomposition and execution."""
        res = brain.chat("Open VS Code, open my Unity project, and find all Python scripts in it.")
        assert res is not None
        assert res["provider"] == "compound_orchestrator"
        assert any(t["tool"] == "desktop_open_app" for t in res["tools_used"])
        assert any(t["tool"] == "desktop_open_project" for t in res["tools_used"])
        assert any(t["tool"] == "desktop_search_files" for t in res["tools_used"])
        assert "controller.py" in res["response"]

    def test_case_11_youtube_search_clarity(self, brain):
        """Test 11: YouTube search in browser distinguishing search from audio playback."""
        res = brain.chat("Search YouTube for relaxing music.")
        assert res is not None
        assert "youtube.com/results" in res["response"]
        assert "relaxing" in res["response"]
        assert any(t["tool"] == "desktop_search_youtube" for t in res["tools_used"])

    def test_case_12_security_confirmation_gate(self):
        """Test 12: Potentially destructive commands must require confirmation."""
        res = terminal_engine.execute_command("rm -rf /tmp/mock_target", session_id="sec_test")
        assert res.get("requires_confirmation") is True
        assert res.get("status") == "CONFIRMATION_REQUIRED"
        token = res.get("confirmation_token")
        assert token is not None

        # Verify confirmation token unlocks execution safely
        confirmed_res = terminal_engine.execute_command(
            "rm -rf /tmp/mock_target",
            session_id="sec_test",
            confirm=True,
            confirmation_token=token,
        )
        assert confirmed_res.get("status") == "SUCCESS"
        assert confirmed_res.get("exit_code") == 0
