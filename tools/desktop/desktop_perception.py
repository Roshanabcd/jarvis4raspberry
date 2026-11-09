"""
JARVIS OS — Phase 4 Desktop Perception Service
Full-screen and active window capture, window geometry extraction,
application identification, and ephemeral screenshot management on Native X11.
"""

import os
import re
import time
import base64
import logging
import hashlib
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

logger = logging.getLogger("JARVIS.Perception")

class DesktopPerceptionService:
    """Provides screen perception, window hierarchy inspection, and visual snapshotting."""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or "/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/screenshots")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.display = os.environ.get("DISPLAY", ":0")
        self.max_history = 10
        self._last_observation: Optional[Dict[str, Any]] = None

    def get_screen_resolution(self) -> Dict[str, int]:
        """Detect current screen resolution via xrandr or fallback to 1360x768."""
        try:
            res = subprocess.run(
                ["xrandr", "--current"],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=3,
            )
            for line in res.stdout.splitlines():
                if "*" in line:
                    match = re.search(r"(\d+)x(\d+)", line)
                    if match:
                        return {"width": int(match.group(1)), "height": int(match.group(2))}
        except Exception as e:
            logger.debug("xrandr query error: %s", e)

        # Fallback query via xdpyinfo
        try:
            res = subprocess.run(
                ["xdpyinfo", "-display", self.display],
                capture_output=True,
                text=True,
                timeout=3,
            )
            m = re.search(r"dimensions:\s+(\d+)x(\d+)", res.stdout)
            if m:
                return {"width": int(m.group(1)), "height": int(m.group(2))}
        except Exception:
            pass

        return {"width": 1360, "height": 768}

    def list_open_windows(self) -> List[Dict[str, Any]]:
        """List all top-level desktop windows via wmctrl -l -p -G."""
        windows = []
        try:
            res = subprocess.run(
                ["wmctrl", "-l", "-p", "-G"],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=4,
            )
            for line in res.stdout.splitlines():
                parts = line.split(None, 8)
                if len(parts) >= 8:
                    win_id = parts[0]
                    desktop_id = int(parts[1]) if parts[1].lstrip('-').isdigit() else -1
                    pid = int(parts[2]) if parts[2].isdigit() else 0
                    x = int(parts[3])
                    y = int(parts[4])
                    w = int(parts[5])
                    h = int(parts[6])
                    client = parts[7]
                    title = parts[8] if len(parts) > 8 else ""

                    # Query WM_CLASS to identify the application name accurately
                    app_name = self._get_window_app_name(win_id, title)

                    windows.append({
                        "id": win_id,
                        "title": title,
                        "app": app_name,
                        "desktop": desktop_id,
                        "pid": pid,
                        "client": client,
                        "geometry": {"x": x, "y": y, "width": w, "height": h},
                    })
        except Exception as e:
            logger.error("Error listing windows via wmctrl: %s", e)

        return windows

    def _get_window_app_name(self, win_id: str, title: str) -> str:
        """Extract application name from WM_CLASS using xprop."""
        try:
            res = subprocess.run(
                ["xprop", "-id", win_id, "WM_CLASS"],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=2,
            )
            if "WM_CLASS" in res.stdout:
                matches = re.findall(r'"([^"]*)"', res.stdout)
                if matches:
                    return matches[-1].lower()
        except Exception:
            pass

        t_lower = title.lower()
        if "chrome" in t_lower:
            return "google-chrome"
        if "visual studio code" in t_lower or "code" in t_lower:
            return "code"
        if "freetube" in t_lower:
            return "freetube"
        if "terminal" in t_lower or "@raspberrypi" in t_lower:
            return "lxterminal"
        if "downloads" in t_lower or "pcmanfm" in t_lower:
            return "pcmanfm"
        return "unknown"

    def get_active_window(self) -> Dict[str, Any]:
        """Query the currently focused window on DISPLAY=:0."""
        try:
            res = subprocess.run(
                ["xdotool", "getactivewindow"],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout.strip().isdigit():
                dec_id = int(res.stdout.strip())
                hex_id = f"0x{dec_id:08x}"

                # Query title
                t_res = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                title = t_res.stdout.strip()

                # Query geometry via xdotool
                g_res = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowgeometry"],
                    env={**os.environ, "DISPLAY": self.display},
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                x, y, w, h = 0, 0, 1360, 768
                m_pos = re.search(r"Position:\s+(\d+),(\d+)", g_res.stdout)
                if m_pos:
                    x, y = int(m_pos.group(1)), int(m_pos.group(2))
                m_geo = re.search(r"Geometry:\s+(\d+)x(\d+)", g_res.stdout)
                if m_geo:
                    w, h = int(m_geo.group(1)), int(m_geo.group(2))

                app_name = self._get_window_app_name(hex_id, title)

                return {
                    "id": hex_id,
                    "title": title,
                    "app": app_name,
                    "geometry": {"x": x, "y": y, "width": w, "height": h},
                    "focused": True,
                }
        except Exception as e:
            logger.debug("Active window query error: %s", e)

        # Fallback to desktop root
        res_geom = self.get_screen_resolution()
        return {
            "id": "0x00000000",
            "title": "Desktop Root",
            "app": "desktop",
            "geometry": {"x": 0, "y": 0, "width": res_geom["width"], "height": res_geom["height"]},
            "focused": True,
        }

    def capture_fullscreen(self) -> Dict[str, Any]:
        """Capture full screen screenshot via scrot."""
        self._cleanup_old_snapshots()
        timestamp = int(time.time() * 1000)
        filename = f"screen_{timestamp}.png"
        filepath = self.storage_dir / filename

        try:
            t0 = time.perf_counter()
            res = subprocess.run(
                ["scrot", str(filepath)],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                timeout=5,
            )
            t_ms = (time.perf_counter() - t0) * 1000

            if res.returncode == 0 and filepath.exists():
                return self._process_image_metadata(filepath, "fullscreen", t_ms)
            else:
                logger.error("scrot fullscreen failed: %s", res.stderr.decode("utf-8", "ignore"))
        except Exception as e:
            logger.error("Capture fullscreen exception: %s", e)

        return {"status": "error", "message": "Failed to capture fullscreen"}

    def capture_active_window(self) -> Dict[str, Any]:
        """Capture only the currently focused window."""
        self._cleanup_old_snapshots()
        timestamp = int(time.time() * 1000)
        filename = f"window_{timestamp}.png"
        filepath = self.storage_dir / filename

        try:
            t0 = time.perf_counter()
            res = subprocess.run(
                ["scrot", "-u", str(filepath)],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                timeout=5,
            )
            t_ms = (time.perf_counter() - t0) * 1000

            if res.returncode == 0 and filepath.exists():
                return self._process_image_metadata(filepath, "active_window", t_ms)
        except Exception as e:
            logger.error("scrot active window failed: %s", e)

        return self.capture_fullscreen()

    def capture_region(self, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
        """Capture a bounded rectangle on screen."""
        self._cleanup_old_snapshots()
        timestamp = int(time.time() * 1000)
        filename = f"region_{timestamp}.png"
        filepath = self.storage_dir / filename

        try:
            t0 = time.perf_counter()
            res = subprocess.run(
                ["scrot", "-a", f"{x},{y},{width},{height}", str(filepath)],
                env={**os.environ, "DISPLAY": self.display},
                capture_output=True,
                timeout=5,
            )
            t_ms = (time.perf_counter() - t0) * 1000

            if res.returncode == 0 and filepath.exists():
                return self._process_image_metadata(filepath, "region", t_ms, region=(x, y, width, height))
        except Exception as e:
            logger.error("scrot region capture failed: %s", e)

        return {"status": "error", "message": f"Failed to capture region {x},{y},{width},{height}"}

    def _process_image_metadata(
        self,
        filepath: Path,
        mode: str,
        duration_ms: float,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """Read image with Pillow, calculate hash, thumbnail, and metadata."""
        try:
            with Image.open(filepath) as img:
                w, h = img.size
                format_name = img.format or "PNG"

                # Generate lightweight thumbnail for UI preview
                thumb = img.copy()
                thumb.thumbnail((480, 270))
                thumb_path = filepath.with_suffix(".thumb.jpg")
                thumb.convert("RGB").save(thumb_path, "JPEG", quality=75)

                with open(thumb_path, "rb") as tf:
                    thumb_b64 = f"data:image/jpeg;base64,{base64.b64encode(tf.read()).decode('utf-8')}"

                # Calculate MD5 image content hash for difference detection
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                    img_hash = hashlib.md5(file_bytes).hexdigest()

                stat = filepath.stat()

                return {
                    "status": "ok",
                    "mode": mode,
                    "filepath": str(filepath),
                    "filename": filepath.name,
                    "thumbnail_url": thumb_b64,
                    "width": w,
                    "height": h,
                    "format": format_name,
                    "size_bytes": stat.st_size,
                    "hash": img_hash,
                    "region": region,
                    "duration_ms": round(duration_ms, 2),
                    "timestamp": time.time(),
                }
        except Exception as e:
            logger.error("Error processing snapshot image: %s", e)
            return {"status": "error", "message": str(e)}

    def observe_desktop(self) -> Dict[str, Any]:
        """Perform a full perceptual observation of the desktop environment."""
        t_start = time.perf_counter()
        resolution = self.get_screen_resolution()
        active_win = self.get_active_window()
        open_wins = self.list_open_windows()
        snap = self.capture_fullscreen()
        total_ms = (time.perf_counter() - t_start) * 1000

        observation = {
            "status": "ok",
            "timestamp": time.time(),
            "total_ms": round(total_ms, 2),
            "resolution": resolution,
            "active_window": active_win,
            "open_windows_count": len(open_wins),
            "open_windows": open_wins,
            "snapshot": snap,
        }
        self._last_observation = observation
        return observation

    def get_last_observation(self) -> Optional[Dict[str, Any]]:
        return self._last_observation

    def _cleanup_old_snapshots(self) -> None:
        """Retain only the last N snapshots in data/screenshots to conserve disk space."""
        try:
            files = sorted(self.storage_dir.glob("screen_*.png"), key=lambda p: p.stat().st_mtime)
            if len(files) > self.max_history:
                for f in files[:-self.max_history]:
                    try:
                        f.unlink()
                        thumb = f.with_suffix(".thumb.jpg")
                        if thumb.exists():
                            thumb.unlink()
                    except Exception:
                        pass
        except Exception as e:
            logger.debug("Screenshot cleanup note: %s", e)


desktop_perception = DesktopPerceptionService()
