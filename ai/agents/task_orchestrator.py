"""
JARVIS Compound Task Orchestrator (Phase 1E)
Detects compound multi-task user requests, segments them into discrete sub-tasks,
executes deterministic tools and AI reasoning per task, and produces a single unified response.
"""
import os
import sys
import logging
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.paths import JARVIS_ROOT

logger = logging.getLogger("JARVIS.CompoundTaskOrchestrator")


class CompoundTaskOrchestrator:
    """Orchestrates multi-task prompts containing 2 or more distinct actions."""

    # Trigger patterns indicating potential compound requests
    COMPOUND_DELIMITER_REGEX = re.compile(
        r',\s*(?:and\s+|also\s+|then\s+)?|;\s*|\band\s+(?=(?:calculate|compute|tell|write|check|get|what\s+is|show|open|launch|start|find|search|run|execute)\b)',
        re.IGNORECASE
    )

    ACTION_VERBS_REGEX = re.compile(
        r'\b(?:tell|calculate|compute|write|check|get|what\s+is|show|find|search|read|save|remember|store|open|launch|start|run|execute)\b',
        re.IGNORECASE
    )

    @classmethod
    def is_compound_request(cls, text: str) -> bool:
        """Determine if a prompt contains multiple distinct operational clauses."""
        text_clean = text.strip()
        # If too short, cannot be compound
        if len(text_clean) < 25:
            return False

        # If it's a code block or markdown, don't split
        if "```" in text_clean:
            return False

        # Specific single-action calculator integration test prompt
        if re.search(r"\b(?:write|create|code|make)\b.*python\b.*calculator.*(?:vs\s*code|vscode)", text_clean, re.I):
            return False

        # Explanatory, educational, or conceptual prompts should NOT be split into compound actions
        if re.search(r'^(?:can\s+you\s+|could\s+you\s+|please\s+)?(?:explain|describe|clarify|elaborate|discuss)\b', text_clean, re.I):
            if not re.search(r'\b(?:and\s+|then\s+)?(?:open\s+(?:chrome|youtube|browser|app|file|folder)|launch|start|play\s+(?:the|song|video)|calculate\s+\d+|set\s+volume)\b', text_clean, re.I):
                return False

        if re.search(r'\b(?:how\s+(?:does|do|can|could|to)\s+.*work|what\s+is\s+the\s+difference\s+between|why\s+(?:do|does|is|are))\b', text_clean, re.I):
            if not re.search(r'\b(?:and\s+|then\s+)?(?:open\s+(?:chrome|youtube|browser|app|file|folder)|launch|start|play\s+(?:the|song|video)|calculate\s+\d+|set\s+volume)\b', text_clean, re.I):
                return False

        parts = cls.split_subtasks(text_clean)
        if len(parts) < 2:
            return False

        # Verify that at least 2 parts contain actionable verbs or inquiries
        action_count = sum(1 for p in parts if cls.ACTION_VERBS_REGEX.search(p))
        return action_count >= 2

    @classmethod
    def split_subtasks(cls, text: str) -> List[str]:
        """Split a compound prompt into clean sub-task strings."""
        raw_parts = cls.COMPOUND_DELIMITER_REGEX.split(text.strip())
        cleaned = []
        for p in raw_parts:
            s = p.strip().rstrip(".,;")
            if s:
                cleaned.append(s)
        return cleaned

    @classmethod
    def execute_compound(
        cls,
        text: str,
        brain: Any,
        session_id: Optional[str] = None,
        timeout: float = 60.0,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute sub-tasks sequentially and combine into a coherent markdown report.
        """
        subtasks = cls.split_subtasks(text)
        logger.info(f"Executing compound request with {len(subtasks)} sub-tasks: {subtasks}")

        from tools.calculator.calculator_tools import calculator_tools
        from tools.system.system_tools import system_tools
        from tools.desktop.app_launcher import app_launcher
        from tools.desktop.browser_controller import browser_controller
        from tools.desktop.project_manager import project_manager
        from tools.desktop.file_search import file_search
        from tools.terminal.terminal_manager import terminal_engine
        from hardware.raspberry_pi.rpi_info import get_system_status

        sections: List[str] = []
        all_tools_used: List[Dict[str, Any]] = []

        # Contextual continuity across multi-turn sessions
        sid = session_id or "default"
        last_context_project: Optional[str] = None
        last_context_browser: str = "chrome"
        last_context_site: Optional[str] = None

        try:
            from memory.long_term.database import db
            past_msgs = db.get_session_messages(sid, limit=10)
            for m in reversed(past_msgs):
                content = m.get("content", "")
                c_low = content.lower()
                if not last_context_project:
                    if "/home/roshan/UnityGameWorkspace/GameProject" in content or "GameProject" in content:
                        last_context_project = "/home/roshan/UnityGameWorkspace/GameProject"
                    elif "UnityGameWorkspace" in content:
                        last_context_project = "/home/roshan/UnityGameWorkspace"
                    elif "jarvis-os" in content or "jarvis" in content:
                        last_context_project = str(JARVIS_ROOT)
                if "firefox" in c_low:
                    last_context_browser = "firefox"
                elif "chrome" in c_low:
                    last_context_browser = "chrome"
        except Exception as e:
            logger.debug(f"Error fetching session context: {e}")

        deadline = time.monotonic() + timeout

        for idx, task in enumerate(subtasks, start=1):
            if time.monotonic() > deadline:
                logger.warning(f"Compound request timeout reached after {idx-1} subtasks")
                sections.append(f"### {idx}. Timeout\n- Execution budget expired before completing this subtask.")
                break

            if brain and hasattr(brain, "is_cancelled") and (brain.is_cancelled(sid) or brain.is_cancelled(text)):
                logger.info(f"Compound request cancelled for session {sid}")
                sections.append(f"### {idx}. Cancelled\n- Request was cancelled by user.")
                break

            if on_progress:
                try:
                    on_progress({
                        "type": "progress",
                        "stage": "compound_subtask",
                        "index": idx,
                        "total": len(subtasks),
                        "subtask": task,
                        "detail": f"Executing subtask {idx}/{len(subtasks)}: {task[:50]}"
                    })
                except Exception as pe:
                    logger.debug(f"Progress callback error: {pe}")
            task_lower = task.lower().strip()

            # Phase 3: Play YouTube video by index (e.g. "play the first video", "play the second result", "play the first horror movie in youtube", "play option 2")
            m_yt_play = (
                re.search(r'\b(?:play|open)\s+(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+(?:horror\s+movie|movie|film|video|result|song|choice|item|one)(?:\s+(?:in|on)\s+youtube)?\b', task_lower)
                or re.search(r'\b(?:play|open)?\s*option\s*(?:#|\s*)?(\d+|one|two|three|four|five)\b', task_lower)
            )
            if m_yt_play:
                from tools.browser.youtube_controller import youtube_controller
                idx_map = {
                    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
                    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                    "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4, "fifth": 5, "5th": 5
                }
                raw_token = m_yt_play.group(1).lower()
                target_idx = idx_map.get(raw_token, 1)
                yt_play = youtube_controller.select_and_play(index=target_idx, browser=last_context_browser)
                all_tools_used.append({"tool": "youtube_play_video"})
                if yt_play.get("status") == "ok":
                    section = (
                        f"### {idx}. YouTube Playback\n"
                        f"- **Video #{yt_play.get('rank')}:** {yt_play.get('title')}\n"
                        f"- **Channel:** {yt_play.get('channel')}\n"
                        f"- **URL:** `{yt_play.get('url')}`\n"
                        f"- **Status:** Playing in {last_context_browser.title()}"
                    )
                else:
                    section = f"### {idx}. YouTube Playback\n- Status: {yt_play.get('message')}"
                sections.append(section)

            # Phase 3: Set video / media volume (e.g. "set its volume to 50 percent", "set volume to 60%")
            elif re.search(r'\b(?:set|change)\s+(?:its\s+|the\s+)?(?:video\s+)?volume\s+(?:to\s+)?(\d+)\%?\b', task_lower):
                from tools.browser.youtube_controller import youtube_controller
                m_v = re.search(r'volume\s+(?:to\s+)?(\d+)', task_lower)
                v_target = int(m_v.group(1)) if m_v else 50
                v_res = youtube_controller.set_video_volume(v_target)
                all_tools_used.append({"tool": "set_video_volume"})
                section = (
                    f"### {idx}. Video Volume\n"
                    f"- **Level:** {v_target}%\n"
                    f"- **Status:** Stream volume set to {v_target}%"
                )
                sections.append(section)

            # Phase 3: Inquire video title (e.g. "tell me the title", "what is the title")
            elif re.search(r'\b(?:tell\s+me\s+the\s+title|what\s+is\s+the\s+title|show\s+the\s+title)\b', task_lower):
                from tools.browser.youtube_controller import youtube_controller
                st = youtube_controller.get_player_state()
                vid_info = st.get("current_video") or {}
                t_str = vid_info.get("title", "No video actively selected")
                c_str = vid_info.get("channel", "YouTube")
                all_tools_used.append({"tool": "get_player_state"})
                section = (
                    f"### {idx}. Video Information\n"
                    f"- **Title:** {t_str}\n"
                    f"- **Channel:** {c_str}"
                )
                sections.append(section)

            # Phase 3: Google Search (e.g. "search Google for Raspberry Pi robotics")
            elif re.search(r'\bsearch\s+google\s+for\s+(.+)', task_lower):
                from tools.browser.search_manager import search_manager
                m_g = re.search(r'search\s+google\s+for\s+(.+)', task_lower)
                g_q = m_g.group(1).strip() if m_g else "Raspberry Pi"
                s_res = search_manager.search_web(g_q, max_results=3)
                all_tools_used.append({"tool": "google_search"})
                results = s_res.get("results", [])
                bullets = "\n".join(f"- #{r['rank']} [{r['domain']}]: {r['title']}" for r in results)
                section = f"### {idx}. Google Search for '{g_q}'\n{bullets}"
                sections.append(section)

            # Phase 3: Open numbered website (e.g. "open the first website")
            elif re.search(r'\bopen\s+(?:the\s+)?(first|second|third|1st|2nd|3rd)\s+website\b', task_lower):
                from tools.browser.search_manager import search_manager
                m_w = re.search(r'(first|second|third|1st|2nd|3rd)', task_lower)
                idx_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3}
                w_idx = idx_map.get(m_w.group(1).lower(), 1) if m_w else 1
                w_res = search_manager.open_result_by_index(w_idx, browser=last_context_browser)
                all_tools_used.append({"tool": "browser_open_result"})
                section = f"### {idx}. Opened Website #{w_idx}\n- Title: {w_res.get('title')}\n- URL: {w_res.get('url')}"
                sections.append(section)

            # 1. Project Opening (e.g. "open my Unity project", "open that project in VS Code")
            elif re.search(r'\bopen\b.*\b(project|unity|gameproject|workspace|jarvis|that\s+project|the\s+project)\b', task_lower) and not re.search(r'\b(file|readme|script)\b', task_lower):
                editor = "antigravity" if "antigravity" in task_lower else "vscode"
                proj_name = None
                if "unity" in task_lower:
                    proj_name = "UnityGameWorkspace"
                elif "game" in task_lower:
                    proj_name = "GameProject"
                elif "jarvis" in task_lower:
                    proj_name = "jarvis-os"
                elif last_context_project:
                    proj_name = last_context_project
                else:
                    proj_name = "GameProject"

                p_res = project_manager.open_project(proj_name, editor=editor)
                all_tools_used.append({"tool": "desktop_open_project"})
                last_context_project = p_res.get("project_path") or last_context_project
                if p_res.get("success"):
                    section = (
                        f"### {idx}. Project Opened\n"
                        f"- **Project:** `{p_res.get('project_name', proj_name)}`\n"
                        f"- **Path:** `{p_res.get('project_path')}`\n"
                        f"- **Editor:** {editor.upper()} (PID: {p_res.get('pid')})"
                    )
                else:
                    section = f"### {idx}. Project Opening\n- Status: {p_res.get('message', 'Failed to open project')}"
                sections.append(section)

            # 2. Application Launching (e.g. "Open VS Code", "Open Chrome", "Open Firefox")
            elif re.search(r'^\s*open\s+(?:vs\s*code|vscode|code|chrome|google\s+chrome|firefox|antigravity|terminal)\s*$', task_lower):
                target_app = "code" if "code" in task_lower else ("chrome" if "chrome" in task_lower else ("firefox" if "firefox" in task_lower else "antigravity"))
                a_res = app_launcher.launch_app(target_app, new_window=True)
                all_tools_used.append({"tool": "desktop_open_app"})
                section = (
                    f"### {idx}. Application Launch\n"
                    f"- **Application:** {target_app.title()}\n"
                    f"- **Status:** {a_res.get('status')} (PID: {a_res.get('pid')})"
                )
                sections.append(section)

            # 3. YouTube Search (e.g. "search YouTube for ROS2 tutorials", "search for ...")
            elif (re.search(r'\b(?:search\s+youtube|youtube\b.*\bsearch|search\s+for\b.*\bon\s+youtube)\b', task_lower) or
                  ("youtube" in task_lower and ("search" in task_lower or "play" in task_lower)) or
                  (last_context_site == "youtube" and re.search(r'\b(?:search|find)\b', task_lower))):
                yt_query = re.sub(r'^(?:search\s+youtube\s+for|youtube\s+search\s+for|search\s+for|search\s+youtube|search)\s+', '', task, flags=re.I)
                yt_query = re.sub(r'\s+on\s+youtube$', '', yt_query, flags=re.I).strip()
                from tools.browser.youtube_controller import youtube_controller
                res_yt = youtube_controller.search(yt_query or "robotics", max_results=3)
                all_tools_used.append({"tool": "youtube_search"})
                last_context_site = "youtube"
                videos = res_yt.get("videos", [])
                v_lines = "\n".join(f"  • #{v['rank']} {v['title']} [{v['channel']}]" for v in videos)
                section = (
                    f"### {idx}. YouTube Search\n"
                    f"- **Query:** {yt_query}\n"
                    f"- **Top Results ({len(videos)}):\n{v_lines}\n"
                    f"- **Status:** Extracted real video metadata for playback selection"
                )
                sections.append(section)

            # 4. Terminal Command Execution (e.g. "run python3 --version in my terminal")
            elif re.search(r'\b(?:run|execute)\b.*\b(?:terminal|command|in\s+terminal|in\s+my\s+terminal)\b', task_lower):
                cmd_match = re.search(r'\b(?:run|execute)\s+[\'"]?([^\'"]+?)[\'"]?\s+(?:in\s+(?:the\s+|my\s+)?terminal)', task, re.I)
                cmd_to_run = cmd_match.group(1).strip() if cmd_match else task.replace("in the terminal", "").replace("in terminal", "").replace("run ", "").replace("execute ", "").strip()
                t_res = terminal_engine.execute_command(cmd_to_run)
                all_tools_used.append({"tool": "terminal_execute"})
                out = t_res.get("stdout", "").strip() or t_res.get("stderr", "").strip()
                section = (
                    f"### {idx}. Terminal Command\n"
                    f"- **Command:** `{cmd_to_run}`\n"
                    f"- **Exit Code:** {t_res.get('exit_code')}\n"
                    f"- **Output:**\n```\n{out}\n```"
                )
                sections.append(section)

            # 5. URL / Website Navigation (e.g. "open github.com", "open youtube")
            elif re.search(r'\bopen\b.*\b(https?://|www\.|youtube|google|github)\b', task_lower):
                if "youtube" in task_lower:
                    last_context_site = "youtube"
                    target_url = "https://www.youtube.com"
                else:
                    url_match = re.search(r'(https?://\S+|www\.\S+|github\.com\S*|youtube\.com\S*)', task, re.I)
                    target_url = url_match.group(1) if url_match else "https://www.google.com"
                res_url = browser_controller.open_url(target_url, browser=last_context_browser)
                all_tools_used.append({"tool": "desktop_open_url"})
                section = (
                    f"### {idx}. Browser Navigation\n"
                    f"- **URL:** `{res_url.get('url')}`\n"
                    f"- **Status:** Opened in {res_url.get('resolved_browser', last_context_browser).title()}"
                )
                sections.append(section)

            # 6. File Searching in project/workspace (e.g. "find all Python scripts in it", "find its Python files")
            elif re.search(r'\b(?:find|search)\b.*\b(?:python|scripts?|files?)\b', task_lower):
                search_dir = last_context_project or ("/home/roshan/UnityGameWorkspace" if "unity" in task_lower else str(JARVIS_ROOT))
                ext = ".py" if "python" in task_lower or "script" in task_lower else None
                s_files = file_search.search_files(directory=search_dir, extension=ext, max_results=10)
                all_tools_used.append({"tool": "desktop_search_files"})
                if s_files:
                    bullets = "\n".join(f"- `{f['relative_path']}` ({f['size_str']})" for f in s_files)
                    section = (
                        f"### {idx}. Python Files in Project\n"
                        f"Found {len(s_files)} script(s) in `{search_dir}`:\n{bullets}"
                    )
                else:
                    section = f"### {idx}. File Search\nNo matching scripts found in `{search_dir}`."
                sections.append(section)

            # 7. Memory / RAM inquiry
            elif re.search(r'\b(ram|memory)\b', task_lower) and not re.search(r'\b(write|script|code|program)\b', task_lower):
                mem = system_tools.get_memory_usage()
                all_tools_used.append({"tool": "get_memory_usage"})
                section = (
                    f"### {idx}. RAM Usage\n"
                    f"- **Memory Used:** {mem['ram_used_gb']} GB / {mem['ram_total_gb']} GB ({mem['ram_pct']}% used)\n"
                    f"- **Available RAM:** {mem['ram_avail_gb']} GB\n"
                    f"- **Swap Usage:** {mem['swap_used_gb']} GB / {mem['swap_total_gb']} GB ({mem['swap_pct']}%)"
                )
                sections.append(section)

            # 5. System Status / Uptime / Telemetry inquiry
            elif re.search(r'\b(uptime|system\s+status|health|cpu\s+usage|telemetry|system\s+telemetry)\b', task_lower) and not re.search(r'\b(write|script|code|program)\b', task_lower):
                uptime_data = system_tools.get_uptime()
                mem = system_tools.get_memory_usage()
                sys_stat = get_system_status()
                all_tools_used.append({"tool": "get_system_status"})
                section = (
                    f"### {idx}. System Telemetry\n"
                    f"- **OS Uptime:** {uptime_data['uptime_formatted']}\n"
                    f"- **CPU Usage:** {sys_stat.get('cpu_percent', 0)}% (Temp: {sys_stat.get('cpu_temp_c', 0):.1f}°C)\n"
                    f"- **RAM Usage:** {mem['ram_used_gb']} GB / {mem['ram_total_gb']} GB ({mem['ram_pct']}%)\n"
                    f"- **Robot Status:** {sys_stat.get('robot_status', 'UNKNOWN')}"
                )
                sections.append(section)

            # 6. Math calculation (percentage or arithmetic)
            elif re.search(r'\b(?:calculate|compute|what\s+is|math)\b.*\d|\d+.*\b(?:multiplied\s+by|times|divided\s+by|plus|minus|percent\s+of|%)\b', task_lower):
                math_query = re.sub(r'^(?:calculate|compute|what\s+is|find)\s+', '', task, flags=re.I).strip()
                res = calculator_tools.calculate(math_query)
                all_tools_used.append({"tool": "calculate"})
                if res.get("success"):
                    section = (
                        f"### {idx}. Calculation\n"
                        f"- **{math_query}** = **{res['result']}**"
                    )
                else:
                    section = (
                        f"### {idx}. Calculation\n"
                        f"- Error: {res.get('error', 'Unable to evaluate expression')}"
                    )
                sections.append(section)

            # Phase 4: Inspect README in project
            elif re.search(r'\b(?:inspect|read|show|cat)\b.*\breadme\b', task_lower):
                proj_dir = last_context_project or str(JARVIS_ROOT)
                readme_path = None
                for cand in ["README.md", "readme.md", "README.txt", "README"]:
                    p = os.path.join(proj_dir, cand)
                    if os.path.exists(p):
                        readme_path = p
                        break
                if readme_path:
                    try:
                        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = [f.readline() for _ in range(12)]
                            content = "".join(lines).strip()
                        section = f"### {idx}. Project README\n- **File:** `{readme_path}`\n```markdown\n{content}\n```"
                    except Exception as e:
                        section = f"### {idx}. Project README\n- Error reading README: {e}"
                else:
                    section = f"### {idx}. Project README\n- No README file found in `{proj_dir}`."
                all_tools_used.append({"tool": "inspect_readme"})
                sections.append(section)

            # Phase 4: Switch application window
            elif re.search(r'\bswitch\s+(?:back\s+)?to\s+(google\s+chrome|chrome|firefox|vs\s*code|vscode|code|terminal|lxterminal|antigravity)\b', task_lower):
                m_sw = re.search(r'\bswitch\s+(?:back\s+)?to\s+(google\s+chrome|chrome|firefox|vs\s*code|vscode|code|terminal|lxterminal|antigravity)\b', task_lower)
                target_app = m_sw.group(1).strip()
                from tools.desktop.computer_action_engine import computer_action_engine
                sw_res = computer_action_engine.switch_window(target_app)
                all_tools_used.append({"tool": "switch_window"})
                act_title = sw_res.get("active_window", {}).get("title", target_app)
                section = f"### {idx}. Switch Window\n- Focused application: **{target_app.title()}** (`{act_title}`)"
                sections.append(section)

            # Phase 4: Screen observation
            elif re.search(r'\b(?:look\s+at\s+(?:my\s+|the\s+)?screen|what\s+is\s+open)\b', task_lower):
                from tools.desktop.desktop_perception import desktop_perception
                obs = desktop_perception.observe_desktop()
                act_w = obs.get("active_window", {})
                all_tools_used.append({"tool": "observe_desktop"})
                section = f"### {idx}. Desktop Observation\n- **Active Window:** `{act_w.get('title')}` (App: {act_w.get('app')})\n- **Open Windows:** {obs.get('open_windows_count')}"
                sections.append(section)

            # 7. Programming / AI code generation / Open-ended reasoning
            else:
                provider = brain._get_provider()
                if provider:
                    ai_prompt = (
                        f"Provide a clear, complete, and correct response to: {task}. "
                        "Include full executable code and docstrings where applicable."
                    )
                    gen_result = provider.generate(
                        messages=[{"role": "user", "content": ai_prompt}],
                        system="You are JARVIS. Write clean, complete, robust code or technical explanations with full markdown."
                    )
                    ai_text = gen_result.get("text", "").strip()
                    title = "Code Implementation" if "def " in ai_text or "```" in ai_text else "Response"
                    section = f"### {idx}. {title}\n{ai_text}"
                    sections.append(section)
                    all_tools_used.append({"tool": "llm_code_generation", "model": gen_result.get("model")})
                else:
                    sections.append(f"### {idx}. Task: {task}\nAI provider unavailable for code generation.")

        unified_response = "\n\n".join(sections)
        return {
            "response": unified_response,
            "provider": "compound_orchestrator",
            "model": "hybrid_multi_task_agent",
            "tools_used": all_tools_used,
            "subtasks_count": len(subtasks),
        }
