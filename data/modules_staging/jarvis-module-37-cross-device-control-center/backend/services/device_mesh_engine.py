"""Cross-Device Control Center Mesh Engine (Module 37 — simulated remote bridge)."""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.app.config import DeviceMeshConfig
from backend.models.database import DeviceMeshDB, utc_now_iso

ALLOWED_CAPABILITIES = {"clipboard", "media", "notifications", "lock", "power", "display"}


class DeviceMeshError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DeviceMeshEngine:
    adapter_name: str = "simulated_mesh_device_bridge"
    is_simulated: bool = True

    def __init__(self, config: Optional[DeviceMeshConfig] = None, db: Optional[DeviceMeshDB] = None) -> None:
        self.config = config or DeviceMeshConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or DeviceMeshDB(self.config.db_path)
        self._started_at = time.monotonic()

    def register_device(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        caps = sorted({c.strip().lower() for c in payload.get("capabilities", []) if c.strip()})
        invalid = [c for c in caps if c not in ALLOWED_CAPABILITIES]
        if invalid:
            raise DeviceMeshError(
                "UNSUPPORTED_CAPABILITY",
                f"Unsupported capability(ies): {', '.join(invalid)}.",
                422,
            )
        now = utc_now_iso()
        item = {
            "device_id": f"dev_{uuid.uuid4().hex[:10]}",
            "name": payload["name"].strip(),
            "device_type": payload.get("device_type", "laptop").strip().lower(),
            "platform": payload.get("platform", "linux").strip().lower(),
            "capabilities": caps,
            "battery_pct": int(payload.get("battery_pct", 100)),
            "online": bool(payload.get("online", True)),
            "last_seen_at": now,
            "created_at": now,
        }
        return self.db.add_device(item)

    def heartbeat(self, device_id: str, online: bool, battery_pct: Optional[int] = None) -> Dict[str, Any]:
        existing = self.db.get_device(device_id)
        if not existing:
            raise DeviceMeshError("DEVICE_NOT_FOUND", f"Device '{device_id}' not found.", 404)
        updated = self.db.update_device_heartbeat(device_id, online=online, battery_pct=battery_pct, last_seen_at=utc_now_iso())
        assert updated is not None
        return updated

    def dispatch_command(self, device_id: str, capability: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        dev = self.db.get_device(device_id)
        if not dev:
            raise DeviceMeshError("DEVICE_NOT_FOUND", f"Device '{device_id}' not found.", 404)
        if not dev["online"]:
            raise DeviceMeshError("DEVICE_OFFLINE", f"Device '{dev['name']}' ({device_id}) is currently offline.", 409)
        cap = capability.strip().lower()
        if cap not in dev["capabilities"]:
            raise DeviceMeshError(
                "CAPABILITY_NOT_SUPPORTED",
                f"Device '{dev['name']}' does not expose capability '{cap}'.",
                422,
            )

        record = {
            "command_id": f"cmd_{uuid.uuid4().hex[:10]}",
            "device_id": device_id,
            "capability": cap,
            "action": action.strip(),
            "params": params or {},
            "status": "executed",
            "result": {
                "ack": True,
                "device_name": dev["name"],
                "message": f"[SIMULATED] Executed {cap}.{action.strip()} on {dev['name']}",
            },
            "simulated": self.is_simulated,
            "created_at": utc_now_iso(),
        }
        return self.db.add_command(record)

    def sync_clipboard(self, source_device_id: str, content: str, mime_type: str = "text/plain") -> Dict[str, Any]:
        dev = self.db.get_device(source_device_id)
        if not dev:
            raise DeviceMeshError("DEVICE_NOT_FOUND", f"Source device '{source_device_id}' not found.", 404)
        if "clipboard" not in dev["capabilities"]:
            raise DeviceMeshError(
                "CAPABILITY_NOT_SUPPORTED",
                f"Device '{dev['name']}' does not support clipboard sync.",
                422,
            )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        entry = {
            "entry_id": f"clip_{uuid.uuid4().hex[:10]}",
            "source_device_id": source_device_id,
            "mime_type": mime_type.strip(),
            "content": content,
            "sha256": digest,
            "created_at": utc_now_iso(),
        }
        return self.db.add_clipboard(entry)

    def get_status(self) -> Dict[str, Any]:
        devices = self.db.list_devices()
        online_count = sum(1 for d in devices if d["online"])
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "devices_count": len(devices),
            "online_devices_count": online_count,
            "commands_count": len(self.db.list_commands(limit=500)),
            "clipboard_entries_count": len(self.db.list_clipboard(limit=500)),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
