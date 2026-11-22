import pytest
from unittest.mock import MagicMock, patch

from ai.brain import strip_command_noise
from ai.local_engine import local_engine, LocalIntelligenceEngine
from tools.registry import tool_registry
from tools.identity.permission_manager import permission_manager, ROLE_ALLOWED_TOOLS, UserRole
from apps.voice.wake_word_engine import WakeWordEngine


def test_strip_command_noise():
    # Leading wake phrases / politeness
    assert strip_command_noise("hello jarvis open youtube in chrome") == "open youtube in chrome"
    assert strip_command_noise("hey jarvis open youtube") == "open youtube"
    assert strip_command_noise("jarvis please open chrome") == "open chrome"

    # Trailing polite / greeting noise
    assert strip_command_noise("open YouTube hello") == "open YouTube"
    assert strip_command_noise("open youtube please") == "open youtube"
    assert strip_command_noise("open chrome thank you") == "open chrome"

    # Both leading and trailing noise
    assert strip_command_noise("hey jarvis open youtube hello") == "open youtube"
    assert strip_command_noise("hello jarvis please open youtube in chrome thank you") == "open youtube in chrome"


def test_tool_registry_browser_tools():
    # Verify open_url, open_youtube, and open_desktop_app are registered
    assert tool_registry.has_tool("open_url"), "open_url must be registered in tool_registry"
    assert tool_registry.has_tool("open_youtube"), "open_youtube must be registered in tool_registry"
    assert tool_registry.has_tool("open_desktop_app"), "open_desktop_app must be registered in tool_registry"

    open_url_tool = tool_registry.get_tool("open_url")
    assert "url" in open_url_tool["schema"]

    open_yt_tool = tool_registry.get_tool("open_youtube")
    assert "query" in open_yt_tool["schema"]

    open_desk_tool = tool_registry.get_tool("open_desktop_app")
    assert "app_name" in open_desk_tool["schema"]


def test_permission_manager_guest_and_user_roles():
    guest_tools = ROLE_ALLOWED_TOOLS[UserRole.GUEST.value]
    user_tools = ROLE_ALLOWED_TOOLS[UserRole.USER.value]

    required_tools = [
        "open_url",
        "open_youtube",
        "open_desktop_app",
        "desktop_open_url",
        "desktop_search_youtube",
        "desktop_open_app",
    ]

    for tool in required_tools:
        assert tool in guest_tools, f"{tool} must be allowed for GUEST role"
        assert tool in user_tools, f"{tool} must be allowed for USER role"


def test_local_engine_intent_with_noise():
    intent1, args1 = local_engine.classify_intent("open YouTube hello")
    assert intent1 in ("desktop_open_url", "desktop_search_youtube"), (
        f"Expected desktop_open_url/desktop_search_youtube for 'open YouTube hello', got {intent1}"
    )

    intent2, args2 = local_engine.classify_intent("hello jarvis open youtube in chrome")
    assert intent2 in ("desktop_open_url", "desktop_search_youtube"), (
        f"Expected desktop_open_url/desktop_search_youtube for 'hello jarvis open youtube in chrome', got {intent2}"
    )


def test_wake_word_engine_command_extraction():
    eng = WakeWordEngine()
    assert eng._command_after_wake_phrase("hello jarvis open youtube in chrome") == "open youtube in chrome"
    assert eng._command_after_wake_phrase("jarvis open youtube please") == "open youtube"
    assert eng._command_after_wake_phrase("hey jarvis open chrome") == "open chrome"
    assert eng._command_after_wake_phrase("hello jarvis") == ""


def test_voice_jobs_turn_and_message_id():
    from apps.voice.voice_jobs import VoiceJobManager, VoiceJob

    manager = VoiceJobManager()
    job = manager.create_job(
        "Test reply",
        turn_id="turn_12345",
        message_id="msg_abcde",
    )
    assert job.turn_id == "turn_12345"
    assert job.message_id == "msg_abcde"


def test_soft_failure_detection():
    from tools.developer.cli_bridge import is_soft_failure

    # Quota 429 marker in stdout even if exit_code == 0
    failed, reason = is_soft_failure("Error 429: RESOURCE_EXHAUSTED. Quota exceeded for model.", exit_code=0)
    assert failed is True
    assert "429" in reason or "quota" in reason.lower()

    # Normal success output with exit_code == 0
    failed_ok, _ = is_soft_failure("Task completed successfully. Output created.", exit_code=0)
    assert failed_ok is False

    # Exit code != 0
    failed_err, reason_err = is_soft_failure("Command failed", exit_code=1)
    assert failed_err is True

    # Missing target file
    failed_missing, reason_missing = is_soft_failure(
        "Saved file", exit_code=0, target_file="/tmp/non_existent_file_test_jarvis_12345.jpg"
    )
    assert failed_missing is True
    assert "was not created on disk" in reason_missing


def test_detect_requested_output_file():
    from tools.developer.cli_bridge import detect_requested_output_file

    path1 = detect_requested_output_file("Please generate an image of a horse and save to /home/roshan/Downloads/horse.jpg")
    assert path1 == "/home/roshan/Downloads/horse.jpg"

    path2 = detect_requested_output_file("create wallpaper save as /tmp/view.png")
    assert path2 == "/tmp/view.png"


def test_task_completion_announcer():
    from apps.voice.task_announcer import make_completion_summary

    # Success announcement with file
    s1 = make_completion_summary("success", action_or_name="generate_image", output_file="/home/roshan/Downloads/horse.jpg")
    assert "Task complete" in s1
    assert "horse.jpg" in s1

    # Quota exhaustion announcement
    s2 = make_completion_summary(
        "quota_exhausted",
        action_or_name="cli_fix",
        failover_trace=[{"cli": "Antigravity"}, {"cli": "Claude"}],
        error="429 quota exceeded"
    )
    assert "quota is exhausted" in s2
    assert "Antigravity" in s2 or "Claude" in s2


def test_openai_tools_schema_includes_desktop_and_youtube():
    from ai.providers.base import JARVIS_TOOLS

    tool_names = [t["name"] for t in JARVIS_TOOLS]
    assert "open_url" in tool_names
    assert "open_youtube" in tool_names
    assert "open_desktop_app" in tool_names

