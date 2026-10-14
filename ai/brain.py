"""
JARVIS Brain — Production AI Orchestrator
Selects the best available AI provider, runs inference with tool calling,
executes tools, and returns a final natural language response.

Provider priority: Ollama → Gemini → OpenAI → Anthropic
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from config.config_manager import config
from ai.providers.base import (
    AIProvider, OllamaProvider, GeminiProvider,
    OpenAIProvider, AnthropicProvider, JARVIS_TOOLS
)
from ai.tools.executor import ToolExecutor

logger = logging.getLogger("JARVIS.Brain")

SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System), an advanced AI operating environment \
running on a Raspberry Pi 5. You are calm, precise, professional, and highly capable.

Your capabilities include:
- Controlling a robot (motors forward/backward/left/right/stop, emergency stop, servos)
- Reading environmental sensors (temperature, humidity, light, distance, motion)
- Capturing camera images and describing scenes
- Reading and writing files in the workspace
- Searching the web for information
- Storing and retrieving memories
- Getting system status (CPU, RAM, temperature, disk)
- Running safe shell commands
- Scheduling recurring tasks
- Speaking aloud via text-to-speech

RULES:
1. When the user asks you to do something physical, USE THE TOOLS — don't just describe what you would do.
2. Always execute robot commands when asked. Safety is enforced at the hardware level.
3. For questions about the real world (weather, news, facts), use web_search.
4. Store important user preferences and facts in memory.
5. Be concise but complete. After using tools, always summarise the result clearly.
6. Never say "I am operating in offline mode" — if a tool fails, explain why and what you did instead.
7. You are JARVIS, not an AI assistant. Speak with confidence and capability.
"""

MAX_TOOL_ROUNDS = 5  # Prevent infinite loops


