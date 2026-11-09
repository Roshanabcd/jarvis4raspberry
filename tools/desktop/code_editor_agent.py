"""
JARVIS OS — Phase 4 Code & File Editing Agent
Provides direct, safe filesystem code reading, targeted editing with git diffs,
editor window opening, and automated test execution.
"""

import os
import difflib
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from tools.terminal.terminal_manager import terminal_engine

logger = logging.getLogger("JARVIS.CodeEditor")

class CodeEditorAgent:
    """Safely reads, modifies, and validates source code files in user projects."""

    def read_source_file(
        self,
        filepath: str,
        start_line: int = 1,
        end_line: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read source file accurately with line numbers."""
        path = Path(filepath)
        if not path.is_absolute():
            path = Path("/home/roshan") / path

        if not path.exists():
            return {"status": "error", "message": f"File '{filepath}' not found"}

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            s_idx = max(0, start_line - 1)
            e_idx = min(total_lines, end_line) if end_line else total_lines

            selected_lines = lines[s_idx:e_idx]
            numbered = "".join(f"{i + s_idx + 1:4d} | {line}" for i, line in enumerate(selected_lines))

            return {
                "status": "ok",
                "filepath": str(path),
                "total_lines": total_lines,
                "start_line": s_idx + 1,
                "end_line": e_idx,
                "content": "".join(selected_lines),
                "numbered_content": numbered,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def open_in_editor(
        self,
        filepath: str,
        line: Optional[int] = None,
        editor: str = "vscode"
    ) -> Dict[str, Any]:
        """Open file in VS Code or Antigravity IDE at specified line."""
        path = str(filepath)
        target = f"{path}:{line}" if line else path

        if editor.lower() in ("vscode", "code"):
            cmd = ["code", "-g", target]
        else:
            cmd = ["/home/roshan/Downloads/Antigravity-arm64/antigravity", path]

        try:
            subprocess.Popen(
                cmd,
                env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")},
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return {
                "status": "ok",
                "editor": editor,
                "filepath": path,
                "line": line,
                "message": f"Opened '{path}' in {editor.upper()}",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def apply_targeted_edit(
        self,
        filepath: str,
        target_snippet: str,
        replacement_snippet: str,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """Perform targeted drop-in code edit, preserving formatting and producing a git diff."""
        path = Path(filepath)
        if not path.is_absolute():
            path = Path("/home/roshan") / path

        if not path.exists():
            return {"status": "error", "message": f"File '{filepath}' not found"}

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if target_snippet not in content:
                return {
                    "status": "error",
                    "message": "Target snippet does not match existing file content exactly.",
                }

            if content.count(target_snippet) > 1:
                return {
                    "status": "error",
                    "message": "Target snippet occurs multiple times. Provide more surrounding context.",
                }

            if create_backup:
                backup_path = path.with_suffix(path.suffix + ".bak")
                with open(backup_path, "w", encoding="utf-8") as bf:
                    bf.write(content)

            new_content = content.replace(target_snippet, replacement_snippet, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Generate unified diff
            diff = difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path.name}",
                tofile=f"b/{path.name}",
            )
            diff_text = "".join(diff)

            return {
                "status": "ok",
                "filepath": str(path),
                "modified": True,
                "diff": diff_text,
                "message": f"Successfully applied edit to {path.name}",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run_tests(self, test_target: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute pytest in project directory."""
        work_dir = cwd or "/home/roshan/.gemini/antigravity/scratch/jarvis-os"
        cmd = f"pytest {test_target} -v"
        res = terminal_engine.execute_command(cmd, cwd=work_dir)
        stdout = res.get("stdout", "")
        stderr = res.get("stderr", "")

        passed = "passed" in stdout.lower() and res.get("exit_code") == 0
        return {
            "status": "ok" if passed else "failed",
            "exit_code": res.get("exit_code"),
            "passed": passed,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": res.get("duration_ms"),
        }


code_editor_agent = CodeEditorAgent()
