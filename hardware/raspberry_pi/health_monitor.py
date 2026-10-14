"""
JARVIS OS - Raspberry Pi Hardware Health Monitor
Monitors CPU, RAM, Temperature, Disk, I2C, Serial, Audio, and Network components.
Supports simulation-safe fallback modes and configurable thresholds.
"""

import glob
import logging
import os
import re
import socket
import subprocess
import time
from typing import Any, Dict, List, Optional

import psutil

from config.config_manager import config

logger = logging.getLogger("JARVIS.Hardware.HealthMonitor")


class HealthStatus:
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"


class HealthMonitor:
    """
    Monitors hardware health metrics for Raspberry Pi 5 under JARVIS OS.
    Retrieves thresholds from configuration with simulation-safe fallbacks.
    """

    def __init__(self) -> None:
        self.simulation_mode: bool = bool(config.get("simulation_mode", True))
        self._load_thresholds()

    def _load_thresholds(self) -> None:
        """Loads health metric thresholds from config."""
        thresholds: Dict[str, Any] = config.get("health_thresholds", {}) or {}
        health_cfg: Dict[str, Any] = config.get("health", {}) or {}
        self.cpu_warning: float = float(thresholds.get("cpu_warning", health_cfg.get("cpu_warn_pct", 75.0)))
        self.cpu_error: float = float(thresholds.get("cpu_error", 90.0))
        self.ram_warning: float = float(thresholds.get("ram_warning", 80.0))
        self.ram_error: float = float(thresholds.get("ram_error", 95.0))
        self.temp_warning: float = float(thresholds.get("temp_warning", health_cfg.get("temp_warn_c", 70.0)))
        self.temp_error: float = float(thresholds.get("temp_error", 85.0))
        self.disk_warning: float = float(thresholds.get("disk_warning", health_cfg.get("disk_warn_pct", 80.0)))
        self.disk_error: float = float(thresholds.get("disk_error", 90.0))

    def check_cpu(self) -> Dict[str, Any]:
        """Checks CPU utilization percentage."""
        try:
            val = float(psutil.cpu_percent(interval=0.1))
            if val >= self.cpu_error:
                status = HealthStatus.ERROR
            elif val >= self.cpu_warning:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.OK
            return {"status": status, "value": round(val, 1)}
        except Exception as exc:
            logger.error("Failed to check CPU health: %s", exc)
            return {"status": HealthStatus.ERROR, "value": 0.0}

    def check_ram(self) -> Dict[str, Any]:
        """Checks RAM memory utilization percentage."""
        try:
            mem = psutil.virtual_memory()
            val = float(mem.percent)
            if val >= self.ram_error:
                status = HealthStatus.ERROR
            elif val >= self.ram_warning:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.OK
            return {"status": status, "value": round(val, 1)}
        except Exception as exc:
            logger.error("Failed to check RAM health: %s", exc)
            return {"status": HealthStatus.ERROR, "value": 0.0}

    def check_temp(self) -> Dict[str, Any]:
        """Checks CPU core temperature in degrees Celsius."""
        temp: Optional[float] = None

        # 1. Try psutil sensors_temperatures
        try:
            if hasattr(psutil, "sensors_temperatures"):
                sensors = psutil.sensors_temperatures()
                for key in ("cpu_thermal", "coretemp", "k10temp", "acpitz"):
                    if key in sensors and sensors[key]:
                        temp = float(sensors[key][0].current)
                        break
        except Exception:
            pass

        # 2. Try sysfs thermal zone on Linux / Raspberry Pi
        if temp is None:
            zone_path = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(zone_path):
                try:
                    with open(zone_path, "r", encoding="utf-8") as f:
                        raw_val = f.read().strip()
                        if raw_val.isdigit():
                            temp = float(raw_val) / 1000.0
                except Exception:
                    pass

        # 3. Try vcgencmd measure_temp on Raspberry Pi OS
        if temp is None:
            try:
                res = subprocess.run(
                    ["vcgencmd", "measure_temp"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if res.returncode == 0:
                    match = re.search(r"temp=([\d\.]+)'C", res.stdout)
                    if match:
                        temp = float(match.group(1))
            except Exception:
                pass

        # 4. Simulation fallback
        if temp is None and self.simulation_mode:
            temp = 42.5

        if temp is None:
            return {"status": HealthStatus.OFFLINE, "value": None}

        if temp >= self.temp_error:
            status = HealthStatus.ERROR
        elif temp >= self.temp_warning:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.OK

        return {"status": status, "value": round(temp, 1)}

    def check_disk(self) -> Dict[str, Any]:
        """Checks root filesystem disk usage percentage."""
        try:
            disk = psutil.disk_usage("/")
            val = float(disk.percent)
            if val >= self.disk_error:
                status = HealthStatus.ERROR
            elif val >= self.disk_warning:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.OK
            return {"status": status, "value_pct": round(val, 1)}
        except Exception as exc:
            logger.error("Failed to check Disk health: %s", exc)
            return {"status": HealthStatus.ERROR, "value_pct": 0.0}

    def check_i2c(self) -> Dict[str, Any]:
        """
        Lists /dev/i2c-* buses and scans for devices using i2cdetect -y 1.
        Returns devices list and health status.
        """
        i2c_nodes = glob.glob("/dev/i2c-*")
        devices: List[str] = []

        # If running in simulation mode and no physical I2C nodes exist
        if self.simulation_mode and not i2c_nodes:
            logger.debug("I2C check running in simulation mode (mocking devices)")
            return {
                "status": HealthStatus.OK,
                "devices": ["0x40", "0x70"],  # Common PCA9685/TB6612 addresses
            }

        if not i2c_nodes:
            return {
                "status": HealthStatus.OFFLINE,
                "devices": [],
            }

        # Try scanning bus 1 (Raspberry Pi default) or the first available bus
        bus_number = "1"
        if "/dev/i2c-1" not in i2c_nodes and i2c_nodes:
            match = re.search(r"\d+", i2c_nodes[0])
            if match:
                bus_number = match.group(0)

        try:
            res = subprocess.run(
                ["i2cdetect", "-y", bus_number],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0:
                lines = res.stdout.strip().splitlines()
                for line in lines[1:]:  # skip header
                    parts = line.split(":")
                    if len(parts) == 2:
                        for item in parts[1].split():
                            item = item.strip()
                            if item not in ("--", "UU", "") and re.match(r"^[0-9a-fA-F]{2}$", item):
                                devices.append(f"0x{item.lower()}")
                            elif item == "UU":
                                devices.append(f"0x{parts[0].strip()[:1]}0-UU")

                return {
                    "status": HealthStatus.OK,
                    "devices": devices,
                }
            else:
                if self.simulation_mode:
                    return {
                        "status": HealthStatus.OK,
                        "devices": ["0x40", "0x70"],
                    }
                return {
                    "status": HealthStatus.ERROR,
                    "devices": [],
                }
        except FileNotFoundError:
            if self.simulation_mode:
                return {
                    "status": HealthStatus.OK,
                    "devices": ["0x40", "0x70"],
                }
            return {
                "status": HealthStatus.WARNING,
                "devices": [],
            }
        except Exception as exc:
            logger.error("Error executing i2cdetect: %s", exc)
            if self.simulation_mode:
                return {
                    "status": HealthStatus.OK,
                    "devices": ["0x40", "0x70"],
                }
            return {
                "status": HealthStatus.ERROR,
                "devices": [],
            }

    def check_serial(self) -> Dict[str, Any]:
        """
        Lists serial ports matching /dev/ttyUSB*, /dev/ttyACM*, /dev/ttyAMA*.
        Returns active ports list and health status.
        """
        patterns = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyAMA*"]
        ports: List[str] = []
        for pat in patterns:
            ports.extend(sorted(glob.glob(pat)))

        if not ports and self.simulation_mode:
            logger.debug("Serial check running in simulation mode (mocking port)")
            return {
                "status": HealthStatus.OK,
                "ports": ["/dev/ttyAMA0 (simulated)"],
            }

        if not ports:
            return {
                "status": HealthStatus.OFFLINE,
                "ports": [],
            }

        return {
            "status": HealthStatus.OK,
            "ports": ports,
        }

    def check_audio(self) -> Dict[str, Any]:
        """Checks audio output/input subsystem availability."""
        has_sound_card = False
        asound_path = "/proc/asound/cards"
        if os.path.exists(asound_path):
            try:
                with open(asound_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content and "--- no soundcards ---" not in content:
                        has_sound_card = True
            except Exception:
                pass

        if not has_sound_card:
            try:
                res = subprocess.run(
                    ["aplay", "-l"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if res.returncode == 0 and "card" in res.stdout:
                    has_sound_card = True
            except Exception:
                pass

        if has_sound_card or self.simulation_mode:
            return {"status": HealthStatus.OK}

        return {"status": HealthStatus.OFFLINE}

    def check_network(self) -> Dict[str, Any]:
        """
        Checks network connectivity by testing socket connection to 8.8.8.8:53.
        Collects active network interfaces.
        """
        interfaces: List[str] = []

        try:
            if hasattr(psutil, "net_if_addrs"):
                interfaces = list(psutil.net_if_addrs().keys())
            elif os.path.exists("/sys/class/net"):
                interfaces = os.listdir("/sys/class/net")
        except Exception:
            pass

        non_lo = [i for i in interfaces if i != "lo"]
        display_interfaces = non_lo if non_lo else interfaces

        connected = False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.5)
            s.connect(("8.8.8.8", 53))
            s.close()
            connected = True
        except Exception:
            connected = False

        if connected:
            return {
                "status": HealthStatus.OK,
                "interfaces": display_interfaces,
            }

        if self.simulation_mode:
            return {
                "status": HealthStatus.OK,
                "interfaces": display_interfaces or ["eth0", "wlan0"],
            }

        return {
            "status": HealthStatus.OFFLINE,
            "interfaces": display_interfaces,
        }

    def check_all(self) -> Dict[str, Any]:
        """
        Runs all hardware health checks and returns a comprehensive health status dict.
        Health states: 'OK', 'WARNING', 'ERROR', 'OFFLINE'.
        """
        self._load_thresholds()
        self.simulation_mode = bool(config.get("simulation_mode", True))

        cpu = self.check_cpu()
        ram = self.check_ram()
        temp = self.check_temp()
        disk = self.check_disk()
        i2c = self.check_i2c()
        serial = self.check_serial()
        audio = self.check_audio()
        network = self.check_network()

        statuses = [
            cpu["status"],
            ram["status"],
            temp["status"],
            disk["status"],
            i2c["status"],
            serial["status"],
            audio["status"],
            network["status"],
        ]

        if HealthStatus.ERROR in statuses:
            overall = HealthStatus.ERROR
        elif HealthStatus.WARNING in statuses:
            overall = HealthStatus.WARNING
        elif HealthStatus.OFFLINE in statuses:
            overall = HealthStatus.WARNING
        else:
            overall = HealthStatus.OK

        return {
            "status": overall,
            "timestamp": time.time(),
            "cpu": cpu,
            "ram": ram,
            "temp": temp,
            "disk": disk,
            "i2c": i2c,
            "serial": serial,
            "audio": audio,
            "network": network,
        }
