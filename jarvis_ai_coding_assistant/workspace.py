"""Path-safe JARVIS workspace explorer and additive patch manager."""

from __future__ import annotations

import difflib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import CodingAssistantConfig

EXTENSION_LANGUAGES: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sh": "bash",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".ino": "cpp",
    ".sql": "sql",
    ".md": "markdown",
    ".txt": "text",
}


class WorkspaceSecurityError(ValueError):
    """Raised when a requested path escapes the configured workspace root."""


class WorkspaceManager:
    """Provides safe, sandboxed read/list/diff/apply operations on a JARVIS workspace."""

    def __init__(self, config: CodingAssistantConfig) -> None:
        self.config = config
        self.root = config.workspace_root.resolve()

    @staticmethod
    def detect_language(path: Path) -> str:
        return EXTENSION_LANGUAGES.get(path.suffix.lower(), "text")

    def resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve a path strictly inside workspace_root, rejecting traversal or symlinks out."""
        cleaned = relative_path.strip()
        if not cleaned:
            raise WorkspaceSecurityError("File path cannot be empty.")
        raw = Path(cleaned)
        if raw.is_absolute():
            candidate = raw.resolve()
        else:
            candidate = (self.root / raw).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceSecurityError(
                f"Access denied: '{relative_path}' escapes workspace root '{self.root}'."
            ) from exc
        return candidate

    def list_files(self, subdir: Optional[str] = None) -> List[Dict[str, object]]:
        """List readable source files in the workspace up to max_list_files."""
        base = self.resolve_safe_path(subdir) if subdir else self.root
        if not base.exists() or not base.is_dir():
            return []

        results: List[Dict[str, object]] = []
        ignored = set(self.config.ignored_dirs)

        for current_root, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in ignored and not d.startswith("."))
            for filename in sorted(files):
                if filename.startswith("."):
                    continue
                full_path = Path(current_root) / filename
                try:
                    resolved = full_path.resolve()
                    resolved.relative_to(self.root)
                    size = resolved.stat().st_size
                except (OSError, ValueError):
                    continue
                if size > self.config.max_file_bytes:
                    continue
                rel = resolved.relative_to(self.root).as_posix()
                results.append(
                    {
                        "path": rel,
                        "size_bytes": size,
                        "language": self.detect_language(resolved),
                    }
                )
                if len(results) >= self.config.max_list_files:
                    return results
        return results

    def read_file(self, relative_path: str) -> Tuple[str, str, int]:
        """Return (content, language, size_bytes) for a workspace file."""
        target = self.resolve_safe_path(relative_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"Workspace file not found: {relative_path}")
        size = target.stat().st_size
        if size > self.config.max_file_bytes:
            raise ValueError(
                f"File '{relative_path}' ({size} bytes) exceeds limit ({self.config.max_file_bytes} bytes)."
            )
        content = target.read_text(encoding="utf-8", errors="replace")
        return content, self.detect_language(target), size

    @staticmethod
    def build_unified_diff(
        original: str,
        updated: str,
        file_label: str = "snippet.py",
    ) -> str:
        """Compute a unified diff string between original and updated text."""
        orig_lines = original.splitlines(keepends=True)
        new_lines = updated.splitlines(keepends=True)
        diff_iter = difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{file_label}",
            tofile=f"b/{file_label}",
            lineterm="",
        )
        return "\n".join(line.rstrip("\n") for line in diff_iter)

    def apply_patch(
        self,
        relative_path: str,
        new_content: str,
        dry_run: bool = True,
        create_backup: bool = True,
    ) -> Dict[str, object]:
        """Preview or safely write updated file content with optional timestamped backup."""
        target = self.resolve_safe_path(relative_path)
        existed = target.exists()
        original = target.read_text(encoding="utf-8", errors="replace") if existed else ""
        rel_display = target.relative_to(self.root).as_posix()
        diff_text = self.build_unified_diff(original, new_content, file_label=rel_display)

        if dry_run:
            return {
                "file_path": rel_display,
                "dry_run": True,
                "applied": False,
                "created_new_file": not existed,
                "backup_path": None,
                "unified_diff": diff_text,
                "bytes_written": 0,
            }

        if not self.config.allow_workspace_writes:
            raise PermissionError(
                "Workspace writes are disabled (set JARVIS_CODING_ALLOW_WRITES=true to enable)."
            )

        backup_rel: Optional[str] = None
        if existed and create_backup:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_dir = self.root / ".jarvis_coding_assistant" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            safe_name = rel_display.replace("/", "__")
            backup_file = backup_dir / f"{safe_name}.{stamp}.bak"
            shutil.copy2(target, backup_file)
            backup_rel = backup_file.relative_to(self.root).as_posix()

        target.parent.mkdir(parents=True, exist_ok=True)
        encoded = new_content.encode("utf-8")
        target.write_bytes(encoded)

        return {
            "file_path": rel_display,
            "dry_run": False,
            "applied": True,
            "created_new_file": not existed,
            "backup_path": backup_rel,
            "unified_diff": diff_text,
            "bytes_written": len(encoded),
        }
