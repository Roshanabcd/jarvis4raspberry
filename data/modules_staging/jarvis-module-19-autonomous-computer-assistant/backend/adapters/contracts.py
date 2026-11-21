"""Versioned JARVIS Common Module Contract (v1.0.0) & Desktop Automation Adapter ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

CONTRACT_VERSION = "1.0.0"
EventCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]


class DesktopAutomationAdapter(ABC):
    """Permitted desktop adapter contract.

    Default implementation is SafeDemoDesktopAdapter (virtual desktop only).
    A real OS adapter (e.g., X11/Wayland/xdotool/pynput) must explicitly implement
    this contract and never run during automated tests.
    """

    adapter_name: str = "abstract"
    is_simulated: bool = True

    @abstractmethod
    def discover_applications(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def list_windows(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def select_window(self, window_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def launch_application(self, app_id: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def capture_screenshot(self, window_id: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def mouse_move(self, x: int, y: int) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def mouse_click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def keyboard_type(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def keyboard_hotkey(self, keys: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_state_snapshot(self) -> Dict[str, Any]:
        raise NotImplementedError
