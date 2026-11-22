"""Central Path Resolver for JARVIS OS.

Enforces /home/roshan/.gemini/antigravity/scratch/jarvis-os as the single
canonical parent directory (JARVIS_ROOT) for all modules, data, captures,
screenshots, photos, databases, logs, notebooks, and worktrees.
"""

import os
from pathlib import Path
from typing import Union

# Primary canonical root
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
JARVIS_ROOT = Path(os.environ.get("JARVIS_ROOT", str(_DEFAULT_ROOT))).resolve()

# Code & Module directories
MODULES_DIR = JARVIS_ROOT / "modules"
NOTEBOOKS_DIR = JARVIS_ROOT / "notebooks"
LOGS_DIR = JARVIS_ROOT / "logs"
WORKTREES_DIR = JARVIS_ROOT / ".worktrees"

# Runtime data & artifact storage
DATA_DIR = JARVIS_ROOT / "data"
CAPTURES_DIR = DATA_DIR / "captures"
PHOTOS_DIR = DATA_DIR / "photos"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DOWNLOADS_DIR = DATA_DIR / "downloads"
DB_DIR = DATA_DIR / "db"
VOICE_SAMPLES_DIR = DATA_DIR / "voice_samples"
MODULE_ARCHIVES_DIR = DATA_DIR / "module_archives"


def ensure_runtime_dirs() -> None:
    """Ensure all canonical runtime artifact directories exist within JARVIS_ROOT."""
    dirs = [
        MODULES_DIR,
        NOTEBOOKS_DIR,
        LOGS_DIR,
        WORKTREES_DIR,
        DATA_DIR,
        CAPTURES_DIR,
        PHOTOS_DIR,
        SCREENSHOTS_DIR,
        DOWNLOADS_DIR,
        DB_DIR,
        VOICE_SAMPLES_DIR,
        MODULE_ARCHIVES_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def is_contained_in_root(target: Union[str, Path]) -> bool:
    """Check if the target path resides strictly inside JARVIS_ROOT."""
    try:
        resolved = Path(target).resolve()
        return resolved == JARVIS_ROOT or resolved.is_relative_to(JARVIS_ROOT)
    except Exception:
        return False


def resolve_contained_path(relative_or_absolute: Union[str, Path], default_subdir: Path = DATA_DIR) -> Path:
    """
    Resolve a path ensuring it stays inside JARVIS_ROOT.
    If an absolute path outside JARVIS_ROOT is provided, maps its basename into default_subdir.
    """
    p = Path(relative_or_absolute)
    if not p.is_absolute():
        resolved = (JARVIS_ROOT / p).resolve()
    else:
        resolved = p.resolve()

    if is_contained_in_root(resolved):
        return resolved

    # Remap outside path into the designated self-contained directory
    return (default_subdir / p.name).resolve()


# Initialize core directories on import
ensure_runtime_dirs()
