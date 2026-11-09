"""
Problem Context Packager for JARVIS OS Phase 5.
Extracts, structures, and sanitizes failure diagnostics, error traces,
git diffs, and relevant source files into a safe, bounded debugging request.
Never transmits secrets, passwords, or .env files.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.agents.models import ProblemContext

logger = logging.getLogger("JARVIS.ContextPackager")

# Sensitive files that must NEVER be packaged
PROHIBITED_FILES = {
    ".env", ".env.local", ".env.production",
    "id_rsa", "id_ed25519", "authorized_keys",
    "cookies.txt", "credentials.json", "secrets.yaml",
}

# Sensitive regex patterns to scrub from text
SECRET_PATTERNS = [
    r"(?i)(?:api_key|apikey|token|password|secret|auth)[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?",
    r"ghp_[a-zA-Z0-9]{36}",
    r"sk-[a-zA-Z0-9]{32,}",
]


class ProblemContextPackager:
    """Structures failure context while enforcing strict privacy and minimal data exposure."""

    def __init__(self, workspace_root: str = "/home/roshan/.gemini/antigravity/scratch/jarvis-os"):
        self.workspace_root = Path(workspace_root)

    def package_failure(
        self,
        original_request: str,
        error_message: str,
        traceback: str = "",
        failed_command: Optional[str] = None,
        exit_code: Optional[int] = None,
        working_dir: Optional[str] = None,
        target_files: Optional[List[str]] = None,
        reproduction_cmd: Optional[str] = None,
        expected: str = "",
        actual: str = "",
    ) -> ProblemContext:
        """Construct a sanitized, bounded ProblemContext object."""
        w_dir = working_dir or str(self.workspace_root)

        # 1. Identify affected component
        affected = self._detect_affected_component(traceback, error_message, target_files)

        # 2. Collect minimal relevant files (max 3)
        files_to_read = list(target_files or [])
        if affected and affected not in files_to_read:
            files_to_read.append(affected)

        file_contents: Dict[str, str] = {}
        for fpath in files_to_read[:3]:
            # Guard against prohibited files
            fname = Path(fpath).name.lower()
            if fname in PROHIBITED_FILES or fname.endswith((".key", ".pem", ".p12", ".pfx")):
                logger.warning("Excluded prohibited secret file from context package: %s", fpath)
                continue

            full_path = Path(fpath) if Path(fpath).is_absolute() else Path(w_dir) / fpath
            if full_path.exists() and full_path.is_file():
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        raw_content = f.read()
                    # Sanitize any accidental secrets in code
                    sanitized_code = self._scrub_secrets(raw_content)
                    file_contents[str(fpath)] = sanitized_code
                except Exception as e:
                    logger.warning("Could not read file for context packaging: %s", e)

        # 3. Collect recent git diff
        git_diff = self._get_recent_diff(w_dir)

        # 4. Sanitize error message and traceback
        clean_err = self._scrub_secrets(error_message)
        clean_tb = self._scrub_secrets(traceback)

        return ProblemContext(
            original_request=original_request,
            failure_type="TEST_FAILURE" if "pytest" in (failed_command or "") or "AssertionError" in error_message else "EXECUTION_ERROR",
            error_message=clean_err,
            traceback=clean_tb,
            failed_command=failed_command,
            exit_code=exit_code,
            working_dir=w_dir,
            affected_component=affected,
            relevant_files=list(file_contents.keys()),
            file_contents=file_contents,
            recent_git_diff=git_diff,
            reproduction_instructions=reproduction_cmd or (f"Run: {failed_command}" if failed_command else "Run tests"),
            expected_behavior=expected or "Operation completes with exit code 0 and valid output.",
            actual_behavior=actual or clean_err,
        )

    def _detect_affected_component(
        self,
        traceback: str,
        error_message: str,
        target_files: Optional[List[str]] = None
    ) -> Optional[str]:
        """Infer target python source file from traceback stack."""
        if target_files and len(target_files) > 0:
            return target_files[0]

        # Scan traceback for File "...", line ...
        matches = re.findall(r'File "([^"]+\.py)"', traceback)
        if matches:
            # Pick the deepest project file
            for cand in reversed(matches):
                if not cand.startswith("/usr") and "site-packages" not in cand:
                    return cand
            return matches[-1]

        # Scan error message for .py
        m_err = re.search(r'([a-zA-Z0-9_\-\.\/]+\.py)', error_message)
        if m_err:
            return m_err.group(1)

        return None

    def _get_recent_diff(self, working_dir: str) -> str:
        """Safely fetch git diff in workspace without blocking."""
        try:
            res = subprocess.run(
                ["git", "diff", "--stat", "-p", "HEAD~1"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
            if res.returncode == 0 and res.stdout:
                return self._scrub_secrets(res.stdout[:2000])  # limit length
        except Exception:
            pass
        return ""

    def is_prohibited_file(self, fpath: str) -> bool:
        fname = Path(fpath).name.lower()
        return fname in PROHIBITED_FILES or fname.endswith((".key", ".pem", ".p12", ".pfx"))

    def scrub_secrets(self, text: str) -> str:
        return self._scrub_secrets(text)

    def _scrub_secrets(self, text: str) -> str:
        """Replace sensitive patterns with [REDACTED_SECRET]."""
        clean = text
        for pat in SECRET_PATTERNS:
            clean = re.sub(pat, "[REDACTED_SECRET]", clean)
        return clean


context_packager = ProblemContextPackager()
