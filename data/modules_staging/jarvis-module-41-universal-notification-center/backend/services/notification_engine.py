"""Local Universal Notification Hub Engine (Module 41)."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from backend.app.config import NotificationConfig
from backend.models.database import NotificationDB, utc_now_iso

VALID_PRIORITIES = {"low", "normal", "high", "critical"}
ALLOWED_CHANNELS = {"hud", "desktop", "voice", "email", "webhook"}


class NotificationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotificationEngine:
    adapter_name: str = "local_notification_hub_engine"
    is_simulated: bool = False

    def __init__(self, config: Optional[NotificationConfig] = None, db: Optional[NotificationDB] = None) -> None:
        self.config = config or NotificationConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or NotificationDB(self.config.db_path)
        self._started_at = time.monotonic()

    def update_preferences(
        self, dnd_enabled: bool, allow_critical_during_dnd: bool, enabled_channels: List[str]
    ) -> Dict[str, Any]:
        cleaned = sorted({c.strip().lower() for c in enabled_channels if c.strip()})
        bad = [c for c in cleaned if c not in ALLOWED_CHANNELS]
        if bad:
            raise NotificationError("UNSUPPORTED_CHANNEL", f"Unsupported channel(s): {', '.join(bad)}.", 422)
        return self.db.update_preferences(
            dnd_enabled=dnd_enabled,
            allow_critical_during_dnd=allow_critical_during_dnd,
            enabled_channels=cleaned,
            now=utc_now_iso(),
        )

    def send_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        priority = payload.get("priority", "normal").strip().lower()
        if priority not in VALID_PRIORITIES:
            raise NotificationError("INVALID_PRIORITY", f"Invalid priority '{priority}'.", 422)

        channels = sorted({c.strip().lower() for c in payload.get("channels", ["hud"]) if c.strip()})
        bad = [c for c in channels if c not in ALLOWED_CHANNELS]
        if bad:
            raise NotificationError("UNSUPPORTED_CHANNEL", f"Unsupported channel(s): {', '.join(bad)}.", 422)

        dedupe_key = payload.get("dedupe_key")
        if dedupe_key:
            dedupe_key = dedupe_key.strip()
            existing = self.db.get_by_dedupe_key(dedupe_key)
            if existing:
                out = dict(existing)
                out["deduplicated"] = True
                return out

        prefs = self.db.get_preferences()
        enabled_set = set(prefs["enabled_channels"])
        suppressed = prefs["dnd_enabled"] and not (priority == "critical" and prefs["allow_critical_during_dnd"])

        if suppressed:
            delivered_channels: List[str] = []
            status = "suppressed"
        else:
            delivered_channels = [c for c in channels if c in enabled_set]
            status = "unread"

        now = utc_now_iso()
        item = self.db.add_notification(
            {
                "notification_id": f"ntf_{uuid.uuid4().hex[:10]}",
                "source_module": payload["source_module"].strip(),
                "title": payload["title"].strip(),
                "message": payload["message"].strip(),
                "priority": priority,
                "channels": channels,
                "delivered_channels": delivered_channels,
                "dedupe_key": dedupe_key,
                "metadata": payload.get("metadata") or {},
                "status": status,
                "created_at": now,
                "updated_at": now,
            }
        )
        out = dict(item)
        out["deduplicated"] = False
        return out

    def acknowledge(self, notification_id: str) -> Dict[str, Any]:
        existing = self.db.get_notification(notification_id)
        if not existing:
            raise NotificationError("NOTIFICATION_NOT_FOUND", f"Notification '{notification_id}' not found.", 404)
        updated = self.db.update_status(notification_id, "acknowledged", utc_now_iso())
        assert updated is not None
        return updated

    def dismiss(self, notification_id: str) -> Dict[str, Any]:
        existing = self.db.get_notification(notification_id)
        if not existing:
            raise NotificationError("NOTIFICATION_NOT_FOUND", f"Notification '{notification_id}' not found.", 404)
        updated = self.db.update_status(notification_id, "dismissed", utc_now_iso())
        assert updated is not None
        return updated

    def get_status(self) -> Dict[str, Any]:
        items = self.db.list_notifications(limit=500)
        prefs = self.db.get_preferences()
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "total_count": len(items),
            "unread_count": sum(1 for i in items if i["status"] == "unread"),
            "suppressed_count": sum(1 for i in items if i["status"] == "suppressed"),
            "dnd_enabled": prefs["dnd_enabled"],
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
