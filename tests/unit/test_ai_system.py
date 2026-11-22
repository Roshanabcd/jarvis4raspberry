"""Unit tests for the JARVIS OS AI provider subsystem, model router, and specialized agents."""

import json
from unittest.mock import MagicMock, patch
import pytest
import requests
from ai.agents.file_agent import FileAgent
from ai.agents.main_agent import MainAgent
from ai.agents.robotics_agent import RoboticsAgent
from ai.agents.sensor_agent import SensorAgent
from ai.agents.system_agent import SystemAgent
from ai.agents.vision_agent import VisionAgent
from ai.prompts.system_prompt import JARVIS_SYSTEM_PROMPT
from ai.providers.base import AIProvider
from ai.providers.ollama_provider import OllamaProvider
from ai.providers.openai_provider import OpenAICompatibleProvider
from ai.router.model_router import ModelRouter


# ---------------------------------------------------------------------------
# Test AIProvider and Local Simulation
# ---------------------------------------------------------------------------
def test_ai_provider_subclass():
    class CustomProvider(AIProvider):
        def generate(self, prompt, context=None, task_type="general", **kwargs):
            return "ok"

        def is_available(self):
            return True

        def get_model_info(self):
            return {"name": "custom"}

    provider = CustomProvider()
    assert provider.is_available() is True
    assert provider.generate("test") == "ok"
    assert provider.get_model_info() == {"name": "custom"}


# ---------------------------------------------------------------------------
# Test OllamaProvider
# ---------------------------------------------------------------------------
def test_ollama_provider_init():
    provider = OllamaProvider(base_url="http://127.0.0.1:11434", model="llama3.2")
    info = provider.get_model_info()
    assert info["name"] == "ollama"
    assert info["model"] == "llama3.2"
    assert info["base_url"] == "http://127.0.0.1:11434"


@patch("requests.get")
def test_ollama_provider_availability(mock_get):
    # Available case
    provider = OllamaProvider(base_url="http://localhost:11434")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp
    assert provider.is_available() is True

    # Server error - new provider instance to avoid cache
    provider = OllamaProvider(base_url="http://localhost:11434")
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_get.return_value = mock_resp
    assert provider.is_available() is False

    # Connection error - new provider instance
    provider = OllamaProvider(base_url="http://localhost:11434")
    mock_get.side_effect = requests.ConnectionError("Connection refused")
    assert provider.is_available() is False


@patch("requests.post")
def test_ollama_provider_generate_success(mock_post):
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "All systems nominal, sir.", "done": True}
    mock_post.return_value = mock_resp

    result = provider.generate("Report status", context={"system_prompt": "You are JARVIS."})
    assert result == "All systems nominal, sir."

    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["model"] == "llama3.2"
    assert payload["prompt"] == "Report status"
    assert payload["system"] == "You are JARVIS."
    assert payload["stream"] is False


@patch("requests.post")
def test_ollama_provider_generate_failure_returns_none(mock_post):
    provider = OllamaProvider(base_url="http://localhost:11434")

    # Connection error returns None
    mock_post.side_effect = requests.ConnectionError("Connection refused")
    assert provider.generate("Test prompt") is None

    # HTTP 500 returns None
    mock_post.side_effect = None
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_post.return_value = mock_resp
    assert provider.generate("Test prompt") is None

    # Disabled provider returns None without network call
    provider.enabled = False
    assert provider.generate("Test prompt") is None


# ---------------------------------------------------------------------------
# Test OpenAICompatibleProvider
# ---------------------------------------------------------------------------
def test_openai_provider_missing_key_graceful():
    provider = OpenAICompatibleProvider(api_key="", enabled=True)
    assert provider.is_available() is False
    assert provider.generate("Hello") is None


def test_openai_provider_init_and_info():
    provider = OpenAICompatibleProvider(
        api_key="sk-test-fake-key",
        model="gpt-4o",
        base_url="https://api.openai.com/v1",
        enabled=True,
    )
    assert provider.is_available() is True
    info = provider.get_model_info()
    assert info["name"] == "openai"
    assert info["model"] == "gpt-4o"
    assert info["has_api_key"] is True


