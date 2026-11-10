#!/usr/bin/env python3
"""
JARVIS OS — Standalone Desktop Application Launcher.
Transforms the web-based JARVIS into a proper, standalone Linux desktop application.

Features:
- Single-instance enforcement (activates existing window if already open)
- Automated backend health inspection and background lifecycle management
- Strict localhost binding enforcement (127.0.0.1:8000)
- Standalone dedicated application window (no Chrome tabs, URL bar, or browser chrome)
- Custom window title, geometry (1360x768), and desktop icon integration
- Graceful shutdown handling, stale lock recovery, and process cleanup
"""

import argparse
import fcntl
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [JARVIS-LAUNCHER] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("JARVIS-LAUNCHER")

# Directories and paths
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "jarvis-os"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PYTHON_BIN = sys.executable or "/home/roshan/miniconda3/bin/python3"
LOCK_FILE = CONFIG_DIR / "desktop_app.lock"
BACKEND_PID_FILE = CONFIG_DIR / "backend.pid"
WINDOW_PID_FILE = CONFIG_DIR / "desktop_window.pid"
DESKTOP_PROFILE_DIR = CONFIG_DIR / "desktop-profile"
ICON_PATH = PROJECT_ROOT / "apps" / "dashboard" / "static" / "jarvis_icon.png"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/health"


