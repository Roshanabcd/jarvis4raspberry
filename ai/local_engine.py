"""
JARVIS Local Intelligence Engine
A rule-based + template engine that provides full JARVIS capability
without requiring an external LLM. Uses NLP intent classification,
real tool execution, and structured responses.

This is NOT a "I'm offline" fallback — it actually DOES the tasks.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.LocalEngine")

# Intent patterns → (intent_name, tool_to_call, template_response)
INTENTS = [
    # Math (highest priority to not get caught by web_search "what is")
    (r"\d+\s*[\+\-\*\/]\s*\d+", "calculate", None),
    (r"\b(calculate|compute|math|solve)\s+([\d\+\-\*\/\^\(\)\.\s]+)", "calculate", None),

    # Robot control
    (r"\b(go|move|drive|navigate)\b.*(forward|ahead|straight)", "robot_forward", None),
    (r"\b(go|move|drive)\b.*(back|backward|reverse)", "robot_backward", None),
    (r"\b(turn|rotate|spin|go|move)\b.*(left)\b", "robot_left", None),
    (r"\b(turn|rotate|spin|go|move)\b.*(right)\b", "robot_right", None),
    (r"\b(emergency stop|e-stop|estop|kill switch)\b", "robot_estop", None),
    (r"\b(stop|halt|freeze|pause)\b", "robot_stop", None),
    (r"\bservo\s+(\d+)\s+(?:to\s+)?(\d+)\b", "servo_set", None),

    # System (before sensors to take priority)
    (r"\b(status|cpu|cpu usage|processor|ram|memory usage|disk|system info|health|system status)\b", "system_status", None),
    (r"\b(how much (memory|ram)|memory available|uptime)\b", "system_status", None),

    # Sensors
    (r"\b(sensors?|temperatures?|humidity|pressure|light|lux|distance|motion|pir|ultrasonic)\b", "read_sensors", None),
    (r"\b(what.*(temp|hot|cold|warm)|how warm|how cold)\b", "read_sensors", None),

    # Camera
    (r"\b(camera|capture|photo|picture|image|take a (photo|picture)|what (do you see|can you see))\b", "camera_capture", None),
    (r"\b(look|see|observe|describe (what|the|around))\b", "camera_capture", None),

    # Memory
    (r"\b(remember|store|save|note|record)\s+(.+)", "memory_store", None),
    (r"\b(what do you remember|recall|search memory|look up|what do you know about|tell me about|do you know)\s+(.+)?", "memory_search", None),

    # File
    (r"\b(read|open|cat|display)\s+file\s+(\S+)", "read_file", None),
    (r"\b(cat|display)\s+(\S+\.\w+)", "read_file", None),
    (r"\b(write|create|save|make)\s+(?:file\s+)?(\S+)", "write_file", None),
    (r"\b(list files?|ls|dir|directory)\b", "list_files", None),

    # Web search
    (r"\b(search|google|look up|find|what is|who is|when (did|was)|where (is|was))\s+(.+)", "web_search", None),
    (r"\b(news|latest|current|today's?)\b", "web_search", None),
    (r"\bweather\b", "web_search_weather", None),

    # Math
    (r"\d+\s*[\+\-\*\/]\s*\d+", "calculate", None),
    (r"\b(calculate|compute|what is|solve)\s+([\d\s\+\-\*\/\^\(\)\.]+)", "calculate", None),

    # Schedule
    (r"\b(schedule|remind me|set a (reminder|alarm|timer))\b", "schedule_task", None),

    # Identity / about
    (r"\b(who are you|what are you|your name|introduce yourself|what can you do)\b", "identity", None),

    # Help
    (r"\b(help|show commands|list commands|command list|command reference|capabilities|how do i|what commands|what can you)\b", "help", None),
]


class LocalIntelligenceEngine:
    """
    Full JARVIS intelligence without an LLM.
    Classifies intent, executes real tools, formats human responses.
    """

    def __init__(self):
        from ai.tools.executor import ToolExecutor
        self.executor = ToolExecutor()

    def classify_intent(self, text: str) -> Tuple[str, Dict]:
        """Returns (intent_name, extracted_args)"""
        text_lower = text.lower().strip()

        # Conceptual, educational, or creative queries route to LLM
        if re.search(r"\b(explain|why is|why are|how does|what is a\b|tell me about the concept|write a|joke|story|poem|who was)\b", text_lower):
            return "general", {"text": text}

        for pattern, intent, _ in INTENTS:
            m = re.search(pattern, text_lower)
            if m:
                return intent, {"match": m, "text": text}

        return "general", {"text": text}

    def respond(self, user_message: str) -> Dict[str, Any]:
        """Process a message and return a structured response."""
        intent, ctx = self.classify_intent(user_message)
        text = ctx["text"]
        match = ctx.get("match")

        tools_used = []

        try:
            if intent == "identity":
                return self._respond_identity()

            elif intent == "help":
                return self._respond_help()

            elif intent == "calculate":
                return self._respond_calculate(text)

            elif intent == "robot_forward":
                speed = self._extract_speed(text) or 50
                dur = self._extract_duration_ms(text)
                result_raw = self.executor.execute("robot_move",
                    {"direction": "forward", "speed": speed, "duration_ms": dur})
                result = json.loads(result_raw)
                tools_used.append("robot_move")
                sim = result.get("simulated", True)
                mode = " (simulated)" if sim else ""
                resp = (f"Moving forward at {speed}% speed{mode}."
                        + (f" Will stop after {dur}ms." if dur else ""))
                return {"response": resp, "tools_used": tools_used, "raw": result}

            elif intent == "robot_backward":
                speed = self._extract_speed(text) or 50
                dur = self._extract_duration_ms(text)
                result_raw = self.executor.execute("robot_move",
                    {"direction": "backward", "speed": speed, "duration_ms": dur})
                tools_used.append("robot_move")
                result = json.loads(result_raw)
                sim = result.get("simulated", True)
                mode = " (simulated)" if sim else ""
                return {"response": f"Moving backward at {speed}% speed{mode}.", "tools_used": tools_used, "raw": result}

            elif intent == "robot_left":
                speed = self._extract_speed(text) or 40
                result_raw = self.executor.execute("robot_move",
                    {"direction": "left", "speed": speed})
                tools_used.append("robot_move")
                return {"response": f"Turning left at {speed}% speed.", "tools_used": tools_used}

            elif intent == "robot_right":
                speed = self._extract_speed(text) or 40
                result_raw = self.executor.execute("robot_move",
                    {"direction": "right", "speed": speed})
                tools_used.append("robot_move")
                return {"response": f"Turning right at {speed}% speed.", "tools_used": tools_used}

            elif intent == "robot_stop":
                self.executor.execute("robot_move", {"direction": "stop"})
                tools_used.append("robot_move")
                return {"response": "Robot stopped. Motors coasting to halt.", "tools_used": tools_used}

            elif intent == "robot_estop":
                self.executor.execute("robot_move", {"direction": "estop"})
                tools_used.append("robot_move")
                return {"response": "⚠️ EMERGENCY STOP activated. All motors cut immediately.", "tools_used": tools_used}

            elif intent == "servo_set":
                # Try to extract channel and angle
                nums = re.findall(r'\d+', text)
                ch, angle = (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (0, 90)
                ch = min(ch, 15)
                angle = max(0, min(180, angle))
                self.executor.execute("servo_set", {"channel": ch, "angle": angle})
                tools_used.append("servo_set")
                return {"response": f"Servo channel {ch} set to {angle}°.", "tools_used": tools_used}

            elif intent == "read_sensors":
                result_raw = self.executor.execute("read_sensors", {})
                result = json.loads(result_raw)
                tools_used.append("read_sensors")
                return {"response": self._format_sensors(result), "tools_used": tools_used, "raw": result}

            elif intent == "system_status":
                result_raw = self.executor.execute("get_system_status", {})
                result = json.loads(result_raw)
                tools_used.append("get_system_status")
                return {"response": self._format_system(result), "tools_used": tools_used, "raw": result}

            elif intent == "camera_capture":
                result_raw = self.executor.execute("camera_capture", {})
                result = json.loads(result_raw)
                tools_used.append("camera_capture")
                desc = result.get("description", "No description available.")
                sim = result.get("simulated", True)
                mode = " (camera simulated)" if sim else ""
                return {"response": f"Camera capture{mode}: {desc}", "tools_used": tools_used}

            elif intent == "memory_store":
                # Extract what to remember
                m_content = re.search(r'\b(?:remember|store|save|note|record)\s+(?:that\s+)?(.+)', text, re.I)
                content = m_content.group(1) if m_content else text
                result_raw = self.executor.execute("memory_store",
                    {"category": "KNOWLEDGE", "content": content})
                result = json.loads(result_raw)
                tools_used.append("memory_store")
                return {"response": f"Stored in memory: \"{content[:80]}\" (ID: {result.get('id', '?')})", "tools_used": tools_used}

            elif intent == "memory_search":
                m_q = re.search(r'\b(?:remember|recall|search memory|look up|what do you remember about)\s+(.+)', text, re.I)
                query = m_q.group(1) if m_q else text
                # Clean query: remove possessives and punctuation
                import re as _re
                clean_q = _re.sub(r"'s\b", "", query).strip().rstrip("?.")
                result_raw = self.executor.execute("memory_search", {"query": clean_q or query})
                result = json.loads(result_raw)
                tools_used.append("memory_search")
                items = result.get("results", [])
                if items:
                    bullet = "\n".join(f"  • {r.get('content', '')[:80]}" for r in items[:3])
                    resp = f"Found {len(items)} memory record(s) for \"{clean_q or query}\":\n{bullet}"
                else:
                    resp = f"No memories found matching \"{clean_q or query}\"."
                return {"response": resp, "tools_used": tools_used}

            elif intent == "read_file":
                m_f = re.search(r"['\"]?([^\s'\"]+\.\w+)['\"]?", text)
                path = m_f.group(1) if m_f else "."
                result_raw = self.executor.execute("read_file", {"path": path})
                result = json.loads(result_raw)
                tools_used.append("read_file")
                if result.get("error"):
                    return {"response": f"Cannot read file: {result['error']}", "tools_used": tools_used}
                content = result.get("content", "")[:500]
                return {"response": f"Contents of {path}:\n```\n{content}\n```", "tools_used": tools_used}

            elif intent == "list_files":
                result_raw = self.executor.execute("run_command", {"command": "ls", "args": ["-la"]})
                result = json.loads(result_raw)
                tools_used.append("run_command")
                return {"response": f"Files:\n```\n{result.get('stdout', '')[:600]}\n```", "tools_used": tools_used}

            elif intent in ("web_search", "web_search_weather"):
                # Extract the search query
                query = text
                if intent == "web_search_weather":
                    query = "current weather forecast"
                else:
                    for prefix in ["search for", "search", "google", "look up", "find", "what is", "who is", "when did", "when was", "where is"]:
                        m_q = re.search(rf"\b{re.escape(prefix)}\s+(.+)", text, re.I)
                        if m_q:
                            query = m_q.group(1)
                            break
                result_raw = self.executor.execute("web_search", {"query": query})
                result = json.loads(result_raw)
                tools_used.append("web_search")
                if result.get("error"):
                    return {"response": f"Search failed: {result['error']}", "tools_used": tools_used}
                answer = result.get("answer") or result.get("abstract", "")
                results = result.get("results", [])
                if answer:
                    return {"response": f"Search result for \"{query}\": {answer}", "tools_used": tools_used}
                elif results:
                    top = results[0]
                    return {"response": f"Top result for \"{query}\": {top.get('title', '')} — {top.get('snippet', top.get('body', ''))[:200]}", "tools_used": tools_used}
                else:
                    return {"response": f"No results found for \"{query}\".", "tools_used": tools_used}

            elif intent == "schedule_task":
                # Extract schedule details
                m_time = re.search(r'(\d{1,2}:\d{2})', text)
                m_every = re.search(r'every\s+(\d+)\s*(second|minute|hour)s?', text, re.I)
                m_task = re.search(r'(?:remind me to|to)\s+(.+?)(?:\s+at|\s+every|\s*$)', text, re.I)

                schedule = "12:00"  # default daily noon
                task_name = "Scheduled Task"
                if m_time:
                    schedule = m_time.group(1)
                elif m_every:
                    n, unit = m_every.group(1), m_every.group(2).lower()
                    multiplier = {"second": 1, "minute": 60, "hour": 3600}.get(unit, 60)
                    schedule = f"every {int(n) * multiplier}s"
                if m_task:
                    task_name = m_task.group(1)

                result_raw = self.executor.execute("schedule_task",
                    {"name": task_name, "schedule": schedule, "command": "echo"})
                result = json.loads(result_raw)
                tools_used.append("schedule_task")
                return {"response": f"Task scheduled: \"{task_name}\" at {schedule} (ID: {result.get('id', '?')})", "tools_used": tools_used}

            else:
                # General — give an honest, helpful response
                return self._respond_general(text)

        except Exception as e:
            logger.error(f"LocalEngine error for intent {intent}: {e}")
            return {"response": f"I attempted to process your request but encountered an error: {e}",
                    "tools_used": tools_used}

    def _respond_identity(self) -> Dict:
        return {
            "response": (
                "I am JARVIS — Just A Rather Very Intelligent System — running on Raspberry Pi 5.\n\n"
                "I can:\n"
                "🤖 Control your robot (forward, backward, left, right, stop, emergency stop)\n"
                "🎛️  Set servo positions (servo <channel> to <angle>°)\n"
                "🌡️  Read sensors (BME280, BH1750, VL53L0X, PIR, HC-SR04)\n"
                "📊 Report system status (CPU, RAM, temperature, disk)\n"
                "📷 Capture camera frames and describe scenes\n"
                "🧠 Store and search long-term memories\n"
                "📁 Read and write files\n"
                "🔍 Search the web\n"
                "⏰ Schedule recurring tasks\n"
                "🔊 Speak responses aloud\n\n"
                "For full AI reasoning, add GOOGLE_API_KEY to .env (Google Gemini is free)."
            ),
            "tools_used": []
        }

    def _respond_help(self) -> Dict:
        return {
            "response": (
                "JARVIS Command Reference:\n\n"
                "ROBOT: 'move forward', 'go backward', 'turn left', 'turn right', 'stop', 'emergency stop'\n"
                "SERVO: 'servo 0 to 90', 'set servo 2 angle 45'\n"
                "SENSORS: 'read sensors', 'what is the temperature', 'check humidity'\n"
                "SYSTEM: 'system status', 'cpu usage', 'check memory'\n"
                "CAMERA: 'capture photo', 'what do you see', 'describe the scene'\n"
                "MEMORY: 'remember that X', 'recall X', 'search memory for X'\n"
                "FILES: 'read file.txt', 'list files'\n"
                "WEB: 'search for X', 'what is X', 'who is X'\n"
                "SCHEDULE: 'schedule X at 14:00', 'remind me to X every 30 minutes'\n"
            ),
            "tools_used": []
        }

    def _respond_calculate(self, text: str) -> Dict:
        nums_expr = re.findall(r'[\d\+\-\*\/\^\(\)\.\s]+', text)
        for expr in sorted(nums_expr, key=len, reverse=True):
            expr = expr.strip()
            if len(expr) < 3:
                continue
            try:
                result = eval(expr.replace("^", "**"), {"__builtins__": {}})
                return {"response": f"{expr.strip()} = **{result}**", "tools_used": []}
            except Exception:
                pass
        return {"response": "I couldn't parse that math expression. Try: 'what is 15 * 7 + 3'?", "tools_used": []}

    def _respond_general(self, text: str) -> Dict:
        return {
            "response": (
                f"I understand you said: \"{text}\"\n\n"
                "I'm running in local intelligence mode (no LLM connected). "
                "I can directly execute: robot control, sensor reads, system status, camera capture, "
                "file operations, web search, and memory storage.\n\n"
                "For open-ended conversation and complex reasoning, add GOOGLE_API_KEY to your .env file "
                "— Google Gemini is free at aistudio.google.com.\n\n"
                "Say 'help' for a full list of commands."
            ),
            "tools_used": []
        }

    def _format_sensors(self, data: dict) -> str:
        lines = ["📡 Sensor Readings:"]
        bme = data.get("bme280", {})
        if bme:
            lines.append(f"  🌡️  Temperature: {bme.get('temperature_c', 'N/A')}°C")
            lines.append(f"  💧 Humidity: {bme.get('humidity_pct', 'N/A')}%")
            lines.append(f"  🌬️  Pressure: {bme.get('pressure_hpa', 'N/A')} hPa")
        bh = data.get("bh1750", {})
        if bh:
            lines.append(f"  💡 Light: {bh.get('lux', 'N/A')} lux")
        vl = data.get("vl53l0x", {})
        if vl:
            lines.append(f"  📏 Distance: {vl.get('distance_mm', 'N/A')} mm")
        pir = data.get("hcsr501", {})
        if pir:
            lines.append(f"  👁️  Motion: {'DETECTED' if pir.get('motion_detected') else 'None'}")
        hc = data.get("hcsr04", {})
        if hc:
            lines.append(f"  🔊 Ultrasonic: {hc.get('distance_cm', 'N/A')} cm")
        return "\n".join(lines)

    def _format_system(self, data: dict) -> str:
        if data.get("error"):
            return f"System status unavailable: {data['error']}"
        lines = ["💻 System Status:"]
        lines.append(f"  🔲 CPU: {data.get('cpu_usage_pct', 0):.1f}%")
        lines.append(f"  💾 RAM: {data.get('ram_pct', 0):.1f}% used ({data.get('ram_used_gb', 0):.1f}GB / {data.get('ram_total_gb', 0):.1f}GB)")
        if data.get('temp_c'):
            lines.append(f"  🌡️  CPU Temp: {data.get('temp_c')}°C")
        lines.append(f"  💿 Disk: {data.get('disk_pct', 0):.1f}% used")
        lines.append(f"  ⏱️  Uptime: {data.get('uptime_str', 'N/A')}")
        lines.append(f"  🤖 Robot: {data.get('robot_state', 'UNKNOWN')}")
        return "\n".join(lines)

    def _extract_speed(self, text: str) -> Optional[int]:
        # "at 70 percent" / "at 70%" 
        m = re.search(r'at\s+(\d+)\s*(?:percent|%)', text, re.I)
        if m:
            return min(100, max(0, int(m.group(1))))
        # bare "70%"
        m = re.search(r'(\d+)\s*%', text)
        if m:
            return min(100, max(0, int(m.group(1))))
        # "speed 70"
        m = re.search(r'speed\s+(\d+)', text, re.I)
        if m:
            return min(100, max(0, int(m.group(1))))
        # words
        for word, val in [("slow", 25), ("half", 50), ("full", 100), ("fast", 80), ("max", 100)]:
            if word in text.lower():
                return val
        return None

    def _extract_duration_ms(self, text: str) -> int:
        m = re.search(r'(?:for\s+)?(\d+(?:\.\d+)?)\s*(second|sec|s|millisecond|ms|minute|min)', text, re.I)
        if m:
            val, unit = float(m.group(1)), m.group(2).lower()
            if unit.startswith("ms") or unit.startswith("milli"):
                return int(val)
            elif unit.startswith("min"):
                return int(val * 60000)
            else:
                return int(val * 1000)
        return 0
