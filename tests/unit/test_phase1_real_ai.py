"""
JARVIS OS — Phase 1 Acceptance & Regression Test Suite
Automated verification for all 12 Phase 1 acceptance criteria:
- Production conversational AI (Ollama llama3.2:1b)
- Truthful system telemetry (real RAM GB, Linux uptime, CPU %, temp, robot state)
- Intent disambiguation (no system status hijacking of code requests)
- Deterministic calculation tools
- Multi-task agent orchestration
- Session isolation & conversational history recall
- Transparent provider error handling
- Non-truncated long responses
- Streaming & graceful cancellation
- Persistence across restart
"""
import pytest
import time
import re
from typing import Dict, Any

from ai.brain import JARVISBrain
from ai.agents.task_orchestrator import CompoundTaskOrchestrator
from tools.calculator.calculator_tools import calculator_tools
from tools.system.system_tools import system_tools
from hardware.raspberry_pi.rpi_info import get_system_status
from memory.long_term.database import db


@pytest.fixture(scope="module")
def brain():
    return JARVISBrain()


def test_case_1_simple_greeting(brain):
    """Test 1: Simple greeting receives natural AI greeting without system telemetry or stubs."""
    session_id = "test_p1_case1"
    res = brain.chat("hello", session_id=session_id)
    assert res.get("provider") in ("ollama", "gemini", "openai", "edge_fastpath")
    text = res.get("response", "").strip()
    assert len(text) > 0
    # Must not be an old system status or calculator dump
    assert "System Status" not in text
    assert "Fibonacci" not in text
    assert "local intelligence mode" not in text.lower()


def test_case_2_system_status_telemetry(brain):
    """Test 2: System status reads actual machine values without 0.0GB or N/A."""
    session_id = "test_p1_case2"
    res = brain.chat("What is my current system status?", session_id=session_id)
    text = res.get("response", "")
    assert "System Status" in text
    assert "RAM:" in text
    assert "0.0GB / 0.0GB" not in text
    assert "0.00 GB / 0.00 GB" not in text
    assert "Uptime: N/A" not in text
    # Verify values exist
    status = get_system_status()
    assert status["ram_total_gb"] > 0
    assert status["ram_used_gb"] > 0
    assert status["uptime_s"] > 0
    assert status["robot_state"] in ("CONNECTED", "DISCONNECTED", "SIMULATION", "UNKNOWN")


def test_case_3_uptime_and_memory_python_script(brain):
    """Test 3: Programming request with 'uptime' and 'memory' generates Python code, not telemetry."""
    session_id = "test_p1_case3"
    res = brain.chat("Write a Python script to display system uptime and memory.", session_id=session_id)
    text = res.get("response", "")
    assert res.get("provider") == "ollama" or res.get("provider") in ("gemini", "openai")
    # Must contain python code
    assert "```python" in text or "def " in text or "import " in text
    assert "psutil" in text or "uptime" in text
    # Must NOT be the raw hardware telemetry output
    assert "🤖 Robot:" not in text


def test_case_4_fibonacci_programming(brain):
    """Test 4: Fibonacci programming returns full Python function and explanation."""
    session_id = "test_p1_case4"
    res = brain.chat("Write a Python function to compute Fibonacci numbers and explain how it works.", session_id=session_id)
    text = res.get("response", "")
    assert "def fibonacci" in text or "def fib" in text
    assert "return" in text
    assert len(text) > 150
    # Must not be a dummy calculator stub
    assert "calculator.py" not in text.lower()


def test_case_5_standalone_number(brain):
    """Test 5: Standalone number requests clarification without assuming calculation or uptime."""
    session_id = "test_p1_case5"
    res = brain.chat("2020", session_id=session_id)
    text = res.get("response", "")
    assert "2020" in text
    assert "how would you like me to use it" in text.lower() or "what would you like" in text.lower()
    assert "System Status" not in text


def test_case_6_deterministic_calculation(brain):
    """Test 6: Natural language calculation returns exact deterministic result (100)."""
    session_id = "test_p1_case6"
    res = brain.chat("What is 25 multiplied by 4?", session_id=session_id)
    text = res.get("response", "")
    assert "100" in text
    assert res.get("provider") == "edge_fastpath"


def test_case_7_multiple_independent_tasks(brain):
    """Test 7: Multi-task compound request splits, executes each, and unifies response."""
    prompt = "Tell me my current RAM usage, calculate 15 percent of 800, and write a short Python function that adds two numbers."
    assert CompoundTaskOrchestrator.is_compound_request(prompt) is True
    res = CompoundTaskOrchestrator.execute_compound(prompt, brain, session_id="test_p1_case7")
    text = res.get("response", "")
    # Check 1: RAM usage
    assert "RAM Usage" in text or "Memory Used" in text
    # Check 2: Calculation 15% of 800 -> 120
    assert "120" in text
    # Check 3: Python function
    assert "def " in text or "```python" in text


def test_case_8_context_preservation_and_recall(brain):
    """Test 8: Context preservation and conversational recall."""
    sid = "test_p1_case8"
    db.clear_session_messages(sid)

    brain.chat("What is Raspberry Pi 5?", session_id=sid)
    brain.chat("How much RAM does my Pi have?", session_id=sid)
    brain.chat("hello", session_id=sid)

    recall_res = brain.chat("What was my first question?", session_id=sid)
    text = recall_res.get("response", "")
    assert "What is Raspberry Pi 5?" in text


def test_case_9_provider_failure_honest_error():
    """Test 9: Simulated provider failure returns honest error without fake fallback text."""
    from ai.providers.base import OllamaProvider
    test_brain = JARVISBrain()
    for p in test_brain._providers:
        if isinstance(p, OllamaProvider):
            p.base_url = "http://127.0.0.1:9999"  # unreachable port

    res = test_brain.chat("Tell me a fact about space.", session_id="test_p1_case9")
    text = res.get("response", "")
    assert res.get("provider") == "error"
    assert "AI Provider Error" in text
    assert "unreachable" in text.lower() or "timed out" in text.lower()


def test_case_10_long_markdown_response(brain):
    """Test 10: Detailed technical question produces full non-truncated markdown response."""
    session_id = "test_p1_case10"
    res = brain.chat("Explain the difference between TCP and UDP protocols with examples.", session_id=session_id)
    text = res.get("response", "")
    assert len(text) > 400
    assert "tcp" in text.lower()
    assert "udp" in text.lower()


def test_case_11_streaming_and_cancellation(brain):
    """Test 11: SSE stream yields tokens progressively and cancels cleanly on client abort."""
    session_id = "test_p1_case11"
    stream_gen = brain.stream_chat("Write a short poem about Linux.", session_id=session_id)
    tokens_received = []
    for ev in stream_gen:
        if ev.get("type") == "token":
            tokens_received.append(ev.get("content"))
            if len(tokens_received) >= 2:
                break
    stream_gen.close()
    assert len(tokens_received) >= 2

    # Verify subsequent request works immediately
    next_res = brain.chat("What is 5 + 5?", session_id=session_id)
    assert "10" in next_res.get("response", "")


def test_case_12_conversation_persistence_across_restart():
    """Test 12: Session turns persist in SQLite DB across instance resets."""
    import ai.brain as bmod
    sid = "test_p1_case12"
    db.clear_session_messages(sid)

    inst1 = bmod.JARVISBrain()
    inst1.chat("What is the speed of light?", session_id=sid)

    # Re-instantiate
    inst2 = bmod.JARVISBrain()
    res = inst2.chat("What was my first question?", session_id=sid)
    assert "What is the speed of light?" in res.get("response", "")
