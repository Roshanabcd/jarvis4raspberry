"""Smart Home Controller Engine (Module 30).

Provides:
- Room & device registry with typed default states
- Safe command dispatch (unlocking security locks requires explicit confirm_unlock=True)
- Multi-device scene definitions & atomic activation
- Threshold-based automation rules evaluation
- Room-level active energy wattage telemetry
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from backend.adapters.bridge_adapter import SimulatedSmartHomeBridgeAdapter, SmartHomeBridgeAdapter
from backend.app.config import SmartHomeConfig
from backend.models.database import SmartHomeDB, utc_now_iso


class SmartHomeError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _default_state(device_type: str, initial: Dict[str, Any]) -> Dict[str, Any]:
    defaults: Dict[str, Dict[str, Any]] = {
        "light": {"power": "off", "brightness": 80},
        "thermostat": {"power": "off", "target_temp_c": 23.0},
        "smart_plug": {"power": "off"},
        "lock": {"locked": True},
        "sensor": {"temp_c": 24.0, "humidity_pct": 50},
    }
    st = dict(defaults.get(device_type, {}))
    st.update(initial or {})
    return st


def _compare(lhs: float, op: str, rhs: float) -> bool:
    if op == ">":
        return lhs > rhs
    if op == ">=":
        return lhs >= rhs
    if op == "<":
        return lhs < rhs
    if op == "<=":
        return lhs <= rhs
    return lhs == rhs


class SmartHomeEngine:
    def __init__(
        self,
        config: Optional[SmartHomeConfig] = None,
        db: Optional[SmartHomeDB] = None,
        bridge: Optional[SmartHomeBridgeAdapter] = None,
    ) -> None:
        self.config = config or SmartHomeConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or SmartHomeDB(self.config.db_path)
        self.bridge = bridge or SimulatedSmartHomeBridgeAdapter()
        self._started_at = time.monotonic()

    def _require_device(self, device_id: str) -> Dict[str, Any]:
        dev = self.db.get_device(device_id)
        if not dev:
            raise SmartHomeError("DEVICE_NOT_FOUND", f"Device '{device_id}' not found.", 404)
        return dev

    def register_device(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        state = _default_state(payload["device_type"], payload.get("initial_state", {}))
        dev = self.db.create_device(
            {
                "device_id": f"dev_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "room": payload["room"].strip(),
                "device_type": payload["device_type"],
                "rated_watts": float(payload.get("rated_watts", 12.0)),
                "state": state,
                "created_at": now,
                "updated_at": now,
            }
        )
        self.db.add_event(f"evt_{uuid.uuid4().hex[:10]}", dev["device_id"], "register", f"Registered in {dev['room']}")
        return dev

    def send_command(self, device_id: str, command: str, value: Any = None, confirm_unlock: bool = False) -> Dict[str, Any]:
        dev = self._require_device(device_id)
        if command == "unlock" and not confirm_unlock:
            raise SmartHomeError(
                "UNLOCK_CONFIRMATION_REQUIRED",
                f"Unlocking '{dev['name']}' requires confirm_unlock=true.",
                409,
            )
        new_state = self.bridge.dispatch(dev, command, value=value)
        updated = self.db.update_device_state(device_id, new_state)
        self.db.add_event(f"evt_{uuid.uuid4().hex[:10]}", device_id, command, f"value={value} -> state={new_state}")
        return updated  # type: ignore[return-value]

    def create_scene(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        for act in payload["actions"]:
            self._require_device(act["device_id"])
        return self.db.create_scene(
            {
                "scene_id": f"scn_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "description": payload.get("description", "").strip(),
                "actions": payload["actions"],
                "created_at": utc_now_iso(),
            }
        )

    def activate_scene(self, scene_id: str) -> Dict[str, Any]:
        scene = self.db.get_scene(scene_id)
        if not scene:
            raise SmartHomeError("SCENE_NOT_FOUND", f"Scene '{scene_id}' not found.", 404)
        results = []
        for act in scene["actions"]:
            updated = self.send_command(act["device_id"], act["command"], value=act.get("value"))
            results.append(updated)
        return {"scene": scene["name"], "applied_count": len(results), "devices": results}

    def create_rule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._require_device(payload["sensor_device_id"])
        self._require_device(payload["target_device_id"])
        return self.db.create_rule(
            {
                "rule_id": f"rul_{uuid.uuid4().hex[:10]}",
                "name": payload["name"].strip(),
                "sensor_device_id": payload["sensor_device_id"],
                "metric_key": payload["metric_key"],
                "operator": payload["operator"],
                "threshold": float(payload["threshold"]),
                "target_device_id": payload["target_device_id"],
                "target_command": payload["target_command"],
                "target_value": payload.get("target_value"),
                "created_at": utc_now_iso(),
            }
        )

    def evaluate_rules(self) -> Dict[str, Any]:
        triggered: List[Dict[str, Any]] = []
        for rule in self.db.list_rules():
            sensor = self.db.get_device(rule["sensor_device_id"])
            if not sensor:
                continue
            val = sensor["state"].get(rule["metric_key"])
            if val is None:
                continue
            try:
                num = float(val)
            except (TypeError, ValueError):
                continue
            if _compare(num, rule["operator"], float(rule["threshold"])):
                updated = self.send_command(rule["target_device_id"], rule["target_command"], value=rule["target_value"])
                triggered.append({"rule_id": rule["rule_id"], "rule_name": rule["name"], "target_device": updated})
        return {"triggered_count": len(triggered), "triggered": triggered}

    def get_energy_summary(self) -> Dict[str, Any]:
        by_room: Dict[str, float] = {}
        total = 0.0
        for d in self.db.list_devices():
            active = d["state"].get("power") == "on"
            watts = float(d["rated_watts"]) if active else 0.0
            if active and d["device_type"] == "light":
                watts = round(watts * (float(d["state"].get("brightness", 100)) / 100.0), 2)
            by_room[d["room"]] = round(by_room.get(d["room"], 0.0) + watts, 2)
            total = round(total + watts, 2)
        return {"total_active_watts": total, "by_room": by_room}

    def get_status(self) -> Dict[str, Any]:
        devs = self.db.list_devices()
        energy = self.get_energy_summary()
        return {
            "adapter": self.bridge.adapter_name,
            "simulated": self.bridge.is_simulated,
            "devices_count": len(devs),
            "active_devices": sum(1 for d in devs if d["state"].get("power") == "on"),
            "scenes_count": len(self.db.list_scenes()),
            "rules_count": len(self.db.list_rules()),
            "total_active_watts": energy["total_active_watts"],
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
