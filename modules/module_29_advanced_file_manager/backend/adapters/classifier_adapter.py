"""File classification adapter contract for Module 29."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class FileClassifierAdapter(ABC):
    adapter_name: str = "abstract_classifier"
    is_simulated: bool = False

    @abstractmethod
    def classify(self, filename: str) -> str:
        """Return target category directory name for a file."""


class LocalRuleFileClassifierAdapter(FileClassifierAdapter):
    """Real deterministic extension-based classifier (no external API needed)."""

    adapter_name = "local_rule_file_classifier"
    is_simulated = False

    EXT_MAP = {
        ".md": "documents",
        ".txt": "documents",
        ".pdf": "documents",
        ".docx": "documents",
        ".py": "code",
        ".js": "code",
        ".ts": "code",
        ".tsx": "code",
        ".html": "code",
        ".css": "code",
        ".csv": "data",
        ".json": "data",
        ".yaml": "data",
        ".yml": "data",
        ".sql": "data",
        ".png": "media",
        ".jpg": "media",
        ".jpeg": "media",
        ".mp4": "media",
        ".mp3": "media",
        ".zip": "archives",
        ".tar": "archives",
        ".gz": "archives",
    }

    def classify(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        return self.EXT_MAP.get(ext, "other")
