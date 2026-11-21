"""IoT Hardware Bridge Adapter contract for Module 30 — Smart Home Controller."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class SmartHomeBridgeAdapter(ABC):
    adapter_name: str = "abstract_smart_home_bridge"
    is_simulated: bool = True

    @abstractmethod
    def dispatch(self, device: Dict[str, Any], command: str, value: Any = None) -> Dict[str, Any]:
        """Apply a command to a device and return the updated state dict."""


class SimulatedSmartHomeBridgeAdapter(SmartHomeBridgeAdapter):
    """Safe local IoT simulator (does not control physical hardware unless replaced)."""

    adapter_name = "simulated_iot_home_bridge"
    is_simulated = True

    def dispatch(self, device: Dict[str, Any], command: str, value: Any = None) -> Dict[str, Any]:
        state = dict(device["state"])
        if command == "turn_on":
            state["power"] = "on"
        elif command == "turn_off":
            state["power"] = "off"
        elif command == "set_brightness":
            pct = max(0, min(100, int(value if value is not None else 100)))
            state["brightness"] = pct
            state["power"] = "on" if pct > 0 else "off"
        elif command == "set_temp":
            state["target_temp_c"] = round(float(value if value is not None else 22.0), 1)
            state["power"] = "on"
        elif command == "lock":
            state["locked"] = True
        elif command == "unlock":
            state["locked"] = False
        elif command == "update_reading" and isinstance(value, dict):
            state.update(value)
        return state
