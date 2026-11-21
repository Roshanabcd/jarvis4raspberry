"""Local Plugin & Skills Marketplace Registry Engine (Module 38)."""

from __future__ import annotations

import hashlib
import re
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.app.config import MarketplaceConfig
from backend.models.database import MarketplaceDB, utc_now_iso

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")
ALLOWED_PERMISSIONS = {
    "read_files",
    "write_files",
    "network_read",
    "calendar_read",
    "notifications",
    "workflows",
    "telemetry_read",
}


class MarketplaceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class MarketplaceEngine:
    adapter_name: str = "local_plugin_registry_engine"
    is_simulated: bool = False

    def __init__(self, config: Optional[MarketplaceConfig] = None, db: Optional[MarketplaceDB] = None) -> None:
        self.config = config or MarketplaceConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or MarketplaceDB(self.config.db_path)
        self._started_at = time.monotonic()

    def _audit(self, package_id: str, action: str, details: str) -> None:
        self.db.add_audit(
            {
                "event_id": f"evt_{uuid.uuid4().hex[:10]}",
                "package_id": package_id,
                "action": action,
                "details": details,
                "created_at": utc_now_iso(),
            }
        )

    def publish_package(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        slug = payload["slug"].strip().lower()
        if not SLUG_RE.match(slug):
            raise MarketplaceError("INVALID_SLUG", f"Slug '{slug}' must be lowercase alphanumeric/hyphen/underscore.", 422)
        version = payload["version"].strip()
        if not SEMVER_RE.match(version):
            raise MarketplaceError("INVALID_SEMVER", f"Version '{version}' must follow MAJOR.MINOR.PATCH.", 422)
        if self.db.get_by_slug_version(slug, version):
            raise MarketplaceError("PACKAGE_ALREADY_EXISTS", f"Package {slug}@{version} already exists.", 409)

        perms = sorted({p.strip().lower() for p in payload.get("permissions", []) if p.strip()})
        bad_perms = [p for p in perms if p not in ALLOWED_PERMISSIONS]
        if bad_perms:
            raise MarketplaceError("DISALLOWED_PERMISSION", f"Disallowed permission(s): {', '.join(bad_perms)}.", 422)

        manifest_payload = str(payload.get("manifest_payload", "{}"))
        digest = hashlib.sha256(f"{slug}@{version}|{manifest_payload}".encode("utf-8")).hexdigest()

        pkg = self.db.add_package(
            {
                "package_id": f"pkg_{uuid.uuid4().hex[:10]}",
                "slug": slug,
                "name": payload["name"].strip(),
                "version": version,
                "kind": payload.get("kind", "skill").strip().lower(),
                "author": payload.get("author", "Roshan Sharma").strip(),
                "description": payload.get("description", "").strip(),
                "permissions": perms,
                "sha256": digest,
                "created_at": utc_now_iso(),
            }
        )
        self._audit(pkg["package_id"], "publish", f"Published {slug}@{version}")
        return pkg

    def install_package(self, package_id: str, expected_sha256: Optional[str] = None, enabled: bool = True) -> Dict[str, Any]:
        pkg = self.db.get_package(package_id)
        if not pkg:
            raise MarketplaceError("PACKAGE_NOT_FOUND", f"Package '{package_id}' not found.", 404)
        if expected_sha256 and expected_sha256.strip().lower() != pkg["sha256"]:
            raise MarketplaceError(
                "CHECKSUM_MISMATCH",
                "Provided expected_sha256 does not match registered package digest.",
                422,
            )
        updated = self.db.upsert_installation(package_id, enabled=enabled, now=utc_now_iso())
        self._audit(package_id, "install", f"Installed {pkg['slug']}@{pkg['version']} (enabled={enabled})")
        return updated

    def toggle_package(self, package_id: str, enabled: bool) -> Dict[str, Any]:
        pkg = self.db.get_package(package_id)
        if not pkg:
            raise MarketplaceError("PACKAGE_NOT_FOUND", f"Package '{package_id}' not found.", 404)
        if not pkg["installed"]:
            raise MarketplaceError("PACKAGE_NOT_INSTALLED", f"Package '{package_id}' must be installed before toggling.", 409)
        updated = self.db.upsert_installation(package_id, enabled=enabled, now=utc_now_iso())
        self._audit(package_id, "toggle", f"Set enabled={enabled} for {pkg['slug']}@{pkg['version']}")
        return updated

    def uninstall_package(self, package_id: str) -> Dict[str, Any]:
        pkg = self.db.get_package(package_id)
        if not pkg:
            raise MarketplaceError("PACKAGE_NOT_FOUND", f"Package '{package_id}' not found.", 404)
        removed = self.db.remove_installation(package_id)
        if not removed:
            raise MarketplaceError("PACKAGE_NOT_INSTALLED", f"Package '{package_id}' is not installed.", 409)
        self._audit(package_id, "uninstall", f"Uninstalled {pkg['slug']}@{pkg['version']}")
        return self.db.get_package(package_id)  # type: ignore[return-value]

    def get_status(self) -> Dict[str, Any]:
        pkgs = self.db.list_packages()
        installed = sum(1 for p in pkgs if p["installed"])
        enabled = sum(1 for p in pkgs if p["enabled"])
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "packages_count": len(pkgs),
            "installed_count": installed,
            "enabled_count": enabled,
            "audit_events_count": len(self.db.list_audit(limit=500)),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