@patch("requests.post")
def test_openai_provider_generate_success(mock_post):
    provider = OpenAICompatibleProvider(api_key="sk-test", enabled=True)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {"message": {"role": "assistant", "content": "Telemetry nominal."}}
        ]
    }
    mock_post.return_value = mock_resp

    result = provider.generate("System check", context={"system_prompt": "You are JARVIS."})
    assert result == "Telemetry nominal."

    payload = mock_post.call_args[1]["json"]
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"


@patch("requests.post")
def test_openai_provider_connection_error_returns_none(mock_post):
    provider = OpenAICompatibleProvider(api_key="sk-test", enabled=True)
    mock_post.side_effect = requests.ConnectionError("DNS failure")
    assert provider.generate("Ping") is None


# ---------------------------------------------------------------------------
# Test ModelRouter
# ---------------------------------------------------------------------------
def test_model_router_preferences():
    ollama_mock = MagicMock(spec=AIProvider)
    openai_mock = MagicMock(spec=AIProvider)

    ollama_mock.is_available.return_value = True
    openai_mock.is_available.return_value = True

    ollama_mock.generate.return_value = "Ollama response"
    openai_mock.generate.return_value = "OpenAI response"

    router = ModelRouter(
        providers={"ollama": ollama_mock, "openai": openai_mock},
        fallback_message="Offline mode",
    )
    # Mock internet connectivity as True
    router.check_internet_connectivity = MagicMock(return_value=True)

    # 1. 'simple' prefers ollama
    assert router.route("Hello", task_type="simple") == "Ollama response"
    ollama_mock.generate.assert_called_with("Hello", context=None, task_type="simple")

    # 2. 'code' prefers openai then ollama
    ollama_mock.generate.reset_mock()
    openai_mock.generate.reset_mock()
    assert router.route("Write python code", task_type="code") == "OpenAI response"
    openai_mock.generate.assert_called_with("Write python code", context=None, task_type="code")
    ollama_mock.generate.assert_not_called()

    # 3. 'vision' prefers openai then ollama
    ollama_mock.generate.reset_mock()
    openai_mock.generate.reset_mock()
    assert router.route("Analyze image", task_type="vision") == "OpenAI response"
    openai_mock.generate.assert_called_with("Analyze image", context=None, task_type="vision")

    # 4. 'general' tries ollama first then openai
    ollama_mock.generate.reset_mock()
    openai_mock.generate.reset_mock()
    assert router.route("General query", task_type="general") == "Ollama response"
    ollama_mock.generate.assert_called_with("General query", context=None, task_type="general")


def test_model_router_fallback_when_all_fail():
    ollama_mock = MagicMock(spec=AIProvider)
    openai_mock = MagicMock(spec=AIProvider)

    ollama_mock.is_available.return_value = False
    openai_mock.is_available.return_value = False

    router = ModelRouter(
        providers={"ollama": ollama_mock, "openai": openai_mock},
        fallback_message="I am operating in offline mode. Cloud AI is unavailable.",
    )
    router.check_internet_connectivity = MagicMock(return_value=False)

    res = router.route("Test query", task_type="general")
    assert res == "I am operating in offline mode. Cloud AI is unavailable."


def test_model_router_status():
    ollama_mock = MagicMock(spec=AIProvider)
    openai_mock = MagicMock(spec=AIProvider)

    ollama_mock.is_available.return_value = True
    openai_mock.is_available.return_value = False

    router = ModelRouter(providers={"ollama": ollama_mock, "openai": openai_mock})
    router.check_internet_connectivity = MagicMock(return_value=True)

    status = router.get_status()
    assert status["internet_connected"] is True
    assert status["ollama"] is True
    assert status["openai"] is False


