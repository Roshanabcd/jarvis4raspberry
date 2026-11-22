"""Platform-aware Desktop Screen Capture & Privacy Service (Module 43)."""

from __future__ import annotations

import base64
import hashlib
import io
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw

from modules.module_43_autonomous_screen_guardian.backend.app.config import ScreenGuardianConfig
from modules.module_43_autonomous_screen_guardian.backend.models.database import utc_now_iso

XRANDR_CONN_RE = re.compile(r"^(\S+)\s+connected\s+(?:primary\s+)?(\d+)x(\d+)\+(\d+)\+(\d+)")


@dataclass
class CapturedFrame:
    frame_id: str
    monitor_id: str
    width: int
    height: int
    sha256: str
    changed: bool
    diff_score: float
    captured_at: str
    backend_used: str
    redacted_regions: int
    png_bytes: bytes
    source_app: str = "Desktop"
    window_title: str = ""

    def to_metadata(self, include_preview_b64: bool = False) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "frame_id": self.frame_id,
            "monitor_id": self.monitor_id,
            "width": self.width,
            "height": self.height,
            "sha256": self.sha256,
            "changed": self.changed,
            "diff_score": round(self.diff_score, 4),
            "captured_at": self.captured_at,
            "backend_used": self.backend_used,
            "redacted_regions": self.redacted_regions,
            "source_app": self.source_app,
            "window_title": self.window_title,
        }
        if include_preview_b64:
            out["preview_data_url"] = "data:image/png;base64," + base64.b64encode(self.png_bytes).decode("ascii")
        return out


