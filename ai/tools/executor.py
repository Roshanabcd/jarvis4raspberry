"""
JARVIS Tool Executor — Runs real actions when AI requests them.
All tools are sandboxed and simulation-safe.
"""
import json
import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("JARVIS.ToolExecutor")


class ToolExecutor:
    """
    Executes tool calls requested by the AI.
    Each method is isolated, safe, and returns a JSON-serialisable result.
    """

    def execute(self, name: str, args: Dict[str, Any]) -> str:
        """Dispatch a tool call. Returns string result for AI consumption."""
        method = getattr(self, f"_tool_{name}", None)
        if method is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = method(**args)
            return json.dumps(result, default=str) if isinstance(result, dict) else str(result)
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return json.dumps({"error": str(e), "tool": name})

    # ── Robot ─────────────────────────────────────────────────

    def _tool_robot_move(self, direction: str, speed: int = 50,
                         duration_ms: int = 0) -> Dict:
        try:
            from tools.robotics.controller import robot
            actions = {
                "forward":  lambda: robot.forward(speed),
                "backward": lambda: robot.backward(speed),
                "left":     lambda: robot.turn_left(speed),
                "right":    lambda: robot.turn_right(speed),
                "stop":     robot.stop,
                "estop":    robot.emergency_stop,
            }
            fn = actions.get(direction.lower())
            if fn:
                fn()
                if duration_ms > 0:
                    time.sleep(duration_ms / 1000)
                    robot.stop()
                return {"status": "ok", "direction": direction, "speed": speed,
                        "duration_ms": duration_ms, "simulated": getattr(robot, "simulated", True)}
            return {"error": f"Unknown direction: {direction}"}
        except Exception as e:
            return {"error": str(e)}

    def _tool_servo_set(self, channel: int, angle: int) -> Dict:
        try:
            from tools.robotics.controller import robot
            robot.set_servo(channel, angle)
            return {"status": "ok", "channel": channel, "angle": angle}
        except Exception as e:
            return {"error": str(e)}

    # ── Sensors ───────────────────────────────────────────────

    def _tool_read_sensors(self) -> Dict:
        try:
            from hardware.sensors.sensor_manager import sensor_manager
            return sensor_manager.read_all()
        except Exception as e:
            return {"error": str(e), "simulated": True}

    # ── System ────────────────────────────────────────────────

    def _tool_get_system_status(self) -> Dict:
        try:
            from hardware.raspberry_pi.rpi_info import get_system_status
            status = get_system_status()
            try:
                from tools.robotics.controller import robot
                status["robot_state"] = str(getattr(robot, "state", "UNKNOWN"))
            except Exception:
                status["robot_state"] = "UNKNOWN"
            return status
        except Exception as e:
            return {"error": str(e)}

    # ── Camera ────────────────────────────────────────────────

    def _tool_camera_capture(self) -> Dict:
        try:
            from apps.vision.service import VisionService
            from config.config_manager import config
            vs = VisionService(simulation=config.get("simulation_mode", True))
            frame = vs.capture_frame()
            desc = vs.describe_scene()
            frame["description"] = desc
            return frame
        except Exception as e:
            return {"error": str(e), "description": "Camera unavailable."}

    # ── Memory ────────────────────────────────────────────────

    def _tool_memory_store(self, category: str, content: str) -> Dict:
        try:
            from memory.long_term.database import db
            mid = db.store(category.upper(), content)
            return {"status": "stored", "id": mid, "category": category, "content": content[:80]}
        except Exception as e:
            return {"error": str(e)}

    def _tool_memory_search(self, query: str) -> Dict:
        try:
            from memory.long_term.database import db
            results = db.search(query)
            return {"results": results[:5], "count": len(results), "query": query}
        except Exception as e:
            return {"error": str(e)}

    # ── Shell ─────────────────────────────────────────────────

    def _tool_run_command(self, command: str, args: list = None) -> Dict:
        try:
            from tools.shell.command_runner import SecureCommandRunner
            runner = SecureCommandRunner()
            return runner.execute(command, args or [], timeout=15)
        except Exception as e:
            return {"error": str(e)}

    # ── Files ─────────────────────────────────────────────────

    def _tool_read_file(self, path: str) -> Dict:
        try:
            from tools.filesystem.file_tools import FileTools
            ft = FileTools()
            content = ft.read_file(path)
            return {"status": "ok", "path": path, "content": content[:2000],
                    "truncated": len(content) > 2000}
        except Exception as e:
            return {"error": str(e)}

    def _tool_write_file(self, path: str, content: str) -> Dict:
        try:
            from tools.filesystem.file_tools import FileTools
            ft = FileTools()
            ft.write_file(path, content)
            return {"status": "written", "path": path, "bytes": len(content)}
        except Exception as e:
            return {"error": str(e)}

    # ── Scheduler ─────────────────────────────────────────────

    def _tool_schedule_task(self, name: str, schedule: str, command: str) -> Dict:
        try:
            from tools.scheduler.task_scheduler import TaskScheduler
            sched = TaskScheduler()
            task_id = sched.schedule_task(name, schedule, command)
            return {"status": "scheduled", "id": task_id, "name": name, "schedule": schedule}
        except Exception as e:
            return {"error": str(e)}

    # ── Web Search ────────────────────────────────────────────

    def _tool_web_search(self, query: str) -> Dict:
        try:
            from tools.web_search.searcher import WebSearcher
            searcher = WebSearcher()
            results = searcher.search(query)
            return {"query": query, "results": results[:3]}
        except Exception as e:
            # Fallback: DuckDuckGo Lite
            try:
                import requests
                r = requests.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1},
                    timeout=8, headers={"User-Agent": "JARVIS/1.0"}
                )
                data = r.json()
                abstract = data.get("AbstractText", "")
                answer = data.get("Answer", "")
                return {"query": query, "answer": answer or abstract or "No direct answer found.",
                        "source": data.get("AbstractURL", "")}
            except Exception as e2:
                return {"error": str(e2), "query": query}

    # ── TTS ───────────────────────────────────────────────────

    def _tool_speak(self, text: str) -> Dict:
        try:
            from apps.voice.tts import TextToSpeech
            tts = TextToSpeech()
            tts.speak_sync(text)
            return {"status": "spoken", "text": text[:80]}
        except Exception as e:
            return {"error": str(e), "text": text[:80]}