# ---------------------------------------------------------------------------
# Test RoboticsAgent
# ---------------------------------------------------------------------------
def test_robotics_agent_forward_and_estop():
    agent = RoboticsAgent()
    mock_robot = MagicMock()
    agent.robot = mock_robot

    # Forward
    res_str = agent.handle("move forward speed 75")
    res = json.loads(res_str)
    assert res["success"] is True
    assert res["action"] == "forward"
    assert res["details"]["speed"] == 75
    mock_robot.forward.assert_called_with(75)

    # Emergency stop
    res_str = agent.handle("emergency stop immediately")
    res = json.loads(res_str)
    assert res["success"] is True
    assert res["action"] == "emergency_stop"
    mock_robot.emergency_stop.assert_called_once()

    # Servo
    res_str = agent.handle("set servo 2 to 120")
    res = json.loads(res_str)
    assert res["success"] is True
    assert res["action"] == "set_servo"
    assert res["details"]["channel"] == 2
    assert res["details"]["angle"] == 120
    mock_robot.set_servo.assert_called_with(2, 120)


# ---------------------------------------------------------------------------
# Test SystemAgent
# ---------------------------------------------------------------------------
def test_system_agent_natural_response():
    agent = SystemAgent()
    agent._fetch_status = MagicMock(return_value={
        "os": "Linux",
        "arch": "aarch64",
        "cpu_usage_percent": 25.0,
        "memory_total_mb": 8000,
        "memory_used_mb": 2000,
        "temperature_c": 45.0,
    })

    # CPU query
    cpu_res = agent.handle("what is the cpu usage?")
    assert "25.0%" in cpu_res
    assert "45.0°C" in cpu_res

    # RAM query
    ram_res = agent.handle("check ram utilization")
    assert "2000 MB" in ram_res
    assert "25.0%" in ram_res

    # General telemetry
    general_res = agent.handle("system status")
    assert "Linux (aarch64)" in general_res


# ---------------------------------------------------------------------------
# Test MainAgent Keyword Delegation
# ---------------------------------------------------------------------------
def test_main_agent_delegation():
    mock_router = MagicMock(spec=ModelRouter)
    mock_robotics = MagicMock(spec=RoboticsAgent)
    mock_sensor = MagicMock(spec=SensorAgent)
    mock_vision = MagicMock(spec=VisionAgent)
    mock_file = MagicMock(spec=FileAgent)
    mock_system = MagicMock(spec=SystemAgent)

    mock_robotics.name = "RoboticsAgent"
    mock_sensor.name = "SensorAgent"
    mock_vision.name = "VisionAgent"
    mock_file.name = "FileAgent"
    mock_system.name = "SystemAgent"

    mock_robotics.handle.return_value = "Robot moved"
    mock_sensor.handle.return_value = "Sensor 22C"
    mock_vision.handle.return_value = "Vision target detected"
    mock_file.handle.return_value = "File read ok"
    mock_system.handle.return_value = "System nominal"
    mock_router.route.return_value = "AI router answer"

    main_agent = MainAgent(
        router=mock_router,
        robotics_agent=mock_robotics,
        sensor_agent=mock_sensor,
        vision_agent=mock_vision,
        file_agent=mock_file,
        system_agent=mock_system,
    )

    # 1. robot / motor / servo
    assert main_agent.handle("activate motor 1") == "Robot moved"
    mock_robotics.handle.assert_called_once()

    # 2. temp / sensor / bme
    assert main_agent.handle("read bme sensor") == "Sensor 22C"
    mock_sensor.handle.assert_called_once()

    # 3. camera / vision / see
    assert main_agent.handle("can you see anything on the camera?") == "Vision target detected"
    mock_vision.handle.assert_called_once()

    # 4. file / read / write
    assert main_agent.handle("read the log file") == "File read ok"
    mock_file.handle.assert_called_once()

    # 5. system / cpu / ram / disk
    assert main_agent.handle("what is the cpu usage?") == "System nominal"
    mock_system.handle.assert_called_once()

    # 6. Fallback general query -> ModelRouter
    assert main_agent.handle("tell me about quantum computing") == "AI router answer"
    mock_router.route.assert_called_once()


# ---------------------------------------------------------------------------
# Test System Prompt Rules
# ---------------------------------------------------------------------------
def test_system_prompt_principles():
    assert "As an AI" not in JARVIS_SYSTEM_PROMPT
    assert "JARVIS" in JARVIS_SYSTEM_PROMPT
    assert "Raspberry Pi" in JARVIS_SYSTEM_PROMPT
    assert "Never pretend actions succeeded" in JARVIS_SYSTEM_PROMPT or "Operational Honesty" in JARVIS_SYSTEM_PROMPT
