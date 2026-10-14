"""
JARVIS AI Brain — Multi-Provider with Tool Calling
Supports: Ollama (local), Google Gemini, OpenAI, Anthropic Claude
Priority: Ollama → Gemini → OpenAI → Anthropic → Echo fallback

Each provider implements real inference — no stub responses.
"""
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS.AI.Brain")

# ──────────────────────────────────────────────
# Tool call schema
# ──────────────────────────────────────────────

JARVIS_TOOLS: List[Dict] = [
    {
        "name": "robot_move",
        "description": "Move the robot. direction: forward|backward|left|right|stop|estop. speed: 0-100.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["forward", "backward", "left", "right", "stop", "estop"]},
                "speed": {"type": "integer", "minimum": 0, "maximum": 100, "default": 50},
                "duration_ms": {"type": "integer", "default": 0}
            },
            "required": ["direction"]
        }
    },
    {
        "name": "servo_set",
        "description": "Set a servo channel to an angle.",
        "parameters": {
            "type": "object",
            "properties": {
                "channel": {"type": "integer", "minimum": 0, "maximum": 15},
                "angle": {"type": "integer", "minimum": 0, "maximum": 180}
            },
            "required": ["channel", "angle"]
        }
    },
    {
        "name": "read_sensors",
        "description": "Read all environmental sensors (temperature, humidity, light, distance, motion).",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_system_status",
        "description": "Get CPU, RAM, temperature, disk usage, and robot state.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "camera_capture",
        "description": "Capture a photo from the camera and describe what is seen.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "memory_store",
        "description": "Store a fact or piece of information in long-term memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["KNOWLEDGE", "USER", "TASK", "SYSTEM", "CONVERSATION", "PREFERENCE", "EVENT"]},
                "content": {"type": "string"}
            },
            "required": ["category", "content"]
        }
    },
    {
        "name": "memory_search",
        "description": "Search long-term memory for relevant information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "run_command",
        "description": "Run an allowed shell command (ls, ps, df, free, uname, etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "args": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file from the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "schedule_task",
        "description": "Schedule a recurring or one-time task.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "schedule": {"type": "string", "description": "HH:MM for daily, 'every Ns' for interval, 'once'"},
                "command": {"type": "string"}
            },
            "required": ["name", "schedule", "command"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "speak",
        "description": "Speak a message aloud using text-to-speech.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "open_app",
        "description": "Open a desktop application like VS Code, text editor, terminal, or browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "e.g. 'code', 'vs code', 'mousepad', 'terminal'"},
                "target": {"type": "string", "description": "Optional file path to open in the app"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "run_code",
        "description": "Run Python or Bash code directly and get output.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Source code string to execute"},
                "file_path": {"type": "string", "description": "Path to file to execute"},
                "language": {"type": "string", "enum": ["python", "bash"], "default": "python"}
            }
        }
    }
]


# ──────────────────────────────────────────────
# Base Provider
# ──────────────────────────────────────────────

