"""Core Screen Guardian Coordinator tying capture, OCR, vision, error detection, notifications, voice, and auto-repair."""

from __future__ import annotations

import asyncio
import base64
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from modules.module_43_autonomous_screen_guardian.backend.adapters.coding_agents import discover_cli_agents
from modules.module_43_autonomous_screen_guardian.backend.adapters.vision_providers import VisionCoordinator
from modules.module_43_autonomous_screen_guardian.backend.adapters.voice_adapter import VoiceCommandAdapter
from modules.module_43_autonomous_screen_guardian.backend.app.config import ScreenGuardianConfig
from modules.module_43_autonomous_screen_guardian.backend.models.database import ScreenGuardianDB, utc_now_iso
from modules.module_43_autonomous_screen_guardian.backend.services.error_detector import ErrorDetectionEngine
from modules.module_43_autonomous_screen_guardian.backend.services.ocr_engine import LocalOCREngine
from modules.module_43_autonomous_screen_guardian.backend.services.repair_engine import AutoRepairEngine
from modules.module_43_autonomous_screen_guardian.backend.services.screen_capture import ScreenCaptureService
from modules.module_43_autonomous_screen_guardian.backend.services.system_telemetry import collect_system_telemetry


class ScreenGuardianService:
    adapter_name: str = "jarvis_screen_guardian_engine"
    is_simulated: bool = False

    def __init__(
        self,
        config: Optional[ScreenGuardianConfig] = None,
        db: Optional[ScreenGuardianDB] = None,
        frame_provider: Optional[Callable[[str], Tuple[bytes, str]]] = None,
    ) -> None:
        self.config = config or ScreenGuardianConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or ScreenGuardianDB(self.config.db_path)
        self.capture = ScreenCaptureService(config=self.config, frame_provider=frame_provider)
        self.ocr = LocalOCREngine()
        self.vision = VisionCoordinator(config=self.config)
        self.detector = ErrorDetectionEngine()
        self.repair = AutoRepairEngine(config=self.config, db=self.db)
        self.voice = VoiceCommandAdapter(db=self.db)
        self.disabled_alert_categories: Set[str] = set()
        self._started_at = time.monotonic()
        self._ws_subscribers: Set[asyncio.Queue[Dict[str, Any]]] = set()
        self.latest_vision_analysis: Optional[Dict[str, Any]] = None

        saved = self.db.load_settings()
        if saved:
            self._apply_settings_dict(saved)

    def subscribe_ws(self) -> asyncio.Queue[Dict[str, Any]]:
        q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._ws_subscribers.add(q)
        return q

    def unsubscribe_ws(self, q: asyncio.Queue[Dict[str, Any]]) -> None:
        self._ws_subscribers.discard(q)

    def _broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        msg = {"event_type": event_type, "timestamp": utc_now_iso(), "data": data}
        for q in list(self._ws_subscribers):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass

    def _apply_settings_dict(self, data: Dict[str, Any]) -> None:
        if "capture_interval_sec" in data and data["capture_interval_sec"] is not None:
            self.config.capture_interval_sec = float(data["capture_interval_sec"])
            self.capture.interval_sec = self.config.capture_interval_sec
        if "vision_provider" in data and data["vision_provider"]:
            self.config.vision_provider = str(data["vision_provider"])
        if "allow_remote_vision_upload" in data and data["allow_remote_vision_upload"] is not None:
            self.config.allow_remote_vision_upload = bool(data["allow_remote_vision_upload"])
        if "performance_mode" in data and data["performance_mode"]:
            self.config.performance_mode = str(data["performance_mode"])
        if "disabled_alert_categories" in data and data["disabled_alert_categories"] is not None:
            self.disabled_alert_categories = {str(c).lower() for c in data["disabled_alert_categories"]}
        if "excluded_windows" in data and data["excluded_windows"] is not None:
            self.capture.excluded_windows = list(data["excluded_windows"])
        if "trusted_workspaces" in data and data["trusted_workspaces"] is not None:
            self.config.trusted_workspaces = [str(Path(p).expanduser().resolve()) for p in data["trusted_workspaces"] if p.strip()]

    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_settings()
        for k, v in updates.items():
            if v is not None:
                current[k] = v
        self._apply_settings_dict(current)
        self.db.save_settings(current)
        self.db.add_log("settings.updated", "Updated Screen Guardian settings")
        return self.get_settings()

    def get_settings(self) -> Dict[str, Any]:
        return {
            "capture_interval_sec": self.config.capture_interval_sec,
            "vision_provider": self.config.vision_provider,
            "allow_remote_vision_upload": self.config.allow_remote_vision_upload,
            "store_raw_screenshots": self.config.store_raw_screenshots,
            "auto_start_on_boot": self.config.auto_start_on_boot,
            "performance_mode": self.config.performance_mode,
            "disabled_alert_categories": sorted(self.disabled_alert_categories),
            "excluded_windows": self.capture.excluded_windows,
            "trusted_workspaces": self.config.trusted_workspaces,
        }

    async def analyze_frame(
        self,
        image_base64: Optional[str] = None,
        ocr_text_override: Optional[str] = None,
        source_app: str = "Unknown Application",
        window_title: str = "",
        use_vision_model: bool = False,
        require_active_session: bool = False,
    ) -> Dict[str, Any]:
        raw_png: Optional[bytes] = base64.b64decode(image_base64) if image_base64 else None
        frame_meta: Optional[Dict[str, Any]] = None
        ocr_res: Dict[str, Any] = {"engine": "text_input", "available": True, "text": ocr_text_override or "", "confidence": None, "boxes": []}

        if raw_png is not None or (ocr_text_override is None):
            frame = self.capture.capture_frame(
                raw_png_override=raw_png,
                source_app=source_app,
                window_title=window_title,
                require_active_session=require_active_session,
            )
            frame_meta = frame.to_metadata(include_preview_b64=False)
            if frame.changed or ocr_text_override is None:
                ocr_res = self.ocr.extract_text(frame.png_bytes)
                if ocr_text_override:
                    ocr_res["text"] = ocr_text_override
            frame_hash = frame.sha256
        else:
            frame_hash = f"txt_{uuid.uuid4().hex[:10]}"

        text = ocr_res.get("text", "")
        if text:
            self.db.add_ocr_entry(frame_hash, source_app, ocr_res["engine"], text, ocr_res.get("confidence"))

        vision_res = await self.vision.analyze(raw_png, text, source_app, use_remote=use_vision_model)
        self.latest_vision_analysis = vision_res

        detection = self.detector.analyze_text(text, source_app=source_app)
        if detection["prompt_injection_detected"]:
            self.db.add_log(
                "security.prompt_injection_blocked",
                "Detected untrusted command-like text on screen; treated strictly as data.",
                level="WARNING",
                details={"matches": detection["injection_warnings"]},
            )

        persisted_errors: List[Dict[str, Any]] = []
        created_notifications: List[Dict[str, Any]] = []
        for err_data in detection["errors"]:
            err_row, is_new = self.db.upsert_error(err_data)
            persisted_errors.append(err_row)
            if is_new and not err_row["ignored"] and err_row["category"] not in self.disabled_alert_categories:
                notif = self.db.add_notification(
                    {
                        "notification_id": f"ntf_{uuid.uuid4().hex[:10]}",
                        "error_id": err_row["error_id"],
                        "category": err_row["category"],
                        "severity": err_row["severity"],
                        "title": f"JARVIS detected a possible {err_row['title']}",
                        "application": source_app,
                        "details": err_row["likely_cause"],
                        "suggested_action": err_row["suggested_action"],
                    }
                )
                created_notifications.append(notif)
                self._broadcast("error.detected", {"error": err_row, "notification": notif})

        return {
            "frame": frame_meta,
            "ocr": ocr_res,
            "vision": vision_res,
            "errors": persisted_errors,
            "notifications_created": created_notifications,
            "prompt_injection_detected": detection["prompt_injection_detected"],
            "injection_warnings": detection["injection_warnings"],
        }

    def handle_notification_action(self, notification_id: str, action: str) -> Dict[str, Any]:
        notif = self.db.get_notification(notification_id)
        if not notif:
            raise KeyError(f"Notification '{notification_id}' not found.")
        act = action.strip().lower()
        if act == "dismiss":
            updated = self.db.update_notification_status(notification_id, "dismissed")
            return {"action": act, "notification": updated}
        if act == "ignore_similar":
            updated = self.db.update_notification_status(notification_id, "ignored")
            if notif.get("error_id"):
                self.db.update_error(notif["error_id"], ignored=1)
            return {"action": act, "notification": updated}
        if act in {"view", "explain", "prepare_fix"}:
            updated = self.db.update_notification_status(notification_id, "acknowledged")
            err = self.db.get_error(notif["error_id"]) if notif.get("error_id") else None
            return {"action": act, "notification": updated, "error": err}
        raise ValueError(f"Unsupported notification action '{action}'.")

    def get_status(self) -> Dict[str, Any]:
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "monitoring": self.capture.get_status(),
            "ocr_available": self.ocr.is_available,
            "ocr_engine": "tesseract_local" if self.ocr.is_available else "tesseract_unavailable",
            "coding_agents": discover_cli_agents(),
            "active_errors": len([e for e in self.db.list_errors(limit=200) if e["status"] in {"new", "ongoing"}]),
            "unread_notifications": len([n for n in self.db.list_notifications(limit=200) if n["status"] == "unread"]),
            "total_repairs": len(self.db.list_repairs(limit=200)),
            "telemetry": collect_system_telemetry(),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
