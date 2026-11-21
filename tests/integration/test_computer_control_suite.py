"""
JARVIS OS — Integration Test Suite: Intelligent Computer Control (Tests A to L)
Verifies:
- Test A: Select Option 1 (Playwright DOM verification)
- Test B: Select Option 1 and Click Submit (Single submit + confirmation verification)
- Test C: Text Entry ("Type Hello JARVIS")
- Test D: Mouse Movement (Target identification and pointer movement)
- Test E: Right Click (Context menu activation)
- Test F: Keyboard Shortcuts ("Press Ctrl+A")
- Test G: Multi-Step Workflow (Open, select option 2, type name, submit)
- Test H: Ambiguous Target Detection (Clarification requested, no blind clicks)
- Test I: Emergency Stop & Cancellation (Workflow halted, inputs released)
- Test J: Permission Enforcement (Mode 1 Observe blocks mutations)
- Test K: Native Desktop Integration (xdotool / PyAutoGUI pointer & keypress)
- Test L: Voice Command Pipeline Dispatch
"""

import os
import time
import pytest
from pathlib import Path

from tools.desktop.browser_backend import PlaywrightBrowserBackend, browser_backend
from tools.desktop.native_backend import native_backend
from tools.desktop.screen_intelligence import screen_intelligence
from tools.desktop.unified_computer_service import (
    UnifiedComputerService,
    ComputerControlMode,
    unified_computer_service,
)
from ai.local_engine import LocalIntelligenceEngine
from apps.voice.service import voice_service


FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures", "computer_control_test_page.html")
)
FIXTURE_URL = f"file://{FIXTURE_PATH}"


@pytest.fixture(scope="module")
def setup_test_browser():
    """Ensure Playwright browser is running and pointed at the test fixture."""
    res = browser_backend.start(initial_url=FIXTURE_URL)
    assert res.get("status") in ("ok", "already_running"), f"Browser start failed: {res}"
    yield browser_backend
    browser_backend.close()


@pytest.fixture(autouse=True)
def reset_service_state():
    """Reset unified service to default mode and reset emergency stop before each test."""
    unified_computer_service.reset_emergency_stop()
    unified_computer_service.set_mode(ComputerControlMode.COMMAND_CONTROL)
    # Reset ambiguity mode in fixture
    if browser_backend.is_running() and browser_backend._page:
        try:
            browser_backend._page.goto(FIXTURE_URL, wait_until="domcontentloaded")
            browser_backend._page.evaluate("() => { if(window.setAmbiguityMode) window.setAmbiguityMode(false); }")
        except Exception:
            pass


# ── Test A: Select Option 1 ───────────────────────────────────

def test_a_select_option_1(setup_test_browser):
    """Test A: 'Select option 1' selects Option 1 radio, keeps others unselected, and verifies DOM."""
    res = unified_computer_service.execute_natural_instruction("Select option 1")
    assert res.get("status") == "ok", f"Expected ok status, got {res}"
    assert res.get("verified") is True, "Option 1 was not verified as selected"

    # Verify directly in Playwright DOM
    assert browser_backend._page is not None
    is_opt1_checked = browser_backend._page.is_checked("#option1")
    is_opt2_checked = browser_backend._page.is_checked("#option2")
    is_opt3_checked = browser_backend._page.is_checked("#option3")

    assert is_opt1_checked is True, "Option 1 radio button should be checked"
    assert is_opt2_checked is False, "Option 2 radio button should remain unchecked"
    assert is_opt3_checked is False, "Option 3 radio button should remain unchecked"


# ── Test B: Select and Submit ──────────────────────────────────

