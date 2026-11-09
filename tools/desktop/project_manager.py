"""
JARVIS Project Manager
Resolves project directories across configured workspaces, recognizes project
markers (.git, pyproject.toml, package.json, Unity Assets/), and launches projects
in VS Code or Antigravity IDE with verification.
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.desktop.app_launcher import app_launcher

logger = logging.getLogger("JARVIS-PROJECT-MANAGER")

PROJECT_MARKERS = [
    ".git",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "Makefile",
    "CMakeLists.txt",
    "Assets",  # Unity
    "ProjectSettings",  # Unity
    "UnityGameWorkspace",
]


class DesktopProjectManager:
    """Manages project discovery and IDE opening."""

    def __init__(self, workspace_roots: Optional[List[str]] = None) -> None:
        home = os.path.expanduser("~")
        self.workspace_roots: List[str] = workspace_roots or [
            os.path.join(home, "UnityGameWorkspace"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, ".openclaw", "workspace"),
            home,
        ]
        self._registered_projects: Dict[str, str] = {
            "jarvis-os": "/home/roshan/.gemini/antigravity/scratch/jarvis-os",
            "jarvis": "/home/roshan/.gemini/antigravity/scratch/jarvis-os",
            "antigravity": "/home/roshan/Downloads/Antigravity-arm64",
        }

    def register_project(self, name: str, path: str) -> bool:
        """Explicitly register a project by name and path."""
        clean_p = os.path.realpath(os.path.expanduser(path))
        if os.path.isdir(clean_p):
            self._registered_projects[name.lower().strip()] = clean_p
            return True
        return False

    def is_project_directory(self, path: str) -> bool:
        """Check if directory contains recognized project markers."""
        if not os.path.isdir(path):
            return False
        try:
            entries = set(os.listdir(path))
            return any(m in entries for m in PROJECT_MARKERS)
        except Exception:
            return False

    def find_projects(self, query: Optional[str] = None, max_results: int = 15) -> List[Dict[str, Any]]:
        """Search workspace roots for recognized projects."""
        results = []
        seen = set()

        # 1. Include registered projects
        for name, p in self._registered_projects.items():
            if os.path.exists(p):
                if not query or query.lower() in name.lower() or query.lower() in p.lower():
                    if p not in seen:
                        seen.add(p)
                        results.append({
                            "name": name,
                            "path": p,
                            "type": "registered",
                            "exists": True,
                        })

        # 2. Scan workspace roots up to depth 3
        for root in self.workspace_roots:
            if not os.path.exists(root):
                continue
            try:
                for dirpath, dirnames, _ in os.walk(root):
                    # Do not recurse into noisy or hidden directories
                    dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv")]
                    depth = len(Path(dirpath).relative_to(Path(root)).parts)
                    if depth > 3:
                        dirnames.clear()
                        continue

                    if self.is_project_directory(dirpath):
                        pname = os.path.basename(dirpath)
                        if not query or query.lower() in pname.lower() or query.lower() in dirpath.lower():
                            if dirpath not in seen:
                                seen.add(dirpath)
                                results.append({
                                    "name": pname,
                                    "path": dirpath,
                                    "type": "discovered",
                                    "exists": True,
                                })
                                if len(results) >= max_results:
                                    return results
            except Exception as e:
                logger.debug(f"Error scanning {root}: {e}")

        return results

    def resolve_project_path(self, target: str) -> Optional[str]:
        """Resolve a project name or path string to an absolute verified directory."""
        clean = target.strip().strip("'\"")

        # 1. Direct path check
        exp = os.path.realpath(os.path.expanduser(clean))
        if os.path.isdir(exp):
            return exp

        # 2. Registered name check
        if clean.lower() in self._registered_projects:
            reg_p = self._registered_projects[clean.lower()]
            if os.path.isdir(reg_p):
                return reg_p

        # 3. Check relative to workspace roots
        for root in self.workspace_roots:
            candidate = os.path.join(root, clean)
            if os.path.isdir(candidate):
                return os.path.realpath(candidate)

        # 4. Search projects by name
        matches = self.find_projects(query=clean, max_results=5)
        if matches:
            # Return exact match if available
            for m in matches:
                if m["name"].lower() == clean.lower():
                    return m["path"]
            return matches[0]["path"]

        return None

    def open_project(
        self,
        project_name_or_path: str,
        editor: str = "vscode",
    ) -> Dict[str, Any]:
        """Resolve project path and launch it in VS Code or Antigravity IDE."""
        resolved = self.resolve_project_path(project_name_or_path)
        if not resolved:
            return {
                "success": False,
                "status": "not_found",
                "project": project_name_or_path,
                "editor": editor,
                "message": f"Could not find project directory matching '{project_name_or_path}'.",
            }

        norm_editor = editor.lower().strip()
        if norm_editor in ("antigravity", "antigravity ide"):
            res = app_launcher.launch_app("antigravity", target=resolved)
        else:
            res = app_launcher.launch_app("code", target=resolved, new_window=True)

        res.update({
            "project_name": os.path.basename(resolved),
            "project_path": resolved,
            "editor": norm_editor,
        })
        return res


project_manager = DesktopProjectManager()
