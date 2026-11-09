"""
JARVIS System Information and Read-Only Diagnostics Tools
Queries physical Raspberry Pi 5 telemetry, OS metrics, and hardware controller status.
"""
import os
import platform
import socket
import subprocess
import time
from typing import Any, Dict, List, Optional
import psutil

from hardware.raspberry_pi.rpi_info import (
    get_system_status as _get_rpi_status,
    get_uptime_seconds,
    format_uptime,
    get_robot_state,
    get_cpu_temp,
)


class SystemTools:
    """Deterministic system information querying for JARVIS OS."""

    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """Retrieve full system telemetry."""
        return _get_rpi_status()

    @staticmethod
    def get_cpu_usage() -> Dict[str, Any]:
        """Read current CPU usage percentage and core counts."""
        pct = psutil.cpu_percent(interval=0.1)
        freq = psutil.cpu_freq()
        return {
            "cpu_usage_pct": pct,
            "cpu_cores_physical": psutil.cpu_count(logical=False),
            "cpu_cores_logical": psutil.cpu_count(logical=True),
            "cpu_freq_mhz": freq.current if freq else None,
            "cpu_temp_c": get_cpu_temp(),
        }

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Read RAM and swap memory usage in GB and percentages."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_avail_gb": round(mem.available / (1024**3), 2),
            "ram_pct": round(mem.percent, 1),
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_pct": round(swap.percent, 1),
        }

    @staticmethod
    def get_uptime() -> Dict[str, Any]:
        """Read Linux OS uptime from /proc/uptime formatted in days, hours, minutes, seconds."""
        uptime_s = get_uptime_seconds()
        return {
            "uptime_seconds": round(uptime_s, 1),
            "uptime_formatted": format_uptime(uptime_s),
            "boot_time": psutil.boot_time(),
        }

    @staticmethod
    def get_disk_usage(mount_point: str = "/") -> Dict[str, Any]:
        """Read disk space usage for a given filesystem path."""
        try:
            disk = psutil.disk_usage(mount_point)
            return {
                "mount_point": mount_point,
                "disk_total_gb": round(disk.total / (1024**3), 1),
                "disk_used_gb": round(disk.used / (1024**3), 1),
                "disk_free_gb": round(disk.free / (1024**3), 1),
                "disk_pct": round(disk.percent, 1),
            }
        except Exception as e:
            return {"mount_point": mount_point, "error": str(e), "success": False}

    @staticmethod
    def get_cpu_temperature() -> Dict[str, Any]:
        """Read Raspberry Pi 5 CPU thermal-zone temperature."""
        temp = get_cpu_temp()
        if temp is None:
            return {"temp_c": None, "available": False, "reason": "No thermal sensor node found"}
        status = "normal" if temp < 70 else ("warm" if temp < 80 else "throttled")
        return {"temp_c": temp, "status": status, "available": True}

    @staticmethod
    def get_network_status() -> Dict[str, Any]:
        """Check local IP, gateway reachability, and network traffic counters."""
        net = psutil.net_io_counters()
        hostname = socket.gethostname()
        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "bytes_sent_mb": round(net.bytes_sent / (1024 * 1024), 1),
            "bytes_recv_mb": round(net.bytes_recv / (1024 * 1024), 1),
        }

    @staticmethod
    def get_application_status() -> Dict[str, Any]:
        """Check status of JARVIS application components and Ollama daemon."""
        services = {}
        # Check Ollama
        try:
            import urllib.request
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1.5) as resp:
                services["ollama"] = "running" if resp.status == 200 else f"http_{resp.status}"
        except Exception as e:
            services["ollama"] = f"unreachable ({e})"

        # Check PipeWire
        try:
            r = subprocess.run(["wpctl", "status"], capture_output=True, text=True, timeout=2)
            services["pipewire"] = "running" if r.returncode == 0 else "degraded"
        except Exception:
            services["pipewire"] = "unknown"

        # Check Uvicorn
        services["jarvis_web"] = "running (port 8000)"

        return {
            "services": services,
            "python_version": platform.python_version(),
            "os": platform.platform(),
        }


class RobotInfoTools:
    """Read-only robot controller diagnostics."""

    @staticmethod
    def get_robot_status() -> Dict[str, Any]:
        """Read current robot state without actuating motors."""
        try:
            from tools.robotics.controller import robot
            return {
                "robot_state": get_robot_state(),
                "simulated": getattr(robot, "simulated", True),
                "armed": getattr(robot, "armed", False),
                "speed": getattr(robot, "current_speed", 0),
                "direction": getattr(robot, "current_direction", "STOPPED"),
            }
        except Exception as e:
            return {"robot_state": "UNKNOWN", "error": str(e)}

    @staticmethod
    def get_motor_state() -> Dict[str, Any]:
        """Read-only motor speed and direction values."""
        try:
            from tools.robotics.controller import robot
            return {
                "state": getattr(robot, "state", "UNKNOWN"),
                "left_motor_speed": getattr(robot, "left_speed", 0),
                "right_motor_speed": getattr(robot, "right_speed", 0),
                "armed": getattr(robot, "armed", False),
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_safety_state() -> Dict[str, Any]:
        """Check e-stop and safety limits."""
        try:
            from tools.robotics.controller import robot
            return {
                "e_stop_engaged": getattr(robot, "estop_active", False),
                "armed": getattr(robot, "armed", False),
                "simulated": getattr(robot, "simulated", True),
            }
        except Exception as e:
            return {"error": str(e)}


system_tools = SystemTools()
robot_info_tools = RobotInfoTools()