def test_b_select_and_submit(setup_test_browser):
    """Test B: 'Select option 1 and click Submit' selects option 1, clicks once, and confirms."""
    res = unified_computer_service.execute_natural_instruction("Select option 1 and click Submit")
    assert res.get("status") == "ok", f"Expected ok status, got {res}"
    assert res.get("verified") is True, "Expected verified submission"

    # Verify DOM confirmation banner and counter
    assert browser_backend._page is not None
    banner = browser_backend._page.query_selector("#confirmation-banner")
    assert banner is not None and banner.is_visible(), "Confirmation banner must be visible"

    banner_text = banner.inner_text()
    assert "Option 1 was selected and the form was submitted successfully" in banner_text

    # Verify submit count is exactly 1
    counter_text = browser_backend._page.inner_text("#submit-counter")
    assert "Submissions: 1" in counter_text, f"Expected 1 submission, got: {counter_text}"


# ── Test C: Text Entry ─────────────────────────────────────────

def test_c_text_entry(setup_test_browser):
    """Test C: 'Type Hello JARVIS' types text into field and verifies value."""
    res = unified_computer_service.execute_natural_instruction("Type Hello JARVIS")
    assert res.get("status") == "ok", f"Expected ok status, got {res}"
    assert res.get("verified") is True, "Expected text to be verified"

    # Verify input field value in DOM
    assert browser_backend._page is not None
    val = browser_backend._page.input_value("#search-input")
    assert val == "Hello JARVIS", f"Expected field value 'Hello JARVIS', got '{val}'"


# ── Test D: Mouse Movement ────────────────────────────────────

def test_d_mouse_movement(setup_test_browser):
    """Test D: 'Move the mouse to the Submit button' resolves element and moves native pointer."""
    # Move to Submit button
    res = unified_computer_service.execute_natural_instruction("Move the mouse to the Submit button")
    assert res.get("status") == "ok", f"Expected ok, got: {res}"
    assert res.get("verified") is True, f"Mouse movement not verified: {res}"

    # Also test explicit coordinates movement
    res_coords = unified_computer_service.execute_natural_instruction("Move the mouse to 450, 250")
    assert res_coords.get("status") == "ok"
    pos = native_backend.get_cursor_position()
    assert abs(pos["x"] - 450) <= 2 and abs(pos["y"] - 250) <= 2, f"Expected (450, 250), got {pos}"


# ── Test E: Right Click ───────────────────────────────────────

def test_e_right_click(setup_test_browser):
    """Test E: 'Right-click the test item' triggers right click / context menu."""
    res = unified_computer_service.execute_natural_instruction("Right-click the test item")
    assert res.get("status") == "ok", f"Expected ok, got: {res}"
    assert res.get("verified") is True


# ── Test F: Keyboard Shortcuts ─────────────────────────────────

def test_f_keyboard_shortcuts(setup_test_browser):
    """Test F: 'Press Ctrl+A' triggers selection hotkey safely."""
    res = unified_computer_service.execute_natural_instruction("Press Ctrl+A")
    assert res.get("status") == "ok", f"Expected ok, got: {res}"
    assert res.get("verified") is True


# ── Test G: Multi-Step Workflow ───────────────────────────────

def test_g_multi_step_workflow(setup_test_browser):
    """Test G: Multi-step workflow: select option 2, type name, submit, and verify."""
    # Step 1: Select option 2
    r1 = unified_computer_service.execute_natural_instruction("Select option 2")
    assert r1.get("status") == "ok" and r1.get("verified") is True

    # Step 2: Type test name
    r2 = unified_computer_service.execute_natural_instruction("Type Chief Engineer")
    assert r2.get("status") == "ok" and r2.get("verified") is True

    # Step 3: Click Submit
    r3 = unified_computer_service.execute_natural_instruction("Click Submit")
    assert r3.get("status") == "ok"

    # Verify resulting confirmation banner
    assert browser_backend._page is not None
    banner = browser_backend._page.query_selector("#confirmation-banner")
    assert banner is not None and banner.is_visible()
    banner_text = banner.inner_text()
    assert "Option 2 was selected" in banner_text
    assert "Chief Engineer" in banner_text


# ── Test H: Ambiguous Target ──────────────────────────────────

