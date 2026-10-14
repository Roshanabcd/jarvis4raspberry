"""Filesystem tools for JARVIS OS.

Provides secure filesystem operations strictly constrained within approved
workspace boundaries (HOME, PROJECTS, JARVIS_DATA) to prevent unauthorized file access.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.config_manager import config

logger = logging.getLogger("JARVIS-FILESYSTEM")


class FileTools:
    """Secure filesystem operations constrained to allowed workspace directories."""

    def __init__(self, allowed_workspaces: Optional[Dict[str, str]] = None) -> None:
        """Initialize FileTools with workspace boundaries.

        Args:
            allowed_workspaces: Optional dictionary mapping workspace names to directory paths.
        """
        self.workspaces: Dict[str, str] = {}
        self._load_workspaces(allowed_workspaces)

    def _load_workspaces(self, custom_workspaces: Optional[Dict[str, str]] = None) -> None:
        """Resolve and store absolute paths for authorized workspaces."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        home_dir = os.path.expanduser("~")

        # 1. Configured workspaces
        cfg_workspaces = config.get("workspaces", {}) if hasattr(config, "get") else {}
        if not isinstance(cfg_workspaces, dict):
            cfg_workspaces = {}

        # 2. Defaults with fallback
        home_path = cfg_workspaces.get("home") or os.environ.get("JARVIS_HOME") or home_dir
        projects_path = cfg_workspaces.get("projects") or os.environ.get("JARVIS_PROJECTS") or project_root
        data_path = cfg_workspaces.get("jarvis_data") or os.environ.get("JARVIS_DATA") or os.path.join(project_root, "data")

        raw_workspaces = {
            "HOME": os.path.expanduser(str(home_path)),
            "PROJECTS": os.path.expanduser(str(projects_path)),
            "JARVIS_DATA": os.path.expanduser(str(data_path)),
        }

        if custom_workspaces:
            for k, v in custom_workspaces.items():
                raw_workspaces[k.upper()] = os.path.expanduser(str(v))

        # Canonicalize all workspace paths
        for name, path in raw_workspaces.items():
            abs_path = os.path.realpath(path)
            self.workspaces[name] = abs_path

        logger.info(f"Initialized FileTools with workspaces: {list(self.workspaces.keys())}")

    def validate_path(self, path: str) -> str:
        """Verify that a path is strictly inside one of the allowed workspaces.

        Args:
            path: Target file or directory path string.

        Returns:
            Resolved canonical absolute path.

        Raises:
            PermissionError: If path resolves outside allowed workspaces.
            ValueError: If path is empty or invalid.
        """
        if not path or not isinstance(path, str) or not path.strip():
            raise ValueError("Path must be a non-empty string.")

        expanded = os.path.expanduser(path.strip())
        real_target = os.path.realpath(expanded)

        for ws_name, ws_path in self.workspaces.items():
            # Check if real_target starts with ws_path
            try:
                common = os.path.commonpath([real_target, ws_path])
                if common == ws_path:
                    return real_target
            except ValueError:
                # Paths on different drives/mounts
                continue

        logger.warning(f"Path traversal check failed: '{path}' -> '{real_target}' is outside allowed workspaces.")
        raise PermissionError(f"Access denied: Path '{path}' is outside authorized workspaces.")

    def read_file(self, path: str) -> str:
        """Read text content from a file within allowed workspaces.

        Args:
            path: File path to read.

        Returns:
            Contents of the file as string.
        """
        safe_path = self.validate_path(path)
        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"File not found: '{path}'")
        if not os.path.isfile(safe_path):
            raise IsADirectoryError(f"Target is a directory, not a file: '{path}'")

        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write text content to a file within allowed workspaces.

        Args:
            path: Target file path.
            content: Content to write.

        Returns:
            Dictionary with operation status and byte count.
        """
        safe_path = self.validate_path(path)
        simulated = config.get("simulation_mode", True)

        os.makedirs(os.path.dirname(safe_path), exist_ok=True)

        if simulated:
            logger.info(f"[SIM] Writing {len(content)} characters to '{safe_path}'")

        with open(safe_path, "w", encoding="utf-8") as f:
            bytes_written = f.write(content)

        return {"path": safe_path, "bytes_written": bytes_written, "simulated": simulated}

    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """Append text content to a file within allowed workspaces.

        Args:
            path: Target file path.
            content: Content to append.

        Returns:
            Dictionary with operation status and byte count appended.
        """
        safe_path = self.validate_path(path)
        simulated = config.get("simulation_mode", True)

        os.makedirs(os.path.dirname(safe_path), exist_ok=True)

        if simulated:
            logger.info(f"[SIM] Appending {len(content)} characters to '{safe_path}'")

        with open(safe_path, "a", encoding="utf-8") as f:
            bytes_written = f.write(content)

        return {"path": safe_path, "bytes_appended": bytes_written, "simulated": simulated}

    def create_dir(self, path: str) -> Dict[str, Any]:
        """Create a directory recursively within allowed workspaces.

        Args:
            path: Directory path to create.

        Returns:
            Dictionary with path and creation flag.
        """
        safe_path = self.validate_path(path)
        simulated = config.get("simulation_mode", True)

        if simulated:
            logger.info(f"[SIM] Creating directory '{safe_path}'")

        created = not os.path.exists(safe_path)
        os.makedirs(safe_path, exist_ok=True)
        return {"path": safe_path, "created": created, "simulated": simulated}

    def list_dir(self, path: str) -> List[Dict[str, Any]]:
        """List contents of a directory within allowed workspaces.

        Args:
            path: Directory path to inspect.

        Returns:
            List of dictionaries describing directory entries.
        """
        safe_path = self.validate_path(path)
        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"Directory not found: '{path}'")
        if not os.path.isdir(safe_path):
            raise NotADirectoryError(f"Target is not a directory: '{path}'")

        results: List[Dict[str, Any]] = []
        for entry in os.scandir(safe_path):
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                size = entry.stat().st_size if not is_dir else 0
                results.append({
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": is_dir,
                    "size_bytes": size,
                })
            except OSError:
                continue

        results.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return results

    def copy_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Copy a file from src to dst, validating workspace constraints on both.

        Args:
            src: Source file path.
            dst: Destination file path.

        Returns:
            Dictionary describing copy result.
        """
        safe_src = self.validate_path(src)
        safe_dst = self.validate_path(dst)
        simulated = config.get("simulation_mode", True)

        if not os.path.exists(safe_src):
            raise FileNotFoundError(f"Source file not found: '{src}'")

        os.makedirs(os.path.dirname(safe_dst), exist_ok=True)

        if simulated:
            logger.info(f"[SIM] Copying '{safe_src}' -> '{safe_dst}'")

        shutil.copy2(safe_src, safe_dst)
        return {"src": safe_src, "dst": safe_dst, "status": "copied", "simulated": simulated}

    def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Move a file from src to dst, validating workspace constraints on both.

        Args:
            src: Source file path.
            dst: Destination file path.

        Returns:
            Dictionary describing move result.
        """
        safe_src = self.validate_path(src)
        safe_dst = self.validate_path(dst)
        simulated = config.get("simulation_mode", True)

        if not os.path.exists(safe_src):
            raise FileNotFoundError(f"Source file not found: '{src}'")

        os.makedirs(os.path.dirname(safe_dst), exist_ok=True)

        if simulated:
            logger.info(f"[SIM] Moving '{safe_src}' -> '{safe_dst}'")

        shutil.move(safe_src, safe_dst)
        return {"src": safe_src, "dst": safe_dst, "status": "moved", "simulated": simulated}

    def delete_file(self, path: str, confirmed: bool = False) -> Dict[str, Any]:
        """Delete a file or directory within allowed workspaces. Requires confirmation.

        Risk Level: 2 (deletion requires confirmed=True).

        Args:
            path: Target file or directory path.
            confirmed: Explicit confirmation flag.

        Returns:
            Dictionary describing deletion result.

        Raises:
            PermissionError: If confirmed is False or path is forbidden.
            FileNotFoundError: If target path does not exist.
        """
        if not confirmed:
            raise PermissionError(
                f"Confirmation required: delete_file operation on '{path}' is risk level >= 2."
            )

        safe_path = self.validate_path(path)
        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"File or directory not found: '{path}'")

        simulated = config.get("simulation_mode", True)
        if simulated:
            logger.warning(f"[SIM] Simulating deletion of '{safe_path}' (confirmed=True)")
            return {"path": safe_path, "deleted": True, "simulated": True}

        if os.path.isdir(safe_path):
            shutil.rmtree(safe_path)
        else:
            os.remove(safe_path)

        return {"path": safe_path, "deleted": True, "simulated": False}

    def search_files(self, directory: str, pattern: str) -> List[str]:
        """Search recursively for files matching a pattern inside a directory.

        Args:
            directory: Directory to search within.
            pattern: Glob-style filename pattern (e.g., '*.py').

        Returns:
            List of matching relative or absolute file paths.
        """
        safe_dir = self.validate_path(directory)
        if not os.path.exists(safe_dir):
            raise FileNotFoundError(f"Search directory not found: '{directory}'")
        if not os.path.isdir(safe_dir):
            raise NotADirectoryError(f"Search target is not a directory: '{directory}'")

        matches: List[str] = []
        for root, _, files in os.walk(safe_dir):
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    matches.append(os.path.join(root, filename))

        return matches


# Global instance
file_tools = FileTools()
