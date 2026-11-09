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


def get_uptime_seconds() -> float:
    """Read Linux system uptime in seconds from /proc/uptime with fallback."""
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.readline().split()[0])
    except Exception:
        return float(time.time() - psutil.boot_time())


def format_uptime(uptime_s: float) -> str:
    """Format uptime into human-readable days, hours, minutes, seconds."""
    total_sec = max(0, int(uptime_s))
    days = total_sec // 86400
    hours = (total_sec % 86400) // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0 or days > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    return ", ".join(parts)


def get_robot_state() -> str:
    """Determine explicit robot operational state: CONNECTED, DISCONNECTED, SIMULATION, UNKNOWN."""
    try:
        from tools.robotics.controller import robot
        if getattr(robot, "simulated", True):
            return "SIMULATION"
        elif getattr(robot, "is_connected", False) or getattr(robot, "armed", False):
            return "CONNECTED"
        return "DISCONNECTED"
    except Exception:
        return "UNKNOWN"


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
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    net  = psutil.net_io_counters()
    temp = get_cpu_temp()
    uptime_s = get_uptime_seconds()
    uptime_str = format_uptime(uptime_s)
    robot_state = get_robot_state()

    ram_total_gb = round(mem.total / (1024**3), 2)
    ram_used_gb = round(mem.used / (1024**3), 2)
    ram_avail_gb = round(mem.available / (1024**3), 2)
    swap_total_gb = round(swap.total / (1024**3), 2)
    swap_used_gb = round(swap.used / (1024**3), 2)

    ram_total_mb = int(mem.total // (1024 * 1024))
    ram_used_mb = int(mem.used // (1024 * 1024))
    disk_total_gb = round(disk.total / (1024**3), 1)
    disk_used_gb = round(disk.used / (1024**3), 1)
    disk_free_gb = round(disk.free / (1024**3), 1)

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "hostname": platform.node(),
        "uptime_s": round(uptime_s, 1),
        "uptime_str": uptime_str,
        "cpu_usage_pct": psutil.cpu_percent(interval=0.1),
        "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "cpu_cores": psutil.cpu_count(logical=False),
        "temp_c": temp,
        "cpu_temp_c": temp if temp is not None else 0.0,
        "ram_total_gb": ram_total_gb,
        "ram_used_gb": ram_used_gb,
        "ram_avail_gb": ram_avail_gb,
        "ram_pct": round(mem.percent, 1),
        "ram_total_mb": ram_total_mb,
        "ram_used_mb": ram_used_mb,
        "memory_total_mb": ram_total_mb,
        "memory_used_mb": ram_used_mb,
        "memory_pct": round(mem.percent, 1),
        "swap_total_gb": swap_total_gb,
        "swap_used_gb": swap_used_gb,
        "swap_total_mb": int(swap.total // (1024 * 1024)),
        "disk_total_gb": disk_total_gb,
        "disk_used_gb": disk_used_gb,
        "disk_free_gb": disk_free_gb,
        "disk_pct": round(disk.percent, 1),
        "disk_used_percent": round(disk.percent, 1),
        "net_sent_mb": round(net.bytes_sent / (1024 * 1024), 1),
        "net_recv_mb": round(net.bytes_recv / (1024 * 1024), 1),
        "robot_state": robot_state,
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
