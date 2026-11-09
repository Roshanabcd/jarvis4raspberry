"""Filesystem tools for JARVIS OS.

Provides secure filesystem operations strictly constrained within approved
workspace boundaries (HOME, PROJECTS, JARVIS_DATA) to prevent unauthorized file access.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import shutil
import subprocess
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

        # 2. Defaults with fallback (HOME is real user home; PROJECTS is jarvis installation)
        home_path = cfg_workspaces.get("home") or home_dir
        projects_path = cfg_workspaces.get("projects") or os.environ.get("JARVIS_PROJECTS") or os.environ.get("JARVIS_HOME") or project_root
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

    def search_folders(self, query: str, directory: Optional[str] = None, max_results: int = 15) -> List[Dict[str, Any]]:
        """Search recursively for folders/directories matching query string.

        Args:
            query: Folder name or substring to search for.
            directory: Root directory to search within (defaults to HOME).
            max_results: Maximum number of folder matches to return.

        Returns:
            List of matching folder dictionaries with name, path, item_count, and size.
        """
        root_dir = directory or self.workspaces.get("HOME", os.path.expanduser("~"))
        safe_dir = self.validate_path(root_dir)
        clean_query = query.lower().strip()

        matches: List[Dict[str, Any]] = []
        skip_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__", ".cache", ".pytest_cache", ".config"}

        for root, dirs, _ in os.walk(safe_dir):
            # Prune noisy directories in-place
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]

            for dname in dirs:
                if clean_query in dname.lower():
                    full_p = os.path.join(root, dname)
                    item_count = 0
                    try:
                        item_count = len(os.listdir(full_p))
                    except Exception:
                        pass
                    matches.append({
                        "name": dname,
                        "path": full_p,
                        "relative_path": os.path.relpath(full_p, safe_dir),
                        "items_count": item_count,
                        "is_dir": True,
                    })
                    if len(matches) >= max_results:
                        return matches

        return matches

    def open_folder(self, folder_name: str, parent_location: Optional[str] = None) -> Dict[str, Any]:
        """Resolve a folder path, list its contents, and open in desktop file manager (pcmanfm/xdg-open).

        Args:
            folder_name: Name of target folder (e.g. 'Downloads', 'abc', 'global-press').
            parent_location: Optional parent path where folder is located (e.g. 'pqr location', 'Downloads').

        Returns:
            Dictionary with open status, folder path, and item summary.
        """
        home = self.workspaces.get("HOME", os.path.expanduser("~"))
        clean_name = folder_name.strip().strip("'\"")

        standard_folders = {
            "downloads": os.path.join(home, "Downloads"),
            "download": os.path.join(home, "Downloads"),
            "music": os.path.join(home, "Music"),
            "desktop": os.path.join(home, "Desktop"),
            "documents": os.path.join(home, "Documents"),
            "document": os.path.join(home, "Documents"),
            "home": home,
            "pictures": os.path.join(home, "Pictures"),
            "picture": os.path.join(home, "Pictures"),
            "videos": os.path.join(home, "Videos"),
            "video": os.path.join(home, "Videos"),
        }

        target_path = None

        # 1. Check parent_location if specified
        if parent_location:
            p_clean = parent_location.strip().strip("'\"")
            p_mapped = standard_folders.get(p_clean.lower(), p_clean)
            if not os.path.isabs(p_mapped):
                # Search if p_mapped is a directory under home
                p_candidate = os.path.join(home, p_mapped)
                if os.path.exists(p_candidate):
                    p_mapped = p_candidate
                else:
                    parent_matches = self.search_folders(p_clean, max_results=1)
                    if parent_matches:
                        p_mapped = parent_matches[0]["path"]

            direct_in_parent = os.path.join(p_mapped, clean_name)
            if os.path.exists(direct_in_parent) and os.path.isdir(direct_in_parent):
                target_path = direct_in_parent
            else:
                # Search inside parent directory
                sub_matches = self.search_folders(clean_name, directory=p_mapped, max_results=1)
                if sub_matches:
                    target_path = sub_matches[0]["path"]

        # 2. Check standard folders
        if not target_path and clean_name.lower() in standard_folders:
            target_path = standard_folders[clean_name.lower()]

        # 3. Check direct path under home or absolute
        if not target_path:
            direct = os.path.expanduser(clean_name) if clean_name.startswith("~") else os.path.join(home, clean_name)
            if os.path.exists(direct) and os.path.isdir(direct):
                target_path = direct

        # 4. Fuzzy search across HOME
        if not target_path:
            matches = self.search_folders(clean_name, max_results=1)
            if matches:
                target_path = matches[0]["path"]

        if not target_path or not os.path.exists(target_path):
            return {
                "status": "not_found",
                "folder_name": folder_name,
                "parent_location": parent_location,
                "message": f"Could not find folder '{folder_name}'" + (f" in '{parent_location}'" if parent_location else "") + ".",
            }

        safe_path = self.validate_path(target_path)
        items = self.list_dir(safe_path)

        # Launch GUI file manager (pcmanfm or xdg-open)
        gui_launched = False
        fm_bin = shutil.which("pcmanfm") or shutil.which("xdg-open")
        if fm_bin:
            env = os.environ.copy()
            if "DISPLAY" not in env:
                env["DISPLAY"] = ":0"
            try:
                subprocess.Popen([fm_bin, safe_path], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                gui_launched = True
            except Exception as e:
                logger.warning(f"Could not launch file manager: {e}")

        top_names = [it["name"] + ("/" if it["is_dir"] else "") for it in items[:10]]
        items_summary = ", ".join(top_names) if top_names else "empty"

        return {
            "status": "opened",
            "path": safe_path,
            "name": os.path.basename(safe_path),
            "total_items": len(items),
            "items": top_names,
            "gui_launched": gui_launched,
            "message": f"Opened folder '{os.path.basename(safe_path)}' at {safe_path}. It contains {len(items)} items: {items_summary}.",
        }

    def open_file(self, file_path: str, editor: Optional[str] = None) -> Dict[str, Any]:
        """Open a file with standard editor (mousepad, code, or xdg-open).

        Args:
            file_path: Relative or absolute file path.
            editor: Preferred editor ('mousepad', 'code', etc.).

        Returns:
            Dictionary with open status.
        """
        home = self.workspaces.get("HOME", os.path.expanduser("~"))
        target = file_path if os.path.isabs(file_path) else os.path.join(home, file_path)
        if not os.path.exists(target):
            # Try searching for file
            matches = self.search_files(home, f"*{file_path}*")
            if matches:
                target = matches[0]

        if not os.path.exists(target):
            return {"status": "not_found", "path": file_path, "message": f"File '{file_path}' not found."}

        safe_path = self.validate_path(target)
        ed_bin = shutil.which(editor) if editor else (shutil.which("mousepad") or shutil.which("xdg-open"))
        if not ed_bin:
            return {"status": "error", "message": "No editor found to open file."}

        env = os.environ.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"

        try:
            p = subprocess.Popen([ed_bin, safe_path], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {
                "status": "opened",
                "path": safe_path,
                "editor": ed_bin,
                "pid": p.pid,
                "message": f"Opened file '{os.path.basename(safe_path)}' in {os.path.basename(ed_bin)}.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to open file: {e}"}


# Global instance
file_tools = FileTools()
