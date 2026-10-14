"""
JARVIS OS - System Diagnostics
Runs comprehensive diagnostic checks across system runtime, hardware buses,
storage, networking, configuration, and database accessibility.
"""

import datetime
import logging
import os
import sqlite3
import subprocess
import sys
from typing import Any, Dict

import psutil

from config.config_manager import config
from hardware.raspberry_pi.health_monitor import HealthMonitor

logger = logging.getLogger("JARVIS.Hardware.Diagnostics")


class Diagnostics:
    """
    Executes full system diagnostics for Raspberry Pi 5 under JARVIS OS.
    Returns structured pass/fail reports per subsystem.
    """

    def __init__(self) -> None:
        self.health_monitor = HealthMonitor()

    def check_python_version(self) -> Dict[str, Any]:
        """Checks if Python runtime satisfies version requirement >= 3.11."""
        version_info = sys.version_info
        current_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        passed = version_info >= (3, 11)
        return {
            "passed": passed,
            "details": f"Python {current_str} (>= 3.11 required)",
        }

    def check_node_version(self) -> Dict[str, Any]:
        """Checks if Node.js runtime is installed via subprocess node --version."""
        sim_mode = bool(config.get("simulation_mode", True))
        try:
            res = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0:
                node_ver = res.stdout.strip()
                return {
                    "passed": True,
                    "details": f"Node.js {node_ver}",
                }
            else:
                if sim_mode:
                    return {
                        "passed": True,
                        "details": "Node.js not detected (simulated: passed)",
                    }
                return {
                    "passed": False,
                    "details": f"node --version exited with code {res.returncode}",
                }
        except FileNotFoundError:
            if sim_mode:
                return {
                    "passed": True,
                    "details": "Node.js not in PATH (simulated: passed)",
                }
            return {
                "passed": False,
                "details": "Node.js not installed in PATH",
            }
        except Exception as exc:
            logger.error("Error checking node version: %s", exc)
            if sim_mode:
                return {
                    "passed": True,
                    "details": f"Node check error: {exc} (simulated: passed)",
                }
            return {
                "passed": False,
                "details": f"Error running node --version: {exc}",
            }

    def check_storage(self) -> Dict[str, Any]:
        """Checks root filesystem storage capacity and availability."""
        try:
            usage = psutil.disk_usage("/")
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            # Require at least 500MB free and usage under 95%
            passed = free_gb >= 0.5 and usage.percent < 95.0
            return {
                "passed": passed,
                "details": f"{free_gb:.1f} GB free of {total_gb:.1f} GB ({usage.percent}% used)",
            }
        except Exception as exc:
            logger.error("Error checking storage: %s", exc)
            return {
                "passed": False,
                "details": f"Failed to check storage: {exc}",
            }

    def check_network(self) -> Dict[str, Any]:
        """Checks network connectivity and interface readiness."""
        net = self.health_monitor.check_network()
        passed = net["status"] == "OK"
        interfaces_str = ", ".join(net.get("interfaces", []))
        return {
            "passed": passed,
            "details": f"Status: {net['status']} (interfaces: {interfaces_str or 'none'})",
        }

    def check_i2c(self) -> Dict[str, Any]:
        """Checks I2C bus availability and detected peripherals."""
        i2c_res = self.health_monitor.check_i2c()
        passed = i2c_res["status"] in ("OK", "WARNING")
        devices_str = ", ".join(i2c_res.get("devices", []))
        return {
            "passed": passed,
            "details": f"Status: {i2c_res['status']} (devices: {devices_str or 'none'})",
        }

    def check_serial(self) -> Dict[str, Any]:
        """Checks UART/USB serial ports."""
        serial_res = self.health_monitor.check_serial()
        passed = serial_res["status"] in ("OK", "WARNING")
        ports_str = ", ".join(serial_res.get("ports", []))
        return {
            "passed": passed,
            "details": f"Status: {serial_res['status']} (ports: {ports_str or 'none'})",
        }

    def check_simulation_mode(self) -> Dict[str, Any]:
        """Validates current simulation mode state."""
        sim_mode = bool(config.get("simulation_mode", True))
        return {
            "passed": True,
            "details": f"Simulation mode is {'ENABLED' if sim_mode else 'DISABLED'}",
        }

    def check_db_accessible(self) -> Dict[str, Any]:
        """Validates SQLite database accessibility and table integrity."""
        # Locate database path from config, environment, or relative project path
        configured_path = (
            config.get("memory", {}).get("db_path")
            or os.environ.get("JARVIS_DB_PATH")
            or "jarvis_memory.db"
        )

        db_path = configured_path
        if not os.path.isabs(db_path):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            candidate = os.path.join(project_root, db_path)
            if os.path.exists(candidate) or not os.path.exists(db_path):
                db_path = candidate

        try:
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT 1;")
            conn.close()

            passed = True
            tables_str = ", ".join(tables) if tables else "none (empty db)"
            return {
                "passed": passed,
                "details": f"SQLite accessible at {db_path} (tables: {tables_str})",
            }
        except Exception as exc:
            logger.error("Error accessing SQLite database at %s: %s", db_path, exc)
            return {
                "passed": False,
                "details": f"Database error at {db_path}: {exc}",
            }

    def check_config_loaded(self) -> Dict[str, Any]:
        """Validates that configuration files were successfully loaded."""
        loaded_keys = list(config.config.keys())
        passed = len(loaded_keys) > 0
        return {
            "passed": passed,
            "details": f"Loaded {len(loaded_keys)} configuration keys from {config.config_dir}",
        }

    def run_full_diagnostics(self) -> Dict[str, Any]:
        """
        Runs all diagnostic checks and returns structured report.
        Checks: python_version, node_version, storage, network, i2c, serial,
        simulation_mode, db_accessible, config_loaded.
        """
        checks: Dict[str, Dict[str, Any]] = {
            "python_version": self.check_python_version(),
            "node_version": self.check_node_version(),
            "storage": self.check_storage(),
            "network": self.check_network(),
            "i2c": self.check_i2c(),
            "serial": self.check_serial(),
            "simulation_mode": self.check_simulation_mode(),
            "db_accessible": self.check_db_accessible(),
            "config_loaded": self.check_config_loaded(),
        }

        all_passed = all(check["passed"] for check in checks.values())

        return {
            "all_passed": all_passed,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checks": checks,
        }
