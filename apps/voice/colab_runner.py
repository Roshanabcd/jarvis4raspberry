"""
JARVIS OS — Automatic Google Colab OmniVoice Runner & Dynamic Voice Integration.

Automatically launches and maintains the Google Colab session for:
Notebook: /home/roshan/Downloads/Super_Eleven_Lab_Lite_2_1.ipynb
Session: testColab (Tesla T4 GPU)

Monitors stdout/stderr in real-time, discovers public Gradio URLs,
automatically registers the live endpoint with JARVIS, and activates personal voice cloning.
"""

from __future__ import annotations

import collections
import logging
import os
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Deque, Dict, List, Optional

from core.paths import NOTEBOOKS_DIR, VOICE_SAMPLES_DIR

logger = logging.getLogger("JARVIS.Voice.ColabRunner")

GRADIO_URL_PATTERN = re.compile(r"https?://[a-zA-Z0-9\-]+\.gradio\.live")
DEFAULT_NOTEBOOK_PATH = str(NOTEBOOKS_DIR / "Super_Eleven_Lab_Lite_2_1.ipynb")
DEFAULT_SESSION_NAME = "testColab"
DEFAULT_VOICE_SAMPLE = str(VOICE_SAMPLES_DIR / "myvoice_ref_clean.wav")
FALLBACK_VOICE_SAMPLE = str(VOICE_SAMPLES_DIR / "myvoice.mp3")


