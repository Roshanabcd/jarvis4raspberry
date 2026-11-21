"""Lightweight Linux/ARM64 System Telemetry Collector (zero psutil requirement)."""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path
from typing import Any, Dict


def collect_system_telemetry() -> Dict[str, Any]:
    load_1, load_5, load_15 = (0.0, 0.0, 0.0)
    try:
        load_1, load_5, load_15 = os.getloadavg()
    except Exception:
        pass

    mem_total_mb = 0.0
    mem_avail_mb = 0.0
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("MemTotal:"):
                mem_total_mb = round(int(line.split()[1]) / 1024.0, 1)
            elif line.startswith("MemAvailable:"):
                mem_avail_mb = round(int(line.split()[1]) / 1024.0, 1)

    mem_used_pct = round(((mem_total_mb - mem_avail_mb) / mem_total_mb) * 100.0, 1) if mem_total_mb > 0 else 0.0

    disk = shutil.disk_usage("/")
    disk_total_gb = round(disk.total / (1024 ** 3), 2)
    disk_free_gb = round(disk.free / (1024 ** 3), 2)
    disk_used_pct = round((disk.used / max(1, disk.total)) * 100.0, 1)

    net_rx_mb = 0.0
    net_tx_mb = 0.0
    netdev = Path("/proc/net/dev")
    if netdev.is_file():
        for line in netdev.read_text(encoding="utf-8", errors="ignore").splitlines()[2:]:
            parts = line.split(":")
            if len(parts) == 2 and parts[0].strip() != "lo":
                nums = parts[1].split()
                if len(nums) >= 9:
                    net_rx_mb += int(nums[0]) / (1024 * 1024)
                    net_tx_mb += int(nums[8]) / (1024 * 1024)

    return {
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "load_avg": {"1m": round(load_1, 2), "5m": round(load_5, 2), "15m": round(load_15, 2)},
        "memory": {
            "total_mb": mem_total_mb,
            "available_mb": mem_avail_mb,
            "used_pct": mem_used_pct,
        },
        "disk": {
            "total_gb": disk_total_gb,
            "free_gb": disk_free_gb,
            "used_pct": disk_used_pct,
        },
        "network": {
            "rx_mb": round(net_rx_mb, 2),
            "tx_mb": round(net_tx_mb, 2),
        },
    }