class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def generate(self, messages: List[Dict], tools: Optional[List] = None,
                 system: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns: {
            "text": str,                       # final text response
            "tool_calls": [{"name":..., "args":{...}}],  # tool calls requested
            "provider": str,
            "model": str,
            "tokens": int,
        }
        """
        ...

    def generate_simple(self, prompt: str, system: Optional[str] = None) -> str:
        """Convenience: single prompt → text response."""
        result = self.generate(
            messages=[{"role": "user", "content": prompt}],
            system=system
        )
        return result.get("text", "")


# ──────────────────────────────────────────────
# Ollama (local — Llama3, Mistral, etc.)
# ──────────────────────────────────────────────

class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "llama3.2:3b") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        try:
            import requests
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                self._available = bool(models)
                if models:
                    if self.model in models:
                        pass
                    elif any("llama3.2:1b" in m for m in models):
                        self.model = next(m for m in models if "llama3.2:1b" in m)
                    elif any("1b" in m for m in models):
                        self.model = next(m for m in models if "1b" in m)
                    else:
                        self.model = models[0]
                    logger.info(f"Ollama using model: {self.model}")
                return self._available
        except Exception:
            pass
        self._available = False
        return False

    def generate(self, messages: List[Dict], tools: Optional[List] = None,
                 system: Optional[str] = None) -> Dict[str, Any]:
        import requests

        chat_messages = []
        sys_prompt = system or "You are JARVIS, an advanced AI operating environment on Raspberry Pi 5."
        if tools:
            tool_desc = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)
            sys_prompt += (
                f"\n\nAvailable tools:\n{tool_desc}\n\n"
                "If you need to perform an action (e.g. open an application, write a file, run code, or control hardware), respond with:\n"
                "TOOL_CALL: {\"name\": \"tool_name\", \"args\": {...}}\n"
                "Otherwise answer directly and concisely."
            )
        chat_messages.append({"role": "system", "content": sys_prompt})

        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "tool":
                chat_messages.append({"role": "user", "content": f"[Tool Result]: {content}"})
            else:
                chat_messages.append({"role": role, "content": content})

        try:
            r = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 256}
                },
                timeout=60
            )
            r.raise_for_status()
            data = r.json()
            msg = data.get("message", {})
            text = (msg.get("content") or msg.get("thinking") or "").strip()
            tool_calls = self._extract_tool_calls(text)
            if tool_calls and "TOOL_CALL:" in text:
                text = text[:text.find("TOOL_CALL:")].strip()
            return {"text": text, "tool_calls": tool_calls,
                    "provider": "ollama", "model": self.model, "tokens": data.get("eval_count", 0)}
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"text": "", "tool_calls": [], "provider": "ollama", "model": self.model,
                    "tokens": 0, "error": str(e)}

    def _extract_tool_calls(self, text: str) -> List[Dict]:
        calls = []
        import re
        for m in re.finditer(r'TOOL_CALL:\s*(\{.*?\})', text, re.DOTALL):
            try:
                data = json.loads(m.group(1))
                calls.append({"name": data.get("name"), "args": data.get("args", {})})
            except Exception:
                pass
        return calls


# ──────────────────────────────────────────────
# Google Gemini
# ──────────────────────────────────────────────

class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: Optional[str] = None,
                 model: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self._client = None

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import google.generativeai as genai  # noqa
            return True
        except ImportError:
            return False

    def _get_client(self):
        if not self._client:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai
        return self._client

    def generate(self, messages: List[Dict], tools: Optional[List] = None,
                 system: Optional[str] = None) -> Dict[str, Any]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            # Build Gemini tool declarations
            gemini_tools = None
            if tools:
                from google.generativeai.types import FunctionDeclaration, Tool
                decls = []
                for t in tools:
                    decls.append(FunctionDeclaration(
                        name=t["name"],
                        description=t["description"],
                        parameters=t.get("parameters", {})
                    ))
                gemini_tools = [Tool(function_declarations=decls)]

            model_kwargs = {"model_name": self.model}
            if system:
                model_kwargs["system_instruction"] = system

            model = genai.GenerativeModel(**model_kwargs, tools=gemini_tools)

            # Convert messages to Gemini format
            history = []
            last_user_msg = ""
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "user":
                    last_user_msg = content
                    if history:
                        history.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    history.append({"role": "model", "parts": [content]})

            chat = model.start_chat(history=history[:-1] if len(history) > 1 else [])
            response = chat.send_message(last_user_msg or messages[-1].get("content", ""))

            text = ""
            tool_calls = []
            for part in response.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append({"name": fc.name, "args": dict(fc.args)})

            return {"text": text.strip(), "tool_calls": tool_calls,
                    "provider": "gemini", "model": self.model,
                    "tokens": response.usage_metadata.total_token_count if hasattr(response, "usage_metadata") else 0}
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return {"text": "", "tool_calls": [], "provider": "gemini",
                    "model": self.model, "tokens": 0, "error": str(e)}


# ──────────────────────────────────────────────
# OpenAI (also works with compatible APIs like Groq, Together, etc.)
# ──────────────────────────────────────────────

class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None,
                 model: str = "gpt-4o-mini",
                 base_url: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def is_available(self) -> bool:
        if not self.api_key or self.api_key.startswith("sk-REPLACE"):
            return False
        try:
            import openai  # noqa
            return True
        except ImportError:
            return False

    def generate(self, messages: List[Dict], tools: Optional[List] = None,
                 system: Optional[str] = None) -> Dict[str, Any]:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

            oai_messages = []
            if system:
                oai_messages.append({"role": "system", "content": system})
            oai_messages.extend(messages)

            kwargs: Dict[str, Any] = {"model": self.model, "messages": oai_messages, "max_tokens": 1024}
            if tools:
                kwargs["tools"] = [{"type": "function", "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters", {})
                }} for t in tools]
                kwargs["tool_choice"] = "auto"

            resp = client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message
            text = msg.content or ""
            tool_calls = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}
                    tool_calls.append({"name": tc.function.name, "args": args, "id": tc.id})

            return {"text": text.strip(), "tool_calls": tool_calls,
                    "provider": "openai", "model": self.model,
                    "tokens": resp.usage.total_tokens if resp.usage else 0}
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return {"text": "", "tool_calls": [], "provider": "openai",
                    "model": self.model, "tokens": 0, "error": str(e)}


# ──────────────────────────────────────────────
# Anthropic Claude
# ──────────────────────────────────────────────

class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None,
                 model: str = "claude-3-haiku-20240307") -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model

    def is_available(self) -> bool:
        if not self.api_key or self.api_key.startswith("sk-ant-REPLACE"):
            return False
        try:
            import anthropic  # noqa
            return True
        except ImportError:
            return False

    def generate(self, messages: List[Dict], tools: Optional[List] = None,
                 system: Optional[str] = None) -> Dict[str, Any]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)

            ant_tools = None
            if tools:
                ant_tools = [{"name": t["name"], "description": t["description"],
                               "input_schema": t.get("parameters", {"type": "object", "properties": {}})}
                              for t in tools]

            kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": 1024,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system
            if ant_tools:
                kwargs["tools"] = ant_tools

            resp = client.messages.create(**kwargs)
            text = ""
            tool_calls = []
            for block in resp.content:
                if block.type == "text":
                    text += block.text
                elif block.type == "tool_use":
                    tool_calls.append({"name": block.name, "args": block.input, "id": block.id})

            return {"text": text.strip(), "tool_calls": tool_calls,
                    "provider": "anthropic", "model": self.model,
                    "tokens": resp.usage.input_tokens + resp.usage.output_tokens}
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return {"text": "", "tool_calls": [], "provider": "anthropic",
                    "model": self.model, "tokens": 0, "error": str(e)}