class ColabAutoRunner:
    """Manages autonomous Google Colab OmniVoice server execution and dynamic discovery."""

    _instance: Optional[ColabAutoRunner] = None

    def __new__(cls) -> ColabAutoRunner:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_runner()
        return cls._instance

    def _init_runner(self) -> None:
        self.session_name = DEFAULT_SESSION_NAME
        self.notebook_path = DEFAULT_NOTEBOOK_PATH
        self.colab_bin = shutil.which("colab") or "/home/roshan/miniconda3/bin/colab"

        self.state: str = "idle"  # idle, starting, executing_cells, ready, stopped, error
        self.active_url: Optional[str] = None
        self.last_error: Optional[str] = None
        self.start_time: float = 0.0

        self._process: Optional[subprocess.Popen] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._recent_logs: Deque[str] = collections.deque(maxlen=100)

        # Check for user-defined voice sample
        self.voice_sample_path = (
            DEFAULT_VOICE_SAMPLE
            if os.path.exists(DEFAULT_VOICE_SAMPLE)
            else FALLBACK_VOICE_SAMPLE
        )

        logger.info(
            "ColabAutoRunner initialized (session=%s, notebook=%s, voice=%s)",
            self.session_name,
            self.notebook_path,
            self.voice_sample_path,
        )

    def append_log(self, line: str) -> None:
        clean = line.strip()
        if clean:
            with self._lock:
                self._recent_logs.append(f"[{time.strftime('%H:%M:%S')}] {clean}")
            logger.info("[Colab] %s", clean)

    def ensure_session(self) -> bool:
        """Verify the Colab session exists or create it with Tesla T4 GPU."""
        if not os.path.exists(self.colab_bin):
            err = f"Colab CLI binary not found at '{self.colab_bin}'"
            self.last_error = err
            self.append_log(f"ERROR: {err}")
            return False

        try:
            self.append_log(f"Checking existing session: {self.session_name}...")
            res = subprocess.run(
                [self.colab_bin, "sessions"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if self.session_name in res.stdout:
                self.append_log(f"✓ Session '{self.session_name}' is already active.")
                return True

            self.append_log(f"Creating new Colab session '{self.session_name}' with T4 GPU...")
            new_res = subprocess.run(
                [self.colab_bin, "new", "-s", self.session_name, "--gpu", "T4"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if new_res.returncode == 0 or "READY" in new_res.stdout or self.session_name in new_res.stdout:
                self.append_log(f"✓ Session '{self.session_name}' created successfully.")
                return True
            else:
                err = new_res.stderr or new_res.stdout
                self.append_log(f"Session creation notice: {err.strip()}")
                self.last_error = f"Colab session creation failed: {err.strip()}"
                return False
        except Exception as exc:
            self.last_error = str(exc)
            self.append_log(f"Warning in ensure_session: {exc}")
            return False

    def start(self, restart_if_running: bool = False) -> bool:
        """Start the background execution loop for the Colab OmniVoice notebook."""
        with self._lock:
            if self.is_running():
                if not restart_if_running:
                    logger.info("ColabAutoRunner is already active.")
                    return True
                self.stop()

            if not os.path.exists(self.notebook_path):
                self.state = "error"
                self.last_error = f"Notebook not found: {self.notebook_path}"
                self.append_log(f"ERROR: {self.last_error}")
                return False

            self._stop_event.clear()
            self.state = "starting"
            self.start_time = time.time()

            self._monitor_thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="JARVIS-ColabAutoRunner",
            )
            self._monitor_thread.start()
            logger.info("Started ColabAutoRunner thread for %s", self.session_name)
            return True

    def _run_loop(self) -> None:
        """Background thread executing the notebook and streaming Gradio output."""
        try:
            if not self.ensure_session():
                self.state = "error"
                return

            self.state = "executing_cells"
            self.append_log(f"Launching notebook '{os.path.basename(self.notebook_path)}'...")

            cmd = [
                self.colab_bin,
                "exec",
                "-s",
                self.session_name,
                "--timeout",
                "86400",
                "-f",
                self.notebook_path,
            ]

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Stream stdout line by line
            for line in iter(self._process.stdout.readline, ""):
                if self._stop_event.is_set():
                    break
                if not line:
                    continue

                self.append_log(line)

                # Search for Gradio Live Share URL
                match = GRADIO_URL_PATTERN.search(line)
                if match:
                    discovered_url = match.group(0).rstrip("/")
                    self.active_url = discovered_url
                    self.state = "ready"
                    self.append_log(f"🎯 Gradio public URL discovered: {discovered_url}")
                    self._on_url_discovered(discovered_url)

            retcode = self._process.poll()
            if not self._stop_event.is_set():
                if retcode == 0:
                    self.append_log("Colab execution finished cleanly.")
                else:
                    self.append_log(f"Colab execution terminated with exit code {retcode}")
                self.state = "stopped"

        except Exception as exc:
            self.state = "error"
            self.last_error = str(exc)
            self.append_log(f"Error in ColabAutoRunner loop: {exc}")

    def _on_url_discovered(self, gradio_url: str) -> None:
        """Register the newly discovered Gradio URL and bind user's voice reference."""
        try:
            from apps.voice.colab_registration import colab_manager
            registered = colab_manager.register_url(
                gradio_url=gradio_url,
                session_id=self.session_name,
                is_local_request=True,
                verify_now=True,
            )
            if registered.get("status") == "ok":
                self.append_log(f"✓ Registered '{gradio_url}' with ColabRegistrationManager.")
            else:
                self.append_log(f"Registration result: {registered}")
        except Exception as exc:
            self.append_log(f"Failed to register URL with colab_manager: {exc}")

        # Bind URL and personal voice sample to gradio_cloner
        try:
            from apps.voice.gradio_tts import gradio_cloner
            gradio_cloner.update_url(gradio_url)
            if os.path.exists(self.voice_sample_path):
                gradio_cloner.reference_voice_path = self.voice_sample_path
                self.append_log(f"✓ Bound user voice reference '{self.voice_sample_path}' to OmniVoice cloner.")
        except Exception as exc:
            self.append_log(f"Failed to bind reference voice to gradio_cloner: {exc}")

    def is_running(self) -> bool:
        """Check if colab process is currently running."""
        with self._lock:
            return bool(self._process and self._process.poll() is None)

    def stop(self) -> Dict[str, Any]:
        """Terminate the running execution process."""
        self._stop_event.set()
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=3)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
            self.state = "stopped"
            self.append_log("ColabAutoRunner stopped by user/system.")
            return {"status": "stopped", "message": "Colab execution stopped."}

    def status(self) -> Dict[str, Any]:
        """Return comprehensive status and recent log lines."""
        with self._lock:
            return {
                "state": self.state,
                "is_running": self.is_running(),
                "session_name": self.session_name,
                "notebook_path": self.notebook_path,
                "voice_sample_path": self.voice_sample_path,
                "voice_sample_exists": os.path.exists(self.voice_sample_path),
                "active_url": self.active_url,
                "last_error": self.last_error,
                "uptime_seconds": int(time.time() - self.start_time) if self.start_time > 0 and self.is_running() else 0,
                "recent_logs": list(self._recent_logs),
            }


# Global singleton instance
colab_runner = ColabAutoRunner()

def get_colab_runner() -> ColabAutoRunner:
    return colab_runner
