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
    OpenAIProvider, AnthropicProvider, NvidiaNimProvider,
    GenericOpenAIProvider, JARVIS_TOOLS
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

        # 6. NVIDIA NIM
        nvidia_key = os.environ.get("NVIDIA_API_KEY", "") or os.environ.get("NIM_API_KEY", "")
        nvidia_model = (cfg.get("nvidia", {}) or {}).get("model", "meta/llama-3.1-70b-instruct")
        self._providers.append(NvidiaNimProvider(api_key=nvidia_key, model=nvidia_model))

        # 7. Generic OpenAI-Compatible
        custom_cfg = cfg.get("custom", {}) or {}
        if custom_cfg.get("enabled"):
            self._providers.append(GenericOpenAIProvider(
                name=custom_cfg.get("name", "custom"),
                base_url=custom_cfg.get("base_url", "http://localhost:8080/v1"),
                api_key=custom_cfg.get("api_key", ""),
                model=custom_cfg.get("model", "custom-model"),
            ))


    def _get_provider(self, name: Optional[str] = None) -> Optional[AIProvider]:
        """Select provider by name or choose the first available provider."""
        if name:
            for p in self._providers:
                if p.name.lower() == name.lower():
                    if p.is_available():
                        self._active = p
                        return p
                    logger.warning(f"Requested provider {name} is not available")
                    break

        if self._active and self._active.is_available():
            return self._active

        for provider in self._providers:
            try:
                if provider.is_available():
                    if not self._active or self._active.name != provider.name:
                        logger.info(f"AI provider selected: {provider.name} ({getattr(provider, 'model', '?')})")
                        self._active = provider
                    return provider
            except Exception as e:
                logger.debug(f"Provider {provider.name} check failed: {e}")
        return None

    def set_active_provider(self, provider_name: str, model_name: Optional[str] = None) -> bool:
        """Explicitly switch active provider and optionally its model."""
        for p in self._providers:
            if p.name.lower() == provider_name.lower():
                if model_name:
                    p.model = model_name
                self._active = p
                logger.info(f"Active AI provider changed to {p.name} ({p.model})")
                return True
        return False

    def get_providers_status(self) -> Dict[str, Any]:
        """Return comprehensive list of providers, models, and availability."""
        provs = []
        for p in self._providers:
            avail = False
            try:
                avail = p.is_available()
            except Exception:
                avail = False
            provs.append({
                "name": p.name,
                "available": avail,
                "model": getattr(p, "model", ""),
                "models": p.list_models() if hasattr(p, "list_models") else [getattr(p, "model", "")],
                "active": bool(self._active and self._active.name == p.name),
            })
        return {
            "providers": provs,
            "active_provider": self._active.name if self._active else (provs[0]["name"] if provs else None),
            "active_model": getattr(self._active, "model", "") if self._active else "",
        }

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

    def stream_chat(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Stream chat response token-by-token.
        Yields events:
        - {"type": "start", "provider": ..., "model": ...}
        - {"type": "token", "content": "..."}
        - {"type": "done", "provider": ..., "model": ..., "ttft_ms": ..., "total_ms": ...}
        """
        import time
        from ai.local_engine import LocalIntelligenceEngine

        t_start = time.time()
        engine = LocalIntelligenceEngine()
        intent, _ = engine.classify_intent(user_message)

        FAST_PATH_INTENTS = {
            "robot_forward", "robot_backward", "robot_left", "robot_right",
            "robot_stop", "robot_estop", "servo_set", "system_status",
            "read_sensors", "calculate", "camera_capture", "memory_store",
            "list_files", "read_file", "write_file", "schedule_task",
            "identity", "help", "open_app", "create_calculator",
            "write_code", "run_code", "play_media", "stop_media",
            "pause_media", "resume_media", "media_status", "set_volume",
            "volume_up", "volume_down", "search_folder", "search_file",
            "open_folder", "open_folder_at", "open_file"
        }

        if intent in FAST_PATH_INTENTS:
            yield {"type": "start", "provider": "edge_fastpath", "model": "deterministic_hardware_engine"}
            local_res = engine.respond(user_message)
            resp_text = local_res.get("response", "Action completed.")
            self._history.append({"role": "user", "content": user_message})
            self._history.append({"role": "assistant", "content": resp_text})
            yield {"type": "token", "content": resp_text}
            yield {
                "type": "done",
                "provider": "edge_fastpath",
                "model": "deterministic_hardware_engine",
                "ttft_ms": int((time.time() - t_start) * 1000),
                "total_ms": int((time.time() - t_start) * 1000),
                "tokens": len(resp_text.split()),
            }
            return

        provider = self._get_provider(provider_name)
        if not provider:
            # Fallback
            fb = self._no_brain_response(user_message)
            resp_text = fb.get("response", "I processed your request.")
            yield {"type": "start", "provider": "local_engine", "model": "rule-based"}
            yield {"type": "token", "content": resp_text}
            yield {
                "type": "done",
                "provider": "local_engine",
                "model": "rule-based",
                "ttft_ms": 10,
                "total_ms": 20,
                "tokens": len(resp_text.split()),
            }
            return

        active_model = model_name or getattr(provider, "model", "")
        yield {"type": "start", "provider": provider.name, "model": active_model}

        self._history.append({"role": "user", "content": user_message})
        messages = self._history[-10:]

        full_response = ""
        ttft_recorded = False
        ttft_ms = 0

        try:
            for chunk in provider.stream_generate(messages, system=SYSTEM_PROMPT, model=active_model):
                token = chunk.get("token", "")
                if token:
                    if not ttft_recorded:
                        ttft_ms = int((time.time() - t_start) * 1000)
                        ttft_recorded = True
                    full_response += token
                    yield {"type": "token", "content": token}
                if chunk.get("done"):
                    break

            if not full_response:
                full_response = "I have processed your request."
                yield {"type": "token", "content": full_response}

            self._history.append({"role": "assistant", "content": full_response})
            yield {
                "type": "done",
                "provider": provider.name,
                "model": active_model,
                "ttft_ms": ttft_ms or int((time.time() - t_start) * 1000),
                "total_ms": int((time.time() - t_start) * 1000),
                "tokens": len(full_response.split()),
            }
        except Exception as e:
            logger.error(f"stream_chat failed: {e}")
            err_msg = f"\n[AI Stream Error: {e}]"
            yield {"type": "token", "content": err_msg}
            yield {
                "type": "done",
                "provider": provider.name,
                "model": active_model,
                "error": str(e),
                "total_ms": int((time.time() - t_start) * 1000),
            }

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
            "identity", "help", "open_app", "create_calculator",
            "write_code", "run_code", "play_media", "stop_media",
            "pause_media", "resume_media", "media_status", "set_volume",
            "volume_up", "volume_down", "search_folder", "search_file",
            "open_folder", "open_folder_at", "open_file"
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
