"""
Unit tests for JARVIS Brain and LocalIntelligenceEngine
"""
import pytest
from ai.brain import JARVISBrain
from ai.local_engine import LocalIntelligenceEngine
from ai.tools.executor import ToolExecutor


@pytest.fixture
def brain():
    return JARVISBrain()


@pytest.fixture
def engine():
    return LocalIntelligenceEngine()


class TestJARVISBrain:
    def test_brain_initialization(self, brain):
        assert brain is not None
        status = brain.status()
        assert "ollama" in status
        assert "gemini" in status
        assert "openai" in status

    def test_identity_intent(self, brain):
        result = brain.chat("Who are you, JARVIS?")
        assert result is not None
        assert "JARVIS" in result["response"]
        assert result["provider"] == "edge_fastpath"

    def test_robot_move_forward(self, brain):
        result = brain.chat("Move the robot forward at 70% speed")
        assert result is not None
        assert "Moving forward" in result["response"]
        assert "70%" in result["response"]
        assert any(t["tool"] == "robot_move" for t in result["tools_used"])

    def test_robot_estop(self, brain):
        result = brain.chat("Emergency stop the robot!")
        assert result is not None
        assert "emergency stop" in result["response"].lower() or "stopped" in result["response"].lower()
        assert any(t["tool"] == "robot_move" for t in result["tools_used"])

    def test_servo_control(self, brain):
        result = brain.chat("Set servo 0 to 90 degrees")
        assert result is not None
        assert "Servo channel 0" in result["response"]
        assert "90°" in result["response"]

    def test_sensor_readings(self, brain):
        result = brain.chat("Read all environmental sensors")
        assert result is not None
        assert "Temperature" in result["response"]
        assert any(t["tool"] == "read_sensors" for t in result["tools_used"])

    def test_system_status(self, brain):
        result = brain.chat("What is the system status and CPU temperature?")
        assert result is not None
        assert "CPU" in result["response"]
        assert any(t["tool"] == "get_system_status" for t in result["tools_used"])

    def test_math_calculation(self, brain):
        result = brain.chat("What is 1024 * 2 + 50?")
        assert result is not None
        assert "2098" in result["response"]

    def test_memory_storage(self, brain):
        result = brain.chat("Remember that the user is Tony Stark")
        assert result is not None
        assert "Stored in memory" in result["response"]


class TestLocalIntelligenceEngine:
    def test_classify_intents(self, engine):
        intent, _ = engine.classify_intent("drive forward at full speed")
        assert intent == "robot_forward"

        intent, _ = engine.classify_intent("e-stop immediately")
        assert intent == "robot_estop"

        intent, _ = engine.classify_intent("read sensor data")
        assert intent == "read_sensors"

        intent, _ = engine.classify_intent("what is the cpu temperature")
        assert intent == "system_status"

        intent, _ = engine.classify_intent("explain the concept of ultrasonic waves")
        assert intent == "general"


class TestToolExecutor:
    def test_execute_system_status(self):
        executor = ToolExecutor()
        raw = executor.execute("get_system_status", {})
        assert "cpu_pct" in raw or "cpu" in raw.lower()

    def test_execute_robot_move(self):
        executor = ToolExecutor()
        raw = executor.execute("robot_move", {"direction": "forward", "speed": 40})
        assert "direction" in raw or "status" in raw

    def test_execute_sensors(self):
        executor = ToolExecutor()
        raw = executor.execute("read_sensors", {})
        assert "temperature" in raw or "readings" in raw