class JARVISBrain:
    """
    The production AI brain for JARVIS OS.
    Runs real inference using the best available provider with tool calling.
    """

    def __init__(self) -> None:
        self._providers: List[AIProvider] = []
        self._active: Optional[AIProvider] = None
        self._executor = ToolExecutor()
        self._history: List[Dict] = []   # Conversation history
        self._init_providers()

    def _init_providers(self) -> None:
        """Build provider list from config + environment variables.
        Priority: Ollama → llama_cpp → Gemini → OpenAI → Anthropic
        """
        cfg = config.get("ai", {}) or {}

        # 1. Ollama (local — fastest when running)
        ollama_url = (cfg.get("ollama", {}) or {}).get("base_url", "http://127.0.0.1:11434")
        ollama_model = (cfg.get("ollama", {}) or {}).get("model", "llama3.2:1b")
        self._providers.append(OllamaProvider(base_url=ollama_url, model=ollama_model))

        # 2. llama-cpp-python (local GGUF — no Ollama needed)
        try:
            from ai.providers.llama_cpp_provider import LlamaCppProvider
            n_threads = int(os.environ.get("LLAMA_THREADS", "4"))
            self._providers.append(LlamaCppProvider(n_threads=n_threads))
        except Exception:
            pass  # optional dependency

        # 3. Google Gemini
        gemini_key = (
            os.environ.get("GOOGLE_API_KEY") or
            os.environ.get("GEMINI_API_KEY") or
            config.get("gemini_api_key", "")
        )
        gemini_model = (cfg.get("gemini", {}) or {}).get("model", "gemini-2.0-flash")
        self._providers.append(GeminiProvider(api_key=gemini_key, model=gemini_model))

        # 4. OpenAI (also works with Groq, Together, local vLLM via OPENAI_BASE_URL)
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        openai_model = (cfg.get("openai", {}) or {}).get("model", "gpt-4o-mini")
        openai_url = os.environ.get("OPENAI_BASE_URL")
        self._providers.append(OpenAIProvider(api_key=openai_key, model=openai_model,
                                               base_url=openai_url))

        # 5. Anthropic
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._providers.append(AnthropicProvider(api_key=anthropic_key))


    def _get_provider(self) -> Optional[AIProvider]:
        """Select the first available provider."""
        for provider in self._providers:
            try:
                if provider.is_available():
                    if not self._active or self._active.name != provider.name:
                        logger.info(f"AI provider: {provider.name} ({provider.model})")
                        self._active = provider
                    return provider
            except Exception as e:
                logger.debug(f"Provider {provider.name} check failed: {e}")
        return None

    def status(self) -> Dict[str, Any]:
        """Return status of all providers."""
        result = {}
        for p in self._providers:
            try:
                avail = p.is_available()
            except Exception:
                avail = False
            result[p.name] = {"available": avail, "model": getattr(p, "model", "?")}
        result["active"] = self._active.name if self._active else None
        return result

    def chat(self, user_message: str, use_tools: bool = True,
             session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Hybrid Intelligence Engine:
        1. Fast-Path: Deterministic execution (<5ms) for robotics hardware, sensors,
           safety e-stops, system diagnostics, and math calculations.
        2. Neural LLM: For general knowledge, conversational reasoning, explanations,
           creative prompts, and open dialogue (Ollama / Gemini / OpenAI / Anthropic).
        3. Fallback: Local rule engine if no LLM is reachable.
        """
        from ai.local_engine import LocalIntelligenceEngine
        engine = LocalIntelligenceEngine()
        intent, _ = engine.classify_intent(user_message)

        FAST_PATH_INTENTS = {
            "robot_forward", "robot_backward", "robot_left", "robot_right",
            "robot_stop", "robot_estop", "servo_set", "system_status",
            "read_sensors", "calculate", "camera_capture", "memory_store",
            "list_files", "read_file", "write_file", "schedule_task",
            "identity", "help"
        }

        if intent in FAST_PATH_INTENTS:
            logger.info(f"Fast-path execution for intent: {intent}")
            local_res = engine.respond(user_message)
            resp_text = local_res.get("response", "Action completed.")
            self._history.append({"role": "user", "content": user_message})
            self._history.append({"role": "assistant", "content": resp_text})
            return {
                "response": resp_text,
                "provider": "edge_fastpath",
                "model": "deterministic_hardware_engine",
                "tools_used": [{"tool": t} for t in local_res.get("tools_used", [])],
                "rounds": 1,
                "tokens": 0,
            }

        provider = self._get_provider()

        if not provider:
            return self._no_brain_response(user_message)

        # Add to history
        self._history.append({"role": "user", "content": user_message})

        # Keep history to last 10 turns
        messages = self._history[-10:]
        tools = JARVIS_TOOLS if use_tools else None
        tools_used = []
        rounds = 0

        try:
            while rounds < MAX_TOOL_ROUNDS:
                rounds += 1
                result = provider.generate(
                    messages=messages,
                    tools=tools,
                    system=SYSTEM_PROMPT
                )

                if result.get("error") and not result.get("text") and not result.get("tool_calls"):
                    logger.warning(f"Provider {provider.name} error: {result['error']}")
                    # Try next provider
                    for p in self._providers:
                        if p.name != provider.name and p.is_available():
                            provider = p
                            logger.info(f"Switched to provider: {provider.name}")
                            break
                    else:
                        return self._no_brain_response(user_message)

                tool_calls = result.get("tool_calls", [])

                if not tool_calls:
                    # Final text response
                    text = result.get("text", "").strip()
                    if not text:
                        text = "I processed your request."
                    self._history.append({"role": "assistant", "content": text})
                    return {
                        "response": text,
                        "provider": result.get("provider", provider.name),
                        "model": result.get("model", ""),
                        "tools_used": tools_used,
                        "rounds": rounds,
                        "tokens": result.get("tokens", 0),
                    }

                # Execute tool calls
                tool_results = []
                for tc in tool_calls:
                    tool_name = tc.get("name", "")
                    tool_args = tc.get("args", {})
                    logger.info(f"Executing tool: {tool_name}({json.dumps(tool_args)[:80]})")

                    tool_result = self._executor.execute(tool_name, tool_args)
                    tools_used.append({"tool": tool_name, "args": tool_args,
                                       "result_preview": tool_result[:120]})

                    tool_results.append({
                        "role": "tool",
                        "content": f"Tool {tool_name} result: {tool_result}",
                        "tool_call_id": tc.get("id", tool_name),
                    })

                # Add assistant message and tool results to conversation
                assistant_msg = result.get("text", "")
                if assistant_msg:
                    messages.append({"role": "assistant", "content": assistant_msg})
                messages.extend(tool_results)

        except Exception as e:
            logger.error(f"Brain error: {e}")
            return {"response": f"I encountered an error: {e}", "provider": "error",
                    "tools_used": [], "rounds": rounds}

        return {"response": "I completed your request.", "provider": provider.name,
                "tools_used": tools_used, "rounds": rounds}

    def _no_brain_response(self, user_message: str) -> Dict[str, Any]:
        """
        Full local intelligence fallback using the LocalIntelligenceEngine.
        Actually executes tasks — no "offline mode" cop-out.
        """
        from ai.local_engine import LocalIntelligenceEngine
        engine = LocalIntelligenceEngine()
        result = engine.respond(user_message)
        return {
            "response": result.get("response", "I processed your request."),
            "provider": "local_engine",
            "model": "rule-based+tools",
            "tools_used": [{"tool": t} for t in result.get("tools_used", [])],
            "rounds": 1,
        }



# Module-level singleton
_brain: Optional[JARVISBrain] = None

def get_brain() -> JARVISBrain:
    global _brain
    if _brain is None:
        _brain = JARVISBrain()
    return _brain