class SingleInstanceLock:
    """File-descriptor based single instance lock with automatic stale lock recovery."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._fp = None

    def acquire(self) -> bool:
        # Check and recover stale lock file from dead process
        if self.lock_path.exists():
            try:
                content = self.lock_path.read_text().strip()
                if content.isdigit():
                    pid = int(content)
                    try:
                        os.kill(pid, 0)
                        # Process exists and is alive
                    except ProcessLookupError:
                        logger.info("Found stale lock file for non-existent PID %d; removing.", pid)
                        self.lock_path.unlink(missing_ok=True)
                    except PermissionError:
                        pass
            except Exception as e:
                logger.debug("Error checking lock file PID: %s", e)

        try:
            self._fp = open(self.lock_path, "w")
            fcntl.flock(self._fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._fp.write(str(os.getpid()))
            self._fp.flush()
            return True
        except (IOError, BlockingIOError):
            return False

    def release(self):
        if self._fp:
            try:
                fcntl.flock(self._fp, fcntl.LOCK_UN)
                self._fp.close()
                if self.lock_path.exists():
                    self.lock_path.unlink()
            except Exception:
                pass


def is_backend_healthy() -> bool:
    """Ping JARVIS OS backend health endpoint."""
    try:
        resp = requests.get(HEALTH_ENDPOINT, timeout=1.5)
        return resp.status_code == 200
    except Exception:
        return False


def is_systemd_voice_service_active() -> bool:
    """Check if jarvis-voice systemd user service is running."""
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", "jarvis-voice.service"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )
        return res.stdout.strip() == "active"
    except Exception:
        return False


def is_window_open() -> bool:
    """Check if the JARVIS OS standalone desktop window is currently open on X11."""
    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0"

    try:
        # 1. Search xdotool by class
        res = subprocess.run(
            ["xdotool", "search", "--class", "jarvis-os"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if res.stdout.strip():
            return True

        # 2. Search xdotool by name
        res = subprocess.run(
            ["xdotool", "search", "--name", "JARVIS OS"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if res.stdout.strip():
            return True

        # 3. Search wmctrl
        res = subprocess.run(
            ["wmctrl", "-lx"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        for line in res.stdout.splitlines():
            line_lower = line.lower()
            if "jarvis-os" in line_lower or "jarvis os" in line_lower:
                return True

        # 4. Check process list for Chrome with --class=jarvis-os
        res = subprocess.run(
            ["pgrep", "-f", "google-chrome.*class=jarvis-os"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.stdout.strip():
            return True
    except Exception as e:
        logger.debug("Window check error: %s", e)
    return False


def activate_existing_window() -> bool:
    """Use xdotool or wmctrl to locate and bring existing JARVIS OS window to the front."""
    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":0"

    try:
        # Search xdotool by class
        search_cmd = ["xdotool", "search", "--class", "jarvis-os"]
        result = subprocess.run(search_cmd, capture_output=True, text=True, env=env, check=False)
        wids = result.stdout.strip().split()

        if not wids:
            # Fallback search by title
            search_cmd = ["xdotool", "search", "--name", "JARVIS OS"]
            result = subprocess.run(search_cmd, capture_output=True, text=True, env=env, check=False)
            wids = result.stdout.strip().split()

        if wids:
            wid = wids[-1]
            subprocess.run(["xdotool", "windowactivate", wid], env=env, check=False)
            logger.info("Focused existing JARVIS OS desktop window (WID: %s)", wid)
            return True

        # Fallback to wmctrl
        res = subprocess.run(["wmctrl", "-lx"], capture_output=True, text=True, env=env, check=False)
        for line in res.stdout.splitlines():
            line_lower = line.lower()
            if "jarvis-os" in line_lower or "jarvis os" in line_lower:
                parts = line.split()
                if parts:
                    subprocess.run(["wmctrl", "-i", "-a", parts[0]], env=env, check=False)
                    logger.info("Focused existing JARVIS OS desktop window via wmctrl (WID: %s)", parts[0])
                    return True
    except Exception as e:
        logger.debug("xdotool / wmctrl activation error: %s", e)
    return False


def start_backend_service() -> bool:
    """Launch JARVIS FastAPI backend bound strictly to 127.0.0.1:8000 in background and wait for readiness."""
    logger.info("Starting JARVIS OS backend service (host=%s, port=%d)...", BACKEND_HOST, BACKEND_PORT)
    cmd = [
        PYTHON_BIN,
        "-m",
        "uvicorn",
        "apps.core.main:app",
        "--host",
        BACKEND_HOST,
        "--port",
        str(BACKEND_PORT),
        "--log-level",
        "info",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["DISPLAY"] = env.get("DISPLAY", ":0")

    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Save PID
    BACKEND_PID_FILE.write_text(str(proc.pid))
    logger.info("Spawned backend with PID: %d. Awaiting health check...", proc.pid)

    # Poll until ready (max 15 seconds)
    start_time = time.time()
    while time.time() - start_time < 15.0:
        if is_backend_healthy():
            logger.info("✓ Backend service verified healthy at %s", BACKEND_URL)
            return True
        time.sleep(0.5)

    logger.warning("Backend service did not respond within 15 seconds.")
    return False


def launch_desktop_window():
    """Launch standalone desktop application window."""
    chrome_bin = (
        subprocess.check_output(["which", "google-chrome"]).decode().strip()
        if subprocess.run(["which", "google-chrome"], capture_output=True).returncode == 0
        else "google-chrome"
    )

    app_url = f"{BACKEND_URL}/"
    app_args = [
        chrome_bin,
        f"--app={app_url}",
        "--class=jarvis-os",
        "--name=jarvis-os",
        f"--user-data-dir={DESKTOP_PROFILE_DIR}",
        "--window-size=1360,768",
        "--window-position=0,0",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--disable-extensions",
        "--password-store=basic",
        "--enable-features=WebRTCPipeWireCapturer",
        "--autoplay-policy=no-user-gesture-required",
    ]

    logger.info("Launching JARVIS OS desktop application window...")
    logger.info("Window Geometry: 1360x768 | Class: jarvis-os | Backend: %s", app_url)

    env = os.environ.copy()
    env["DISPLAY"] = env.get("DISPLAY", ":0")

    proc = subprocess.Popen(app_args, env=env)
    WINDOW_PID_FILE.write_text(str(proc.pid))
    return proc


def stop_all_services():
    """Terminate running desktop window and background backend if requested."""
    logger.info("Stopping JARVIS OS application and services...")
    # Kill desktop window if running
    try:
        subprocess.run(["pkill", "-f", "class=jarvis-os"], check=False)
    except Exception:
        pass

    if WINDOW_PID_FILE.exists():
        try:
            wpid = int(WINDOW_PID_FILE.read_text().strip())
            os.kill(wpid, signal.SIGTERM)
        except Exception:
            pass
        WINDOW_PID_FILE.unlink(missing_ok=True)

    # Read backend PID
    if BACKEND_PID_FILE.exists():
        try:
            pid = int(BACKEND_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info("Terminated backend process PID: %d", pid)
            BACKEND_PID_FILE.unlink(missing_ok=True)
        except Exception as e:
            logger.debug("Backend kill error: %s", e)

    # Clean lock file
    LOCK_FILE.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="JARVIS OS Desktop Application Launcher")
    parser.add_argument("--stop", action="store_true", help="Stop JARVIS OS desktop and backend")
    parser.add_argument("--status", action="store_true", help="Check JARVIS OS desktop status")
    parser.add_argument("--backend-only", action="store_true", help="Start backend service only")
    args = parser.parse_args()

    if args.stop:
        stop_all_services()
        sys.exit(0)

    if args.status:
        healthy = is_backend_healthy()
        win_open = is_window_open()
        voice_active = is_systemd_voice_service_active()
        status_str = "running" if (healthy and win_open) else ("backend_only" if healthy else "stopped")

        print(json.dumps({
            "status": status_str,
            "backend_healthy": healthy,
            "window_open": win_open,
            "backend_url": BACKEND_URL,
            "backend_binding": f"{BACKEND_HOST}:{BACKEND_PORT}",
            "voice_service_active": voice_active,
        }, indent=2))
        sys.exit(0)

    # 1. Single-instance check
    lock = SingleInstanceLock(LOCK_FILE)
    if not lock.acquire():
        logger.info("Another instance of JARVIS OS is already running or holding lock.")
        if activate_existing_window():
            logger.info("Brought existing JARVIS OS window to focus.")
            sys.exit(0)
        else:
            logger.info("Existing window not found via xdotool; proceeding with launch.")

    try:
        # 2. Ensure backend is running
        if not is_backend_healthy():
            if not start_backend_service():
                logger.error("Failed to start JARVIS OS backend service. Aborting.")
                sys.exit(1)
        else:
            logger.info("✓ Backend service already active at %s", BACKEND_URL)

        if args.backend_only:
            logger.info("Backend running in standalone mode.")
            return

        # 3. Launch standalone desktop window
        win_proc = launch_desktop_window()

        def signal_handler(sig, frame):
            logger.info("Signal %s received; closing desktop window...", sig)
            try:
                win_proc.terminate()
            except Exception:
                pass
            lock.release()
            WINDOW_PID_FILE.unlink(missing_ok=True)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Wait for the desktop window to close
        win_proc.wait()
        logger.info("JARVIS OS desktop window closed by user.")

    finally:
        lock.release()
        WINDOW_PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