class ScreenCaptureError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ScreenCaptureService:
    """
    Manages user-authorized screen monitoring, monitor discovery, in-memory capture,
    sensitive window/region redaction, and frame change detection.
    """

    def __init__(
        self,
        config: Optional[ScreenGuardianConfig] = None,
        frame_provider: Optional[Callable[[str], Tuple[bytes, str]]] = None,
    ) -> None:
        self.config = config or ScreenGuardianConfig.from_env()
        self._frame_provider = frame_provider
        self.state: str = "stopped"  # stopped | monitoring | paused
        self.consent_granted: bool = False
        self.selected_monitor: str = "primary"
        self.interval_sec: float = self.config.capture_interval_sec
        self.excluded_windows: List[str] = ["1Password", "Bitwarden", "KeePassXC", "Private Browsing"]
        self.excluded_regions: List[Dict[str, int]] = []
        self._last_image: Optional[Image.Image] = None
        self._last_hash: Optional[str] = None
        self.last_frame: Optional[CapturedFrame] = None
        self.last_error: Optional[str] = None
        self.frames_captured: int = 0
        self.frames_skipped_unchanged: int = 0

    def detect_display_server(self) -> Dict[str, Any]:
        wayland = bool(os.getenv("WAYLAND_DISPLAY"))
        x11 = bool(os.getenv("DISPLAY"))
        available_backends: List[str] = []
        try:
            import mss  # noqa: F401
            available_backends.append("mss_x11")
        except Exception:
            pass
        if shutil.which("scrot"):
            available_backends.append("scrot_x11")
        if shutil.which("grim"):
            available_backends.append("grim_wayland")
        if shutil.which("xdg-desktop-portal") or wayland:
            available_backends.append("xdg_desktop_portal_pipewire")
        return {
            "session_type": os.getenv("XDG_SESSION_TYPE", "wayland" if wayland else ("x11" if x11 else "headless")),
            "display_env": os.getenv("DISPLAY", ""),
            "wayland_display": os.getenv("WAYLAND_DISPLAY", ""),
            "available_backends": available_backends,
            "headless": not (wayland or x11),
        }

    def list_monitors(self) -> List[Dict[str, Any]]:
        if os.getenv("DISPLAY") and shutil.which("xrandr"):
            try:
                proc = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, timeout=3)
                monitors: List[Dict[str, Any]] = []
                for line in proc.stdout.splitlines():
                    m = XRANDR_CONN_RE.match(line.strip())
                    if m:
                        monitors.append(
                            {
                                "monitor_id": m.group(1),
                                "width": int(m.group(2)),
                                "height": int(m.group(3)),
                                "x": int(m.group(4)),
                                "y": int(m.group(5)),
                                "primary": " primary " in line,
                            }
                        )
                if monitors:
                    return monitors
            except Exception:
                pass
        return [
            {
                "monitor_id": "primary",
                "width": 1920,
                "height": 1080,
                "x": 0,
                "y": 0,
                "primary": True,
                "note": "No live X11/Wayland display detected in current environment.",
            }
        ]

    def start(
        self,
        explicit_consent: bool,
        monitor_id: str = "primary",
        interval_sec: float = 2.0,
        excluded_windows: Optional[List[str]] = None,
        excluded_regions: Optional[List[Dict[str, int]]] = None,
    ) -> Dict[str, Any]:
        if not explicit_consent:
            raise ScreenCaptureError(
                "CONSENT_REQUIRED",
                "Explicit user consent (explicit_consent=true) is mandatory before starting screen monitoring.",
                403,
            )
        self.consent_granted = True
        self.selected_monitor = monitor_id
        self.interval_sec = max(0.5, min(60.0, float(interval_sec)))
        if excluded_windows is not None:
            self.excluded_windows = excluded_windows
        if excluded_regions is not None:
            self.excluded_regions = excluded_regions
        self.state = "monitoring"
        self.last_error = None
        return self.get_status()

    def pause(self) -> Dict[str, Any]:
        if self.state == "monitoring":
            self.state = "paused"
        return self.get_status()

    def resume(self) -> Dict[str, Any]:
        if not self.consent_granted:
            raise ScreenCaptureError("CONSENT_REQUIRED", "Cannot resume without explicit monitoring consent.", 403)
        if self.state == "paused":
            self.state = "monitoring"
        return self.get_status()

    def stop(self) -> Dict[str, Any]:
        self.state = "stopped"
        self.consent_granted = False
        self._last_image = None
        self._last_hash = None
        return self.get_status()

    def is_window_excluded(self, window_title: str) -> bool:
        low = (window_title or "").lower()
        return any(ex.lower() in low for ex in self.excluded_windows if ex.strip())

    def _capture_raw_png(self, monitor_id: str) -> Tuple[bytes, str]:
        if self._frame_provider is not None:
            return self._frame_provider(monitor_id)

        # 1. Try mss (X11 / TigerVNC)
        if os.getenv("DISPLAY"):
            try:
                import mss  # type: ignore
                with mss.mss() as sct:
                    idx = 1 if len(sct.monitors) > 1 else 0
                    shot = sct.grab(sct.monitors[idx])
                    img = Image.frombytes("RGB", shot.size, shot.rgb)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG", optimize=True)
                    return buf.getvalue(), "mss_x11"
            except Exception:
                pass

            # 2. Try scrot (X11)
            if shutil.which("scrot"):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tf:
                    subprocess.run(["scrot", "-o", tf.name], check=True, timeout=5)
                    return open(tf.name, "rb").read(), "scrot_x11"

        # 3. Try grim (Wayland / wlroots)
        if os.getenv("WAYLAND_DISPLAY") and shutil.which("grim"):
            proc = subprocess.run(["grim", "-"], capture_output=True, check=True, timeout=5)
            return proc.stdout, "grim_wayland"

        raise ScreenCaptureError(
            "DISPLAY_UNAVAILABLE",
            "No active X11/Wayland capture backend available in this headless environment. "
            "On Raspberry Pi 5 / TigerVNC / Ubuntu desktop, install mss, scrot, or grim with an active DISPLAY.",
            503,
        )

    def _apply_redactions(self, img: Image.Image) -> Tuple[Image.Image, int]:
        if not self.excluded_regions:
            return img, 0
        redacted = img.copy()
        draw = ImageDraw.Draw(redacted)
        count = 0
        for reg in self.excluded_regions:
            x = max(0, int(reg.get("x", 0)))
            y = max(0, int(reg.get("y", 0)))
            w = max(0, int(reg.get("width", 0)))
            h = max(0, int(reg.get("height", 0)))
            if w > 0 and h > 0:
                draw.rectangle([x, y, x + w, y + h], fill=(0, 0, 0))
                count += 1
        return redacted, count

    def capture_frame(
        self,
        raw_png_override: Optional[bytes] = None,
        source_app: str = "Desktop",
        window_title: str = "",
        require_active_session: bool = True,
    ) -> CapturedFrame:
        if require_active_session and self.state != "monitoring":
            raise ScreenCaptureError(
                "MONITORING_NOT_ACTIVE",
                f"Screen capture requires an active monitoring session (current state: '{self.state}').",
                409,
            )
        if self.is_window_excluded(window_title):
            raise ScreenCaptureError(
                "WINDOW_EXCLUDED",
                f"Window '{window_title}' matches a privacy exclusion rule and was not captured.",
                403,
            )

        try:
            if raw_png_override is not None:
                raw_bytes, backend = raw_png_override, "injected_frame"
            else:
                raw_bytes, backend = self._capture_raw_png(self.selected_monitor)

            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            img, redacted_count = self._apply_redactions(img)

            out_buf = io.BytesIO()
            img.save(out_buf, format="PNG", optimize=True)
            final_bytes = out_buf.getvalue()
            sha = hashlib.sha256(final_bytes).hexdigest()

            changed = True
            diff_score = 1.0
            if self._last_hash == sha:
                changed = False
                diff_score = 0.0
                self.frames_skipped_unchanged += 1
            elif self._last_image is not None and self._last_image.size == img.size:
                diff = ImageChops.difference(self._last_image, img)
                hist = diff.histogram()
                # Mean absolute channel diff normalized to [0, 1]
                total_pixels = img.size[0] * img.size[1] * 3
                weighted = sum((i % 256) * count for i, count in enumerate(hist))
                diff_score = weighted / max(1, total_pixels * 255)
                changed = diff_score > 0.002
                if not changed:
                    self.frames_skipped_unchanged += 1

            self._last_image = img
            self._last_hash = sha
            self.frames_captured += 1
            frame = CapturedFrame(
                frame_id=f"frm_{sha[:10]}_{self.frames_captured}",
                monitor_id=self.selected_monitor,
                width=img.size[0],
                height=img.size[1],
                sha256=sha,
                changed=changed,
                diff_score=diff_score,
                captured_at=utc_now_iso(),
                backend_used=backend,
                redacted_regions=redacted_count,
                png_bytes=final_bytes,
                source_app=source_app,
                window_title=window_title,
            )
            self.last_frame = frame
            self.last_error = None
            return frame
        except ScreenCaptureError as exc:
            self.last_error = exc.message
            raise
        except Exception as exc:
            self.last_error = str(exc)
            raise ScreenCaptureError("CAPTURE_FAILED", f"Screen capture failed: {exc}", 500)

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "consent_granted": self.consent_granted,
            "selected_monitor": self.selected_monitor,
            "interval_sec": self.interval_sec,
            "excluded_windows": self.excluded_windows,
            "excluded_regions_count": len(self.excluded_regions),
            "store_raw_screenshots": self.config.store_raw_screenshots,
            "frames_captured": self.frames_captured,
            "frames_skipped_unchanged": self.frames_skipped_unchanged,
            "last_error": self.last_error,
            "display_server": self.detect_display_server(),
        }
