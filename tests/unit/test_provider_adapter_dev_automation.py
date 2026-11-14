import json
import subprocess

from ai.providers.base import AIProvider
from ai.providers.capabilities import build_developer_automation_report, detect_cli_capabilities
from ai.providers.llama_cpp_provider import LlamaCppProvider
from ai.providers.local_sim import SimulatedLocalProvider


class _DummyBrain:
    def get_providers_status(self):
        return {
            "providers": [
                {
                    "id": "openai",
                    "name": "openai",
                    "model": "gpt-4o-mini",
                    "status": "missing_key",
                    "credential_configured": False,
                    "verification": "missing_key",
                    "active": False,
                }
            ]
        }


def test_simulated_local_provider_conforms_to_adapter_contract():
    provider = SimulatedLocalProvider(model_name="sim-test", enabled=True)
    assert isinstance(provider, AIProvider)
    assert provider.is_available() is True
    assert provider.list_models() == ["sim-test"]

    msg_result = provider.generate([{"role": "user", "content": "hello world"}])
    assert isinstance(msg_result, dict)
    assert msg_result["provider"] == "simulated"
    assert msg_result["tool_calls"] == []
    assert "hello world"[:11] in msg_result["text"]

    prompt_result = provider.generate("direct prompt")
    assert isinstance(prompt_result, str)
    assert "direct prompt" in prompt_result

    info = provider.get_model_info()
    assert info["name"] == "simulated"
    assert info["enabled"] is True
    assert info["model"] == "sim-test"


def test_llama_cpp_provider_reports_unavailable_without_runtime(monkeypatch):
    provider = LlamaCppProvider(model_path="/nonexistent/model.gguf", enabled=True)

    def _raise_import_error(name, *args, **kwargs):
        if name == "llama_cpp":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", _raise_import_error)

    assert provider.is_available() is False
    result = provider.generate([{"role": "user", "content": "hi"}])
    assert result["provider"] == "llama_cpp"
    assert result["text"] == ""
    assert "error" in result
    info = provider.get_model_info()
    assert info["name"] == "llama_cpp"
    assert info["enabled"] is True
    assert info["available"] is False


def test_llama_cpp_provider_disabled_returns_structured_error():
    provider = LlamaCppProvider(enabled=False)
    result = provider.generate([{"role": "user", "content": "hi"}])
    assert result["error"] == "Provider disabled"
    assert provider.is_available() is False


def test_detect_cli_capabilities_reports_real_status_with_mocks(monkeypatch):
    def fake_which(name):
        return f"/usr/bin/{name}" if name in {"git", "python3"} else None

    def fake_run(command, capture_output, text, timeout, check):
        if command[:2] == ["git", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="git version 2.40.0\n", stderr="")
        if command[:2] == ["python3", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="Python 3.12.0\n", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="error")

    monkeypatch.setattr("ai.providers.capabilities.shutil.which", fake_which)
    monkeypatch.setattr("ai.providers.capabilities.subprocess.run", fake_run)

    caps = detect_cli_capabilities(["git", "python3", "gh"])
    by_name = {item["name"]: item for item in caps}
    assert by_name["git"]["status"] == "available"
    assert by_name["git"]["installed"] is True
    assert "git version" in by_name["git"]["probe"]["summary"]
    assert by_name["python3"]["status"] == "available"
    assert by_name["gh"]["status"] == "missing"
    assert by_name["gh"]["installed"] is False


def test_build_developer_automation_report_includes_provider_summary():
    report = build_developer_automation_report(brain=_DummyBrain())
    assert "cli_capabilities" in report
    assert isinstance(report["cli_capabilities"], list)
    assert report["providers"] == [
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "status": "missing_key",
            "credential_configured": False,
            "verification": "missing_key",
            "active": False,
        }
    ]
    # Ensure report is JSON serializable and contains no secret-like fields
    encoded = json.dumps(report)
    assert "api_key" not in encoded
    assert "Authorization" not in encoded
