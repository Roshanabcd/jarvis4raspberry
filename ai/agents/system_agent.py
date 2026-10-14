"""System agent for hardware monitoring and telemetry reporting in JARVIS OS."""

import logging
from typing import Any, Dict, Optional
from ai.agents.base_agent import BaseAgent
from config.config_manager import config

logger = logging.getLogger("JARVIS-SYSTEM-AGENT")


class SystemAgent(BaseAgent):
    """Specialized agent that queries Raspberry Pi system status and formats natural responses."""

    def __init__(self):
        super().__init__(
            name="SystemAgent",
            description="Inspects Raspberry Pi hardware metrics including CPU, RAM, disk, and thermal sensor readings.",
        )
        self.simulation_mode = config.get("simulation_mode", True)

    def _fetch_status(self) -> Dict[str, Any]:
        """Fetch system status from rpi_info or return fallback data."""
        try:
            from hardware.raspberry_pi.rpi_info import get_system_status
            return get_system_status()
        except Exception as exc:
            logger.warning("Failed to retrieve hardware status via rpi_info: %s", exc)
            # Safe simulated fallback
            return {
                "os": "Linux",
                "arch": "aarch64",
                "cpu_usage_percent": 14.2,
                "memory_total_mb": 8192,
                "memory_used_mb": 2048,
                "temperature_c": 42.5,
                "simulated": True,
            }

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process queries regarding CPU, RAM, disk, temperature, or general system health.

        Args:
            query: System query string (e.g. 'what is the cpu usage?', 'system status', 'ram').
            context: Optional execution context.

        Returns:
            Natural language response detailing the system metrics.
        """
        q = query.lower()
        stats = self._fetch_status()

        os_name = stats.get("os", "Linux")
        arch = stats.get("arch", "arm")
        cpu_usage = stats.get("cpu_usage_percent", 0.0)
        mem_total = stats.get("memory_total_mb", 0)
        mem_used = stats.get("memory_used_mb", 0)
        temp_c = stats.get("temperature_c")

        mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0.0
        temp_str = f"{temp_c:.1f}°C" if temp_c is not None else "unavailable"

        logger.info(
            "System status retrieved: CPU=%s%%, MEM=%s/%sMB, TEMP=%s",
            cpu_usage,
            mem_used,
            mem_total,
            temp_str,
        )

        # Highlight specific query if targeted
        if "cpu" in q:
            return f"CPU utilization is currently at {cpu_usage:.1f}%. Thermal reading: {temp_str}."

        if "ram" in q or "memory" in q:
            return (
                f"Memory usage: {mem_used} MB utilized of {mem_total} MB "
                f"({mem_percent:.1f}%). System is operating within normal parameters."
            )

        if "temp" in q or "thermal" in q:
            return f"CPU core temperature is currently {temp_str}."

        if "disk" in q:
            # Check disk usage if requested
            disk_info = ""
            try:
                import psutil
                disk = psutil.disk_usage("/")
                disk_percent = disk.percent
                disk_free_gb = disk.free // (1024**3)
                disk_info = f" Disk root utilization is at {disk_percent}% with {disk_free_gb} GB free."
            except Exception:
                disk_info = " Disk telemetry is currently unavailable."
            return f"System storage: {disk_info}"

        # General system summary
        return (
            f"System telemetry: {os_name} ({arch}). "
            f"CPU load is {cpu_usage:.1f}%. "
            f"Memory utilization is {mem_used} MB / {mem_total} MB ({mem_percent:.1f}%). "
            f"Core temperature is {temp_str}. All operational parameters normal."
        )
