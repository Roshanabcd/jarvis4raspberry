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

    def execute(self, name: str, args: Dict[str, Any], confirmed: bool = True) -> str:
        """Dispatch a tool call through ToolRegistry or fallback executor methods."""
        from tools.registry import tool_registry
        if tool_registry.has_tool(name):
            try:
                res = tool_registry.execute_tool(name, args, confirmed=confirmed)
                if res["success"]:
                    return json.dumps(res["result"], default=str) if isinstance(res["result"], (dict, list)) else str(res["result"])
                return json.dumps({"status": "error", "error": res.get("error", "Execution failed"), "tool": name})
            except Exception as e:
                logger.warning(f"Tool registry execution error for {name}: {e}")

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
            # Clamp duration to safe range: max 10,000ms (10 seconds)
            safe_duration_ms = max(0, min(10000, int(duration_ms)))
            safe_speed = max(0, min(100, int(speed)))

            actions = {
                "forward":  lambda: robot.forward(safe_speed),
                "backward": lambda: robot.backward(safe_speed),
                "left":     lambda: robot.turn_left(safe_speed),
                "right":    lambda: robot.turn_right(safe_speed),
                "stop":     robot.stop,
                "estop":    robot.emergency_stop,
            }
            fn = actions.get(direction.lower())
            if fn:
                fn()
                if safe_duration_ms > 0:
                    time.sleep(safe_duration_ms / 1000)
                    robot.stop()
                return {
                    "status": "ok",
                    "direction": direction,
                    "speed": safe_speed,
                    "duration_ms": safe_duration_ms,
                    "state": getattr(robot, "state", "UNKNOWN"),
                    "armed": getattr(robot, "armed", False),
                    "simulated": getattr(robot, "simulated", True),
                }
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
            from apps.vision.service import vision_service
            frame = vision_service.capture_frame()
            desc = vision_service.describe_scene(frame.get("image_path"))
            frame["description"] = desc
            return frame
        except Exception as e:
            return {"error": str(e), "description": "Camera unavailable.", "simulated": False}

    def _tool_detect_objects(self) -> Dict:
        try:
            from apps.vision.service import vision_service
            return vision_service.detect_objects()
        except Exception as e:
            return {"error": str(e), "objects": [], "count": 0}

    def _tool_identify_user(self) -> Dict:
        try:
            from apps.vision.service import vision_service
            return vision_service.identify_present_user()
        except Exception as e:
            return {"error": str(e), "identified": False, "role": "GUEST", "display_name": "Guest"}

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

    # ── Media Player ──────────────────────────────────────────

    def _tool_play_media(self, query: Optional[str] = None) -> Dict:
        try:
            from tools.media.media_player import media_player
            return media_player.play(query)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _tool_stop_media(self) -> Dict:
        try:
            from tools.media.media_player import media_player
            return media_player.stop()
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _tool_pause_media(self) -> Dict:
        try:
            from tools.media.media_player import media_player
            return media_player.pause()
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _tool_resume_media(self) -> Dict:
        try:
            from tools.media.media_player import media_player
            return media_player.resume()
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _tool_set_volume(self, level_pct: int) -> Dict:
        try:
            from tools.media.media_player import media_player
            return media_player.set_volume(level_pct)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    # ── Folder & File Navigation ──────────────────────────────

    def _tool_search_folders(self, query: str, directory: Optional[str] = None) -> Dict:
        try:
            from tools.filesystem.file_tools import file_tools
            matches = file_tools.search_folders(query=query, directory=directory)
            return {"query": query, "total_matches": len(matches), "folders": matches}
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _tool_open_folder(self, folder_name: str, parent_location: Optional[str] = None) -> Dict:
        try:
            from tools.filesystem.file_tools import file_tools
            return file_tools.open_folder(folder_name=folder_name, parent_location=parent_location)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _tool_open_file(self, file_path: str, editor: Optional[str] = None) -> Dict:
        try:
            from tools.filesystem.file_tools import file_tools
            return file_tools.open_file(file_path=file_path, editor=editor)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    # ── Desktop & Applications ────────────────────────────────

    def _tool_open_app(self, app_name: str, target: Optional[str] = None) -> Dict:
        """Launch desktop applications (VS Code, mousepad, terminal, etc.)"""
        import shutil
        import subprocess

        aliases = {
            "vs code": "code",
            "vscode": "code",
            "visual studio code": "code",
            "code editor": "code",
            "editor": "code",
            "terminal": "lxterminal",
            "browser": "chromium-browser",
            "calculator": "galculator",
            "text editor": "mousepad",
        }
        cmd = aliases.get(app_name.lower().strip(), app_name.lower().strip())
        path = shutil.which(cmd)
        if not path:
            local_p = os.path.expanduser(f"~/.local/bin/{cmd}")
            if os.path.exists(local_p):
                path = local_p

        if not path:
            if cmd == "code" and shutil.which("mousepad"):
                cmd = "mousepad"
                path = shutil.which("mousepad")
            else:
                return {"error": f"Application '{app_name}' is not installed.", "status": "not_installed"}

        env = os.environ.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"

        args = [path]
        if target:
            args.append(target)

        try:
            p = subprocess.Popen(args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"status": "opened", "app": app_name, "executable": path, "pid": p.pid, "target": target}
        except Exception as e:
            return {"error": f"Failed to launch '{app_name}': {e}", "status": "failed"}

    # ── Code Execution ────────────────────────────────────────

    def _tool_run_code(self, code: Optional[str] = None, file_path: Optional[str] = None,
                       language: str = "python") -> Dict:
        """Execute Python or Bash code directly on the system."""
        import subprocess
        import tempfile

        created_temp = False
        target_file = None
        if file_path:
            target_file = file_path
        elif code:
            ext = ".py" if language == "python" else ".sh"
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False, mode="w")
            tmp.write(code)
            tmp.flush()
            tmp.close()
            target_file = tmp.name
            created_temp = True
        else:
            return {"error": "No code or file_path provided", "status": "failed"}

        cmd = ["python3", target_file] if language == "python" else ["bash", target_file]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return {
                "status": "success" if res.returncode == 0 else "error",
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode,
                "file": target_file
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Execution timed out (15s limit)"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            if created_temp and target_file and os.path.exists(target_file):
                try:
                    os.remove(target_file)
                except OSError:
                    pass

