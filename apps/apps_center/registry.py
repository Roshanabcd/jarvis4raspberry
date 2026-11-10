"""
JARVIS OS — Centralized Application Registry.
Manages the application catalog, manifest validation, category indexing,
and truthful status reporting for all 20 JARVIS applications.
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from apps.apps_center.models import (
    ApplicationManifest,
    AppCategory,
    AppStatus,
    CATEGORY_LABELS,
    CANONICAL_APP_IDS,
)

logger = logging.getLogger("JARVIS.AppsCenter.Registry")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_FILE = PROJECT_ROOT / "data" / "apps" / "registry.json"


class ApplicationRegistry:
    """
    Centralized, thread-safe application registry for JARVIS OS.
    Guarantees strict schema validation, unique IDs, and truthful status rules.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ApplicationRegistry, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, registry_path: Optional[Path] = None):
        if self._initialized:
            return
        with self._lock:
            self._registry_path = registry_path or REGISTRY_FILE
            self._apps: Dict[str, ApplicationManifest] = {}
            self._load_registry()
            self._initialized = True

    def _load_registry(self) -> None:
        """Load and validate all application manifests from disk."""
        if not self._registry_path.exists():
            logger.warning("Registry file not found at %s. Initializing empty registry.", self._registry_path)
            self._apps = {}
            return

        try:
            with open(self._registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            catalog = data.get("catalog", [])
            seen_ids: Set[str] = set()
            loaded: Dict[str, ApplicationManifest] = {}

            for item in catalog:
                try:
                    manifest = ApplicationManifest(**item)
                    if manifest.id in seen_ids:
                        logger.error("Duplicate application ID '%s' detected; skipping duplicate.", manifest.id)
                        continue
                    seen_ids.add(manifest.id)
                    loaded[manifest.id] = manifest
                except Exception as val_err:
                    logger.error("Manifest validation failure for item '%s': %s", item.get("id", "unknown"), val_err)

            self._apps = loaded
            logger.info("Successfully loaded %d application manifests from registry.", len(self._apps))
        except Exception as e:
            logger.error("Failed to load application registry from %s: %s", self._registry_path, e)
            self._apps = {}

    def reload(self) -> int:
        """Force reload from disk."""
        with self._lock:
            self._load_registry()
            return len(self._apps)

    def get_all_apps(self) -> List[ApplicationManifest]:
        """Return all registered application manifests sorted alphabetically."""
        with self._lock:
            return sorted(self._apps.values(), key=lambda a: (a.status != AppStatus.AVAILABLE, a.name))

    def get_app(self, app_id: str) -> Optional[ApplicationManifest]:
        """Retrieve application manifest by unique ID."""
        with self._lock:
            return self._apps.get(app_id.strip().lower())

    def search_apps(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> List[ApplicationManifest]:
        """
        Multi-attribute search across application manifests.
        Matches name, category, description, capabilities, or permissions.
        """
        with self._lock:
            results = list(self._apps.values())

            if category:
                cat_clean = category.strip().lower()
                results = [a for a in results if a.category.value == cat_clean]

            if status:
                stat_clean = status.strip().lower()
                results = [a for a in results if a.status.value == stat_clean]

            if capability:
                cap_clean = capability.strip().lower()
                results = [a for a in results if any(cap_clean in c.lower() for c in a.capabilities)]

            if query:
                q = query.strip().lower()
                results = [
                    a for a in results
                    if q in a.name.lower()
                    or q in a.description.lower()
                    or q in a.category.value.lower()
                    or any(q in cap.lower() for cap in a.capabilities)
                    or any(q in perm.lower() for perm in a.permissions)
                ]

            return sorted(results, key=lambda a: (a.status != AppStatus.AVAILABLE, a.name))

    def get_categories(self) -> List[Dict[str, Any]]:
        """Return list of categories with display labels and application counts."""
        with self._lock:
            counts: Dict[str, int] = {cat.value: 0 for cat in AppCategory}
            for app in self._apps.values():
                counts[app.category.value] = counts.get(app.category.value, 0) + 1

            return [
                {
                    "id": cat.value,
                    "label": CATEGORY_LABELS.get(cat, cat.value.replace("_", " ").title()),
                    "count": counts.get(cat.value, 0),
                }
                for cat in AppCategory
            ]

    def get_available_apps(self) -> List[ApplicationManifest]:
        """Return only verified Available applications."""
        with self._lock:
            return [a for a in self._apps.values() if a.status == AppStatus.AVAILABLE]

    def get_planned_apps(self) -> List[ApplicationManifest]:
        """Return all Planned applications."""
        with self._lock:
            return [a for a in self._apps.values() if a.status == AppStatus.PLANNED]

    def set_app_status(self, app_id: str, new_status: AppStatus) -> bool:
        """
        Update the status of an application and persist to registry file.
        Requires ADMIN permission.
        """
        with self._lock:
            app = self.get_app(app_id)
            if not app:
                return False
            app.status = new_status
            self._save_to_disk()
            return True

    def _save_to_disk(self) -> None:
        """Persist current registry state to disk."""
        try:
            self._registry_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": "1.0.0",
                "updated_at": str(os.path.getmtime(self._registry_path) if self._registry_path.exists() else 0),
                "catalog": [app.model_dump() for app in self._apps.values()],
            }
            with open(self._registry_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            logger.info("Saved %d applications to %s", len(self._apps), self._registry_path)
        except Exception as e:
            logger.error("Failed to persist registry to %s: %s", self._registry_path, e)


# Global singleton instance
app_registry = ApplicationRegistry()
