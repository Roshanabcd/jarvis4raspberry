"""
JARVIS System Information & Health for Raspberry Pi 5
"""
import os
import time
import socket
import platform
import subprocess
import logging
from typing import Dict, Any, List

import psutil

logger = logging.getLogger("JARVIS.HW.RPi")


def _run(cmd: list) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return ""


def get_cpu_temp() -> float | None:
    """Read CPU temperature from Pi thermal zone."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        temps = psutil.sensors_temperatures()
        if "cpu_thermal" in temps:
            return round(temps["cpu_thermal"][0].current, 1)
        return None


def get_system_status() -> Dict[str, Any]:
    mem  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net  = psutil.net_io_counters()
    temp = get_cpu_temp()

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "hostname": platform.node(),
        "uptime_s": round(time.time() - psutil.boot_time(), 0),
        "cpu_usage_pct": psutil.cpu_percent(interval=0.5),
        "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "cpu_cores": psutil.cpu_count(logical=False),
        "temp_c": temp,
        "ram_total_mb": mem.total // (1024 * 1024),
        "ram_used_mb": mem.used  // (1024 * 1024),
        "ram_pct": mem.percent,
        "swap_total_mb": psutil.swap_memory().total // (1024 * 1024),
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "disk_used_gb":  round(disk.used  / (1024**3), 1),
        "disk_pct": disk.percent,
        "net_sent_mb": round(net.bytes_sent  / (1024 * 1024), 1),
        "net_recv_mb": round(net.bytes_recv  / (1024 * 1024), 1),
        "timestamp": time.time(),
    }


def list_i2c_devices() -> List[str]:
    """Return detected I2C bus device nodes."""
    buses = []
    for entry in os.scandir("/dev"):
        if entry.name.startswith("i2c-"):
            buses.append(entry.path)
    return sorted(buses)


def scan_i2c_bus(bus: int = 1) -> List[str]:
    """
    Run i2cdetect to find connected devices.
    Returns list of hex addresses found.
    """
    raw = _run(["i2cdetect", "-y", str(bus)])
    addresses = []
    for line in raw.splitlines():
        parts = line.split(":")[1:]
        if parts:
            for token in parts[0].split():
                if token != "--":
                    addresses.append(f"0x{token}")
    return addresses


def list_serial_ports() -> List[str]:
    ports = []
    patterns = ["/dev/ttyUSB", "/dev/ttyACM", "/dev/ttyAMA", "/dev/ttyS"]
    for entry in os.scandir("/dev"):
        for pat in patterns:
            if entry.path.startswith(pat):
                ports.append(entry.path)
    return sorted(set(ports))


def is_online(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False
