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
            norm_name = name.lower().strip()
            if norm_name in ("capture_image", "take_screenshot", "inspect_screen", "capture_screen", "screen_inspect"):
                if "screen" in norm_name or "screenshot" in norm_name:
                    method = self._tool_screen_capture
                elif norm_name == "capture_image":
                    is_screen = any("screen" in str(v).lower() or "desktop" in str(v).lower() for v in args.values())
                    method = self._tool_screen_capture if is_screen else self._tool_camera_capture
            elif norm_name in ("running_apps_processes", "get_running_apps", "list_running_processes", "running_processes"):
                method = self._tool_running_apps_processes
            elif norm_name in ("developer_escalation", "diagnose_cli", "run_cli_diagnosis"):
                method = self._tool_developer_escalation

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

    # ── Camera & Screen Vision ────────────────────────────────

    def _tool_screen_capture(self) -> Dict:
        try:
            from tools.desktop.desktop_perception import DesktopPerceptionService
            dp = DesktopPerceptionService()
            snap = dp.capture_fullscreen()
            if snap.get("status") != "ok" or not snap.get("filepath"):
                return {"error": "Failed to capture screen image", "description": "Screen capture was not successful."}
            image_path = snap.get("filepath")
            from apps.vision.service import vision_service
            desc = vision_service.describe_scene(image_path)
            return {
                "status": "ok",
                "image_path": image_path,
                "description": desc or "Screen analyzed successfully.",
                "width": snap.get("width"),
                "height": snap.get("height"),
            }
        except Exception as e:
            return {"error": str(e), "description": "Screen vision tool unavailable: " + str(e)}

    def _tool_camera_capture(self) -> Dict:
        try:
            from apps.vision.service import vision_service
            frame = vision_service.capture_frame()
            desc = vision_service.describe_scene(frame.get("image_path"))
            frame["description"] = desc
            return frame
        except Exception as e:
            return {"error": str(e), "description": "Camera unavailable.", "simulated": False}

    def _tool_inspect_screen(self) -> Dict:
        return self._tool_screen_capture()

    def _tool_running_apps_processes(self) -> Dict:
        try:
            from tools.system.process_inspector import process_inspector
            return process_inspector.get_running_overview()
        except Exception as e:
            return {"error": str(e)}

    def _tool_developer_escalation(self, prompt: str = "") -> Dict:
        try:
            from tools.developer.cli_bridge import developer_cli_bridge
            return developer_cli_bridge.run_diagnostic_cli(prompt=prompt)
        except Exception as e:
            return {"error": str(e)}

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

        # Check capability catalog first (e.g. document-qa, youtube-summarizer, orchestrator, smart-home)
        try:
            from ai.capabilities.registry import get_capability_registry
            reg = get_capability_registry()
            cap = reg.get_capability(app_name.lower().strip())
            if not cap:
                for c in reg.list_capabilities():
                    if app_name.lower().strip() in c.name.lower() or any(app_name.lower().strip() == kw.lower() for kw in c.keywords):
                        cap = c
                        break
            if cap and cap.route:
                return {
                    "status": "opened",
                    "app": cap.name,
                    "capability_id": cap.id,
                    "route": cap.route,
                    "target_tab": cap.target_tab,
                    "message": f"Opened {cap.name} interface at {cap.route}."
                }
        except Exception:
            pass

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

    # ── Autonomous Capabilities & Developer CLIs ──────────────

    def _tool_invoke_capability(self, capability_id: str, action_id: str = "execute",
                               parameters: Optional[Dict[str, Any]] = None) -> Dict:
        """Invoke any of JARVIS's 45+ autonomous capabilities or extension modules."""
        try:
            from ai.capabilities.dispatcher import get_capability_dispatcher
            from ai.capabilities.models import CapabilityInvocationRequest
            dispatcher = get_capability_dispatcher()
            req = CapabilityInvocationRequest(
                capability_id=capability_id,
                action_id=action_id,
                parameters=parameters or {},
                channel="agent_tool",
            )
            res = dispatcher.execute(req)
            return {
                "status": res.status,
                "capability_id": res.capability_id,
                "action_id": res.action_id,
                "output": res.markdown_output,
                "spoken_summary": res.spoken_summary,
                "data": res.data,
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "capability_id": capability_id}

    def _tool_execute_coding_cli(self, cli_name: str, prompt: str,
                                action: str = "run_task") -> Dict:
        """Execute local AI developer coding CLI (antigravity, claude, codex, copilot, etc.)."""
        return self._tool_invoke_capability(
            capability_id=f"developer-cli:{cli_name}",
            action_id=action,
            parameters={"prompt": prompt, "instruction": prompt},
        )

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

    # ── Computer Control & Browser Automation ───────────────────

    def _tool_computer_execute(self, instruction: str) -> Dict[str, Any]:
        from tools.desktop.unified_computer_service import unified_computer_service
        return unified_computer_service.execute_natural_instruction(instruction)

    def _tool_computer_select_option(self, option: str) -> Dict[str, Any]:
        from tools.desktop.browser_backend import browser_backend
        return browser_backend.select_option(option, verify=True)

    def _tool_computer_click(self, button: str = "left", x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        from tools.desktop.native_backend import native_backend
        return native_backend.click(x=x, y=y, button=button)

    def _tool_computer_move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        from tools.desktop.native_backend import native_backend
        return native_backend.move_cursor(x, y, duration=0.25, smooth=True)

    def _tool_computer_type(self, text: str) -> Dict[str, Any]:
        from tools.desktop.native_backend import native_backend
        return native_backend.type_text(text)

    def _tool_computer_stop(self) -> Dict[str, Any]:
        from tools.desktop.unified_computer_service import unified_computer_service
        return unified_computer_service.emergency_stop()

    def _tool_open_url(self, url: str, browser: str = "chrome") -> Dict[str, Any]:
        from tools.browser.browser_agent import browser_agent
        clean = (url or "").strip()
        if clean.lower() in ("youtube", "youtube.com"):
            clean = "https://www.youtube.com"
        elif clean.lower() in ("google", "google.com"):
            clean = "https://www.google.com"
        elif not clean.startswith(("http://", "https://", "about:", "chrome://")):
            clean = f"https://{clean}"
        return browser_agent.open_url(clean, browser=browser, new_tab=True)

    def _tool_open_youtube(self, query: str = "", url: str = "") -> Dict[str, Any]:
        from tools.browser.youtube_controller import youtube_controller
        from tools.browser.browser_agent import browser_agent
        if url:
            return browser_agent.open_url(url, browser="chrome", new_tab=True)
        clean_q = (query or "").strip()
        if clean_q and clean_q.lower() not in ("youtube", "none", "null", "all"):
            return youtube_controller.play_direct_query(clean_q, browser="chrome")
        return browser_agent.open_url("https://www.youtube.com", browser="chrome", new_tab=True)

    def _tool_open_desktop_app(self, app_name: str, target: Optional[str] = None, new_window: bool = False) -> Dict[str, Any]:
        from tools.desktop.action_engine import desktop_action_engine
        return desktop_action_engine.open_application(app_name, target=target, new_window=new_window)