def test_h_ambiguous_target(setup_test_browser):
    """Test H: When multiple visible Submit buttons exist, report ambiguity and refuse blind click."""
    assert browser_backend._page is not None
    # Enable the ambiguity section containing two duplicate Submit buttons
    browser_backend._page.evaluate("() => window.setAmbiguityMode(true)")

    ambig_check = browser_backend.detect_ambiguity("Submit", element_type="button")
    assert ambig_check.get("ambiguous") is True, "Ambiguity detector should flag multiple Submit buttons"
    assert ambig_check.get("count") >= 2, "Should find at least 2 candidate buttons"

    # Now execute click Submit
    res = unified_computer_service.execute_natural_instruction("Click Submit")
    assert res.get("status") == "ambiguous", f"Expected ambiguous status, got: {res}"
    assert "Multiple" in res.get("response", "") or "clarify" in res.get("response", "")

    # Cleanup ambiguity mode
    browser_backend._page.evaluate("() => window.setAmbiguityMode(false)")


# ── Test I: Emergency Stop & Cancellation ─────────────────────

def test_i_emergency_stop_cancellation(setup_test_browser):
    """Test I: Triggering Emergency Stop blocks all subsequent actions and releases inputs."""
    # Trigger stop via instruction
    res_stop = unified_computer_service.execute_natural_instruction("Jarvis, stop controlling my computer")
    assert res_stop.get("status") == "stopped"
    assert unified_computer_service.is_emergency_stopped() is True

    # Any subsequent mutation attempt must be blocked immediately
    res_blocked = unified_computer_service.execute_natural_instruction("Select option 1 and click Submit")
    assert res_blocked.get("status") == "blocked"
    assert "EMERGENCY STOP" in res_blocked.get("response", "")

    # Reset stop
    unified_computer_service.reset_emergency_stop()
    assert unified_computer_service.is_emergency_stopped() is False


# ── Test J: Permission Enforcement (Safety Modes) ─────────────

def test_j_permission_enforcement(setup_test_browser):
    """Test J: Mode 1 (Observe Only) blocks click and type mutations."""
    unified_computer_service.set_mode(ComputerControlMode.OBSERVE)

    res = unified_computer_service.execute_natural_instruction("Select option 1 and click Submit")
    assert res.get("status") == "blocked"
    assert "OBSERVE" in res.get("response", "")

    # Restore command control mode
    unified_computer_service.set_mode(ComputerControlMode.COMMAND_CONTROL)
    res_ok = unified_computer_service.execute_natural_instruction("Select option 1")
    assert res_ok.get("status") == "ok"


# ── Test K: Native Desktop Integration ────────────────────────

def test_k_native_desktop_integration():
    """Test K: Real pointer movement and display query on X11 TigerVNC desktop."""
    info = native_backend.get_display_server_info()
    assert info["server_type"] in ("x11", "wayland"), f"Expected x11 or wayland, got {info['server_type']}"
    assert info["resolution"]["width"] > 0 and info["resolution"]["height"] > 0

    # Move cursor smoothly to (200, 200) and verify position
    res = native_backend.move_cursor(200, 200, duration=0.1, smooth=True)
    assert res.get("status") == "ok"
    pos = native_backend.get_cursor_position()
    assert abs(pos["x"] - 200) <= 2 and abs(pos["y"] - 200) <= 2


# ── Test L: Voice Command Pipeline Dispatch ───────────────────

def test_l_voice_command_pipeline(setup_test_browser):
    """Test L: Voice command pipeline dispatches computer automation and synthesizes reply."""
    # Test through LocalIntelligenceEngine intent classification
    engine = LocalIntelligenceEngine()
    intent, ctx = engine.classify_intent("Jarvis, select option 1 and click Submit")
    assert intent == "computer_command", f"Expected computer_command intent, got {intent}"

    # Test processing through voice_service
    response = voice_service.process_command(
        text="Jarvis, select option 1 and click Submit",
        speak=False,
    )
    assert "Option 1 was selected and the form was submitted successfully" in response
