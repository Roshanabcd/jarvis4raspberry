"""
JARVIS Desktop File and Content Search Engine
Performs bounded, secure filesystem searches by filename, extension, size,
date, and file content (grep) across workspace directories.
"""
from __future__ import annotations

import fnmatch
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("JARVIS-FILE-SEARCH")

NOISY_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__",
    ".pytest_cache", ".venv", "venv", ".mypy_cache",
    ".cache", "dist", "build", "target", ".idea", ".vscode"
}


class DesktopFileSearch:
    """Fast, safe search engine for files and file contents."""

    def __init__(self, default_root: Optional[str] = None) -> None:
        self.default_root = default_root or os.path.expanduser("~")

    def _should_skip_dir(self, dir_name: str) -> bool:
        return dir_name in NOISY_DIRS or dir_name.startswith(".")

    def search_files(
        self,
        directory: Optional[str] = None,
        pattern: str = "*",
        extension: Optional[str] = None,
        max_results: int = 50,
        max_depth: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search directory for files matching filename pattern or extension."""
        root_dir = os.path.realpath(os.path.expanduser(directory or self.default_root))
        if not os.path.exists(root_dir):
            return []

        # Format extension if provided
        norm_ext = extension.strip().lower() if extension else None
        if norm_ext and not norm_ext.startswith("."):
            norm_ext = f".{norm_ext}"

        matches = []
        try:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                # Filter out noisy directories in-place
                dirnames[:] = [d for d in dirnames if not self._should_skip_dir(d)]

                # Check max depth relative to root
                rel = os.path.relpath(dirpath, root_dir)
                depth = 0 if rel == "." else len(Path(rel).parts)
                if depth > max_depth:
                    dirnames.clear()
                    continue

                for fname in filenames:
                    if norm_ext and not fname.lower().endswith(norm_ext):
                        continue
                    if pattern and pattern != "*" and not fnmatch.fnmatch(fname.lower(), pattern.lower()):
                        continue

                    full_path = os.path.join(dirpath, fname)
                    try:
                        st = os.stat(full_path)
                        matches.append({
                            "name": fname,
                            "path": full_path,
                            "relative_path": os.path.relpath(full_path, root_dir),
                            "size_bytes": st.st_size,
                            "size_str": f"{st.st_size / 1024:.1f} KB" if st.st_size >= 1024 else f"{st.st_size} B",
                            "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
                            "is_dir": False,
                        })
                    except Exception:
                        pass

                    if len(matches) >= max_results:
                        return matches
        except Exception as e:
            logger.error(f"search_files error in {root_dir}: {e}")

        return matches

    def search_content(
        self,
        query: str,
        directory: Optional[str] = None,
        file_pattern: Optional[str] = None,
        max_results: int = 25,
        max_depth: int = 4,
    ) -> List[Dict[str, Any]]:
        """Search text content within source files (similar to grep -rnI)."""
        root_dir = os.path.realpath(os.path.expanduser(directory or self.default_root))
        if not os.path.exists(root_dir):
            return []

        clean_q = query.strip()
        if not clean_q:
            return []

        # Try fast ripgrep if installed, fallback to grep or python walk
        matches = []
        try:
            # Use grep -rnI with directory exclude patterns
            cmd = ["grep", "-rnI", "-i", "--max-count=5"]
            for nd in NOISY_DIRS:
                cmd.extend([f"--exclude-dir={nd}"])
            if file_pattern:
                cmd.extend([f"--include={file_pattern}"])
            cmd.extend([clean_q, root_dir])

            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
            lines = res.stdout.strip().splitlines()
            for line in lines[:max_results]:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    fpath = parts[0].strip()
                    lineno = parts[1].strip()
                    text_match = parts[2].strip()
                    matches.append({
                        "file": fpath,
                        "line": int(lineno) if lineno.isdigit() else 1,
                        "content": text_match[:180],
                    })
        except Exception as e:
            logger.debug(f"Grep search error, falling back to python walk: {e}")
            # Python walk fallback
            q_lower = clean_q.lower()
            for root, dirs, files in os.walk(root_dir):
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
                for f in files:
                    if file_pattern and not fnmatch.fnmatch(f, file_pattern):
                        continue
                    full_p = os.path.join(root, f)
                    try:
                        if os.path.getsize(full_p) > 2 * 1024 * 1024:  # Skip > 2MB files
                            continue
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as fh:
                            for idx, line in enumerate(fh, 1):
                                if q_lower in line.lower():
                                    matches.append({
                                        "file": full_p,
                                        "line": idx,
                                        "content": line.strip()[:180],
                                    })
                                    if len(matches) >= max_results:
                                        return matches
                    except Exception:
                        pass

        return matches


file_search = DesktopFileSearch()
