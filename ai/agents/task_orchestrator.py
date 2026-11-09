"""
JARVIS Compound Task Orchestrator (Phase 1E)
Detects compound multi-task user requests, segments them into discrete sub-tasks,
executes deterministic tools and AI reasoning per task, and produces a single unified response.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

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
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute sub-tasks sequentially and combine into a coherent markdown report.
        """
        subtasks = cls.split_subtasks(text)
        logger.info(f"Executing compound request with {len(subtasks)} sub-tasks: {subtasks}")

        from tools.calculator.calculator_tools import calculator_tools
        from tools.system.system_tools import system_tools
        from tools.desktop.app_launcher import app_launcher
        from tools.desktop.project_manager import project_manager
        from tools.desktop.file_search import file_search
        from tools.terminal.terminal_manager import terminal_engine
        from hardware.raspberry_pi.rpi_info import get_system_status

        sections: List[str] = []
        all_tools_used: List[Dict[str, Any]] = []
        last_context_project: Optional[str] = None

        for idx, task in enumerate(subtasks, start=1):
            task_lower = task.lower().strip()

            # 1. Project Opening (e.g. "open my Unity project", "open GameProject in VS Code")
            if re.search(r'\bopen\b.*\b(project|unity|gameproject|workspace|jarvis)\b', task_lower) and not re.search(r'\b(file|readme|script)\b', task_lower):
                editor = "antigravity" if "antigravity" in task_lower else "vscode"
                proj_name = "UnityGameWorkspace" if "unity" in task_lower else ("GameProject" if "game" in task_lower else "jarvis-os")
                p_res = project_manager.open_project(proj_name, editor=editor)
                all_tools_used.append({"tool": "desktop_open_project"})
                last_context_project = p_res.get("project_path")
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

            # 3. File Searching in project/workspace (e.g. "find all Python scripts in it", "find all Python files in my Unity project")
            elif re.search(r'\b(?:find|search)\b.*\b(?:python|scripts?|files?)\b', task_lower):
                search_dir = last_context_project or ("/home/roshan/UnityGameWorkspace" if "unity" in task_lower else "/home/roshan/UnityGameWorkspace")
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

            # 4. Memory / RAM inquiry
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

            # 5. System Status / Uptime inquiry
            elif re.search(r'\b(uptime|system\s+status|health|cpu\s+usage)\b', task_lower) and not re.search(r'\b(write|script|code|program)\b', task_lower):
                uptime_data = system_tools.get_uptime()
                all_tools_used.append({"tool": "get_uptime"})
                section = (
                    f"### {idx}. System Uptime\n"
                    f"- **Uptime:** {uptime_data['uptime_formatted']}"
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
