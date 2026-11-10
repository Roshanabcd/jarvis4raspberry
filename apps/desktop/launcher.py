#!/usr/bin/env python3
"""
JARVIS OS — Standalone Desktop Application Launcher.
Transforms the web-based JARVIS into a proper, standalone Linux desktop application.

Features:
- Single-instance enforcement (activates existing window if already open)
- Automated backend health inspection and background lifecycle management
- Standalone dedicated application window (no Chrome tabs, URL bar, or browser chrome)
- Custom window title, geometry (1360x768), and desktop icon integration
- Graceful shutdown handling and process cleanup
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
DESKTOP_PROFILE_DIR = CONFIG_DIR / "desktop-profile"
ICON_PATH = PROJECT_ROOT / "apps" / "dashboard" / "static" / "jarvis_icon.png"

BACKEND_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/health"


class SingleInstanceLock:
    """File-descriptor based single instance lock."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._fp = None

    def acquire(self) -> bool:
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


def start_backend_service() -> bool:
    """Launch JARVIS FastAPI backend in background and wait for readiness."""
    logger.info("Starting JARVIS OS backend service...")
    cmd = [
        PYTHON_BIN,
        "-m",
        "uvicorn",
        "apps.core.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
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


def activate_existing_window() -> bool:
    """Use xdotool to locate and bring existing JARVIS OS window to the front."""
    try:
        search_cmd = ["xdotool", "search", "--class", "jarvis-os"]
        result = subprocess.run(search_cmd, capture_output=True, text=True, check=False)
        wids = result.stdout.strip().split()
        if wids:
            wid = wids[-1]
            subprocess.run(["xdotool", "windowactivate", wid], check=False)
            logger.info("Focused existing JARVIS OS desktop window (WID: %s)", wid)
            return True
    except Exception as e:
        logger.debug("xdotool activation error: %s", e)
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
    return proc


def stop_all_services():
    """Terminate running desktop window and background backend if requested."""
    logger.info("Stopping JARVIS OS application and services...")
    # Kill desktop window if running
    try:
        subprocess.run(["pkill", "-f", "class=jarvis-os"], check=False)
    except Exception:
        pass

    # Read backend PID
    if BACKEND_PID_FILE.exists():
        try:
            pid = int(BACKEND_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info("Terminated backend process PID: %d", pid)
            BACKEND_PID_FILE.unlink(missing_ok=True)
        except Exception as e:
            logger.debug("Backend kill error: %s", e)


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
        locked = LOCK_FILE.exists()
        print(json.dumps({
            "status": "running" if (healthy and locked) else ("backend_only" if healthy else "stopped"),
            "backend_healthy": healthy,
            "window_open": locked,
            "backend_url": BACKEND_URL,
        }, indent=2))
        sys.exit(0)

    # 1. Single-instance check
    lock = SingleInstanceLock(LOCK_FILE)
    if not lock.acquire():
        logger.info("Another instance of JARVIS OS is already running.")
        if activate_existing_window():
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
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Wait for the desktop window to close
        win_proc.wait()
        logger.info("JARVIS OS desktop window closed by user.")

    finally:
        lock.release()


if __name__ == "__main__":
    main()
