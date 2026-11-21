"""Real local Linux/POSIX host telemetry & localhost TCP probe adapter (simulated=False)."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class HostProbeAdapter(ABC):
    adapter_name: str = "abstract_host_probe"
    is_simulated: bool = False

    @abstractmethod
    def collect_metrics(self, disk_path: str = "/") -> Dict[str, Any]:
        """Collect current host metrics."""

    @abstractmethod
    def probe_tcp(self, host: str, port: int, timeout_s: float = 0.5) -> Tuple[str, Optional[float]]:
        """Probe TCP reachability and return (status, latency_ms)."""


class LocalLinuxHostProbe(HostProbeAdapter):
    adapter_name: str = "local_linux_host_probe"
    is_simulated: bool = False

    def _read_meminfo(self) -> Dict[str, float]:
        meminfo = Path("/proc/meminfo")
        if not meminfo.is_file():
            return {"memory_total_mb": 0.0, "memory_available_mb": 0.0, "memory_used_pct": 0.0}
        vals: Dict[str, int] = {}
        for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                num = parts[1].strip().split()[0]
                if num.isdigit():
                    vals[key] = int(num)
        total_kb = vals.get("MemTotal", 0)
        avail_kb = vals.get("MemAvailable", vals.get("MemFree", 0))
        used_pct = round(((total_kb - avail_kb) / total_kb) * 100.0, 2) if total_kb > 0 else 0.0
        return {
            "memory_total_mb": round(total_kb / 1024.0, 1),
            "memory_available_mb": round(avail_kb / 1024.0, 1),
            "memory_used_pct": used_pct,
        }

    def _read_cpu_temp(self) -> Optional[float]:
        for tz in (
            Path("/sys/class/thermal/thermal_zone0/temp"),
            Path("/sys/class/hwmon/hwmon0/temp1_input"),
        ):
            if tz.is_file():
                try:
                    raw = tz.read_text(encoding="utf-8").strip()
                    val = float(raw)
                    return round(val / 1000.0 if val > 200 else val, 1)
                except (OSError, ValueError):
                    continue
        return None

    def _read_uptime_s(self) -> float:
        up = Path("/proc/uptime")
        if up.is_file():
            try:
                return round(float(up.read_text(encoding="utf-8").split()[0]), 1)
            except (OSError, ValueError, IndexError):
                pass
        return 0.0

    def collect_metrics(self, disk_path: str = "/") -> Dict[str, Any]:
        try:
            l1, l5, l15 = os.getloadavg()
        except (OSError, AttributeError):
            l1, l5, l15 = 0.0, 0.0, 0.0

        disk = shutil.disk_usage(disk_path if Path(disk_path).exists() else "/")
        disk_used_pct = round((disk.used / disk.total) * 100.0, 2) if disk.total > 0 else 0.0
        mem = self._read_meminfo()

        return {
            "hostname": socket.gethostname(),
            "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count() or 1,
            "load_1m": round(l1, 3),
            "load_5m": round(l5, 3),
            "load_15m": round(l15, 3),
            "memory_total_mb": mem["memory_total_mb"],
            "memory_available_mb": mem["memory_available_mb"],
            "memory_used_pct": mem["memory_used_pct"],
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "disk_used_pct": disk_used_pct,
            "cpu_temp_c": self._read_cpu_temp(),
            "host_uptime_seconds": self._read_uptime_s(),
        }

    def probe_tcp(self, host: str, port: int, timeout_s: float = 0.5) -> Tuple[str, Optional[float]]:
        t0 = time.monotonic()
        try:
            with socket.create_connection((host, port), timeout=timeout_s):
                latency = round((time.monotonic() - t0) * 1000.0, 2)
                return ("up", latency)
        except OSError:
            return ("down", None)
