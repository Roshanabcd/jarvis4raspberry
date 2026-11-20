"""
Ollama Local Reasoning Adapter for JARVIS OS.
Provides local model-based defect analysis, root-cause hypotheses, and offline repair proposals,
bridging directly to the safe JARVIS CodeEditorAgent for real filesystem modifications.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from tools.agents.adapters.base import BaseAgentAdapter
from tools.agents.models import AgentCapabilities, AgentMetadata, AgentStatus, AgentTask, ProblemContext

logger = logging.getLogger("JARVIS.OllamaAdapter")


class OllamaAdapter(BaseAgentAdapter):
    """Adapter for local Ollama server running at http://127.0.0.1:11434."""

    def __init__(self, endpoint: str = "http://127.0.0.1:11434"):
        super().__init__(agent_id="ollama", display_name="Local Ollama AI")
        self.endpoint = endpoint
        self._cached_meta: Optional[AgentMetadata] = None

    def discover(self) -> AgentMetadata:
        """Inspect running Ollama service and retrieve installed models."""
        url = f"{self.endpoint}/api/tags"
        models: List[str] = []
        is_ready = False
        error_msg = None

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-OS/Phase5"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    is_ready = len(models) > 0
        except Exception as e:
            error_msg = f"Cannot connect to Ollama at {self.endpoint}: {e}"

        caps = AgentCapabilities(
            supports_noninteractive=True,
            supports_file_editing=True,  # Bridged to CodeEditorAgent
            supports_shell=True,          # Bridged to TerminalManager
            supports_structured_output=True,
            supports_review=True,
            supports_sandbox=True,
            models=models or ["llama3.2:1b", "qwen3.5:4b"],
        )

        meta = AgentMetadata(
            id=self.agent_id,
            display_name=self.display_name,
            installed=True,
            authenticated=is_ready,
            version="0.5.x",
            cli_path=self.endpoint,
            capabilities=caps,
            permission_mode="local_safe",
            status=AgentStatus.READY if is_ready else AgentStatus.ERROR,
            error_message=error_msg,
        )
        self._cached_meta = meta
        return meta

    def health_check(self) -> bool:
        meta = self.discover()
        return meta.status == AgentStatus.READY

    def analyze_problem(self, context: ProblemContext, model: str = "llama3.2:1b") -> Dict[str, Any]:
        """Perform offline/local root-cause analysis using Ollama."""
        prompt = (
            f"You are JARVIS OS autonomous diagnostic engineer.\n"
            f"Analyze this error and explain the root cause and required fix concisely:\n\n"
            f"Problem: {context.original_request}\n"
            f"Error: {context.error_message}\n"
            f"Traceback:\n{context.traceback}\n"
            f"Working directory: {context.working_dir}\n"
            f"Affected file: {context.affected_component or 'unknown'}\n"
            f"Relevant files: {', '.join(context.relevant_files)}\n\n"
            f"Identify: 1. Root cause. 2. Specific fix. 3. Target snippet and replacement snippet."
        )

        try:
            req_data = json.dumps({
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 48},
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self.endpoint}/api/generate",
                data=req_data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                analysis_text = res_json.get("response", "")

            return {
                "status": "ok",
                "model": model,
                "analysis": analysis_text,
                "agent_id": self.agent_id,
            }
        except Exception as e:
            return {"status": "error", "message": f"Ollama generation failed: {e}"}

    def diagnose_problem(self, context: ProblemContext, model: str = "llama3.2:1b") -> Dict[str, Any]:
        """Alias for analyze_problem."""
        return self.analyze_problem(context, model=model)

    def execute_task(self, task: AgentTask, context: ProblemContext) -> Dict[str, Any]:
        """Execute local diagnostic analysis."""
        model = "llama3.2:1b"
        return self.analyze_problem(context, model=model)
