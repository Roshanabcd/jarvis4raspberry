#!/usr/bin/env python3
"""
JARVIS OS ? Neural Vision & Spatial Distance Engine for Raspberry Pi 5
======================================================================
Hardware Target:
  - Raspberry Pi 5 (64-bit Raspberry Pi OS Bookworm / Trixie)
  - Raspberry Pi Camera Module 3 (Sony IMX708 12MP sensor, Phase Detection Autofocus)
    Specs: https://www.raspberrypi.com/documentation/accessories/camera-module-3.html
    Product Brief: https://pip-assets.raspberrypi.com/categories/786-raspberry-pi-camera-module-3/documents/RP-008151-DS-1-camera-module-3-product-brief.pdf

Science & AI Pipeline:
  1. Deep Neural Object Detection & ByteTrack Multi-Object Tracking:
     Uses Ultralytics YOLO (YOLO11n / YOLOv8n with optional NCNN export for Pi 5 ARM Cortex-A76)
     to detect and track 80 COCO object classes in real time.
     Ref: https://docs.ultralytics.com/guides/raspberry-pi
  2. Dual-Mode Optical & Autofocus Spatial Distance Estimation:
     - Pinhole Camera Projective Geometry:
       Computes focal length in pixels from Camera Module 3's horizontal (66 deg) and vertical
       (41 deg) field of view (4.74 mm focal length; or 102 deg x 67 deg for Wide 2.75 mm):
         f_px = (W / 2) / tan(HFOV / 2)
         Z_pinhole = (Real_Size_m * f_px) / Apparent_BBox_Pixels
     - Phase Detection Autofocus (PDAF) Dioptre Telemetry:
       Reads real-time `LensPosition` (in dioptres, where 1 dioptre = 1 / distance_in_meters)
       and `AfState` from `Picamera2.capture_metadata()`:
         Z_pdaf = 1.0 / max(LensPosition, 0.05)
       Ref: https://pip.raspberrypi.com/documents/RP-008156-DS-picamera2-manual.pdf
     - Kalman-Inspired Exponential Moving Average (EMA) Sensor Fusion:
       Fuses `Z_pinhole` with `Z_pdaf` when the target is near the autofocus region of interest
       and smooths distance and 3D camera-frame coordinates (X, Y, Z in meters) across frames
       by track ID to eliminate bounding-box jitter.
  3. Dual Output Mode for JARVIS OS (`0.0.0.0:8000` / Desktop):
     - Local OpenCV Iron-Man / JARVIS tactical HUD window (`--display` or default)
     - Optional Flask/MJPEG stream + `/api/detections` JSON telemetry endpoint (`--web --port 8082`)
       so you can embed the annotated feed and spatial memory directly into your JARVIS OS dashboard.

Quick Setup on Raspberry Pi 5:
  sudo apt update && sudo apt install -y python3-picamera2 python3-opencv python3-flask
  python3 -m venv --system-site-packages jarvis_venv
  source jarvis_venv/bin/activate
  pip install ultralytics

Usage:
  python3 camera.py                         # Standard Camera Module 3 + local HUD + Web API
  python3 camera.py --export-ncnn           # Export & run NCNN model for max FPS on Pi 5
  python3 camera.py --wide                  # Use Camera Module 3 Wide (102° HFOV) optics
  python3 camera.py --test-image frame.jpg  # Run single-image diagnostic test
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import logging
import math
import os
import signal
import socket
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple

# Auto-re-exec into dedicated hardware-accelerated venv if current Python lacks picamera2
VENV_PYTHON = os.path.expanduser("~/jarvis_camera_venv/bin/python")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = os.path.expanduser("~/jarvis_venv/bin/python")

if os.path.exists(VENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(VENV_PYTHON):
    try:
        import picamera2  # noqa: F401
    except ImportError:
        print(f"[JARVIS] Switching to hardware camera environment ({VENV_PYTHON})...")
        os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

# Configure Qt font directory to prevent Qt QFontDatabase warning logs
os.environ.setdefault("QT_QPA_FONTDIR", "/usr/share/fonts/truetype/dejavu")

import cv2
import numpy as np

# Attempt to import Picamera2 and libcamera controls (pre-installed on Raspberry Pi OS)
try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

# Ultralytics YOLO will be imported lazily in _load_yolo_model for fast CLI startup
YOLO = None
YOLO_AVAILABLE = None

# Attempt to import Flask for JARVIS OS Web Dashboard integration
try:
    from flask import Flask, Response, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


# ==============================================================================
# 1. RASPBERRY PI CAMERA MODULE 3 OPTICAL SPECIFICATIONS & REAL-WORLD PRIORS
# ==============================================================================
# Reference: Raspberry Pi Camera Module 3 Datasheet (Sony IMX708, 4608x2592, 7.4mm diagonal)
# Standard variant: Focal length = 4.74 mm, HFOV = 66.0°, VFOV = 41.0°
# Wide variant:     Focal length = 2.75 mm, HFOV = 102.0°, VFOV = 67.0°

@dataclass
class CameraOpticsConfig:
    width: int = 1280
    height: int = 720
    hfov_deg: float = 66.0
    vfov_deg: float = 41.0
    focal_length_mm: float = 4.74

    @property
    def fx(self) -> float:
        """Horizontal focal length in pixels derived from pinhole geometry."""
        return (self.width / 2.0) / math.tan(math.radians(self.hfov_deg / 2.0))

    @property
    def fy(self) -> float:
        """Vertical focal length in pixels derived from pinhole geometry."""
        return (self.height / 2.0) / math.tan(math.radians(self.vfov_deg / 2.0))

    @property
    def cx(self) -> float:
        return self.width / 2.0

    @property
    def cy(self) -> float:
        return self.height / 2.0


# Anthropometric & physical object priors (in meters) for COCO classes.
# Format: class_name -> (reference_height_m, reference_width_m, preferred_axis)
# Note: For "person", we dynamically handle seated/upper-body vs full standing posture!
COCO_PHYSICAL_PRIORS: Dict[str, Tuple[float, float, str]] = {
    "person": (1.68, 0.48, "adaptive_person"),
    "bicycle": (1.05, 1.70, "height"),
    "car": (1.50, 1.80, "height"),
    "motorcycle": (1.15, 0.80, "height"),
    "bus": (3.10, 2.55, "height"),
    "truck": (3.20, 2.50, "height"),
    "cat": (0.28, 0.45, "height"),
    "dog": (0.50, 0.65, "height"),
    "backpack": (0.45, 0.32, "height"),
    "umbrella": (0.85, 0.95, "width"),
    "handbag": (0.30, 0.35, "height"),
    "bottle": (0.24, 0.075, "height"),
    "wine glass": (0.20, 0.08, "height"),
    "cup": (0.11, 0.085, "height"),
    "fork": (0.19, 0.025, "height"),
    "knife": (0.21, 0.025, "height"),
    "spoon": (0.18, 0.035, "height"),
    "bowl": (0.09, 0.16, "width"),
    "banana": (0.12, 0.18, "width"),
    "apple": (0.08, 0.08, "width"),
    "chair": (0.85, 0.52, "height"),
    "couch": (0.85, 1.95, "height"),
    "potted plant": (0.45, 0.30, "height"),
    "bed": (0.75, 1.50, "width"),
    "dining table": (0.76, 1.30, "height"),
    "tv": (0.55, 0.95, "width"),
    "laptop": (0.24, 0.35, "width"),
    "mouse": (0.04, 0.065, "width"),
    "remote": (0.16, 0.045, "height"),
    "keyboard": (0.14, 0.44, "width"),
    "cell phone": (0.15, 0.075, "height"),
    "microwave": (0.30, 0.50, "width"),
    "oven": (0.85, 0.60, "height"),
    "refrigerator": (1.70, 0.75, "height"),
    "book": (0.23, 0.16, "height"),
    "clock": (0.28, 0.28, "height"),
    "vase": (0.28, 0.14, "height"),
    "scissors": (0.18, 0.07, "height"),
    "teddy bear": (0.35, 0.25, "height"),
}


# ==============================================================================
# 2. KALMAN-INSPIRED TEMPORAL SMOOTHING & SPATIAL DISTANCE ENGINE
# ==============================================================================

@dataclass
class TrackedTarget:
    track_id: int
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    distance_m: float
    coords_3d: Tuple[float, float, float]  # (X_m, Y_m, Z_m) in camera frame
    bearing_deg: Tuple[float, float]       # (azimuth_deg, elevation_deg)
    zone: str                              # CRITICAL (<1.0m), NEAR (1.0-2.5m), SAFE (>2.5m)
    method: str                            # "FUSED (PDAF+OPTIC)" or "OPTICAL PINHOLE"
    last_seen: float = field(default_factory=time.time)


class SpatialDistanceEngine:
    """
    Computes 3D spatial coordinates (X, Y, Z), bearing angles, and distance in meters
    by combining Camera Module 3 pinhole optics with IMX708 PDAF LensPosition telemetry.
    """

    def __init__(self, optics: CameraOpticsConfig, ema_alpha: float = 0.35):
        self.optics = optics
        self.ema_alpha = ema_alpha
        self._smoothed_distances: Dict[int, float] = {}
        self._smoothed_bboxes: Dict[int, np.ndarray] = {}

    def estimate_pinhole_distance(
        self, label: str, x1: float, y1: float, x2: float, y2: float
    ) -> float:
        """
        Estimates distance (Z in meters) using thin-lens pinhole projection:
          Z = (Real_Dimension_m * Focal_Length_px) / Apparent_Pixels
        Includes posture-aware compensation for 'person' bounding boxes (e.g., seated
        or upper-body framing near the bottom of the frame, as common in desktop setups).
        """
        bw = max(x2 - x1, 4.0)
        bh = max(y2 - y1, 4.0)
        aspect = bw / bh

        ref_h, ref_w, mode = COCO_PHYSICAL_PRIORS.get(label, (0.35, 0.35, "height"))

        if mode == "adaptive_person":
            # Check if person bbox is touching the bottom border or has seated/upper-body aspect ratio
            touches_bottom = y2 >= (self.optics.height * 0.94)
            if aspect > 0.62 or touches_bottom:
                # Seated or upper-body framing: shoulder/torso span (~0.52m) and seated height (~0.88m)
                z_from_w = (0.54 * self.optics.fx) / bw
                z_from_h = (0.88 * self.optics.fy) / bh
                return 0.55 * z_from_h + 0.45 * z_from_w
            else:
                # Full standing posture
                z_from_h = (ref_h * self.optics.fy) / bh
                z_from_w = (ref_w * self.optics.fx) / bw
                return 0.75 * z_from_h + 0.25 * z_from_w
        elif mode == "width":
            return (ref_w * self.optics.fx) / bw
        else:
            return (ref_h * self.optics.fy) / bh

    def fuse_with_pdaf(
        self,
        z_pinhole: float,
        bbox: Tuple[float, float, float, float],
        lens_position_dioptres: Optional[float],
        af_state: Optional[int],
    ) -> Tuple[float, str]:
        """
        Fuses optical pinhole distance with Raspberry Pi Camera Module 3's PDAF
        `LensPosition` metadata (measured in dioptres = 1 / distance_m).
        When the bounding box overlaps the central autofocus region and LensPosition > 0.1,
        blends the hardware focus distance with the optical estimate.
        """
        x1, y1, x2, y2 = bbox
        cx_box = 0.5 * (x1 + x2)
        cy_box = 0.5 * (y1 + y2)

        # Check if object is near the central 45% of the frame where PDAF weights focus
        dist_from_center = math.hypot(
            (cx_box - self.optics.cx) / self.optics.width,
            (cy_box - self.optics.cy) / self.optics.height,
        )
        is_centered = dist_from_center < 0.28

        if (
            lens_position_dioptres is not None
            and lens_position_dioptres > 0.15
            and is_centered
        ):
            z_pdaf = 1.0 / float(lens_position_dioptres)
            # PDAF is most accurate between 0.10m and 3.5m on the IMX708 VCM actuator
            if 0.10 <= z_pdaf <= 3.50 and abs(z_pdaf - z_pinhole) / max(z_pinhole, 0.1) < 0.65:
                # Weight PDAF higher when AfState == 2 (Focused)
                pdaf_weight = 0.45 if af_state == 2 else 0.25
                z_fused = (1.0 - pdaf_weight) * z_pinhole + pdaf_weight * z_pdaf
                return z_fused, "FUSED (PDAF+OPTIC)"

        return z_pinhole, "OPTICAL PINHOLE"

    def process_detection(
        self,
        track_id: int,
        label: str,
        confidence: float,
        raw_bbox: Tuple[float, float, float, float],
        lens_position: Optional[float],
        af_state: Optional[int],
    ) -> TrackedTarget:
        # Smooth bounding box coordinates
        raw_arr = np.array(raw_bbox, dtype=np.float32)
        if track_id in self._smoothed_bboxes:
            smooth_arr = (
                self.ema_alpha * raw_arr
                + (1.0 - self.ema_alpha) * self._smoothed_bboxes[track_id]
            )
        else:
            smooth_arr = raw_arr
        self._smoothed_bboxes[track_id] = smooth_arr

        x1, y1, x2, y2 = [float(v) for v in smooth_arr]
        z_pinhole = self.estimate_pinhole_distance(label, x1, y1, x2, y2)
        z_raw, method = self.fuse_with_pdaf(
            z_pinhole, (x1, y1, x2, y2), lens_position, af_state
        )

        # Temporal EMA filter on distance
        if track_id in self._smoothed_distances:
            z_smooth = (
                self.ema_alpha * z_raw
                + (1.0 - self.ema_alpha) * self._smoothed_distances[track_id]
            )
        else:
            z_smooth = z_raw
        self._smoothed_distances[track_id] = z_smooth

        # Back-project 2D pixel centroid (u, v) to 3D metric camera coordinates (X, Y, Z)
        u = 0.5 * (x1 + x2)
        v = 0.5 * (y1 + y2)
        x_3d = ((u - self.optics.cx) * z_smooth) / self.optics.fx
        y_3d = ((v - self.optics.cy) * z_smooth) / self.optics.fy

        # Bearing angles (azimuth & elevation in degrees)
        azimuth_deg = math.degrees(math.atan2(x_3d, z_smooth))
        elevation_deg = math.degrees(math.atan2(-y_3d, z_smooth))

        # Proximity zone classification
        if z_smooth < 1.0:
            zone = "CRITICAL"
        elif z_smooth < 2.5:
            zone = "NEAR"
        else:
            zone = "SAFE"

        return TrackedTarget(
            track_id=track_id,
            label=label,
            confidence=confidence,
            bbox=(int(x1), int(y1), int(x2), int(y2)),
            distance_m=round(z_smooth, 2),
            coords_3d=(round(x_3d, 2), round(y_3d, 2), round(z_smooth, 2)),
            bearing_deg=(round(azimuth_deg, 1), round(elevation_deg, 1)),
            zone=zone,
            method=method,
            last_seen=time.time(),
        )


# ==============================================================================
# 3. JARVIS OS TACTICAL HUD RENDERER (IRON-MAN CYAN / AMBER / CRIMSON OVERLAY)
# ==============================================================================

class JarvisHUDRenderer:
    """
    Renders a futuristic JARVIS OS spatial telemetry overlay with corner brackets,
    3D metric coordinates, top-down radar sonar mini-map, and Camera Module 3 ISP stats.
    """

    # BGR Color Palette matching JARVIS OS Dark UI
    CYAN = (240, 215, 0)
    AMBER = (0, 185, 255)
    CRIMSON = (60, 40, 255)
    EMERALD = (120, 230, 40)
    DARK_BG = (18, 14, 10)
    WHITE = (245, 245, 245)

    def __init__(self, optics: CameraOpticsConfig):
        self.optics = optics

    def _zone_color(self, zone: str) -> Tuple[int, int, int]:
        if zone == "CRITICAL":
            return self.CRIMSON
        if zone == "NEAR":
            return self.AMBER
        return self.CYAN

    @staticmethod
    def _draw_corner_brackets(
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        color: Tuple[int, int, int],
        thickness: int = 2,
    ) -> None:
        x1, y1, x2, y2 = bbox
        bw = x2 - x1
        bh = y2 - y1
        L = max(12, min(int(min(bw, bh) * 0.22), 34))

        # Top-Left
        cv2.line(frame, (x1, y1), (x1 + L, y1), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x1, y1), (x1, y1 + L), color, thickness, cv2.LINE_AA)
        # Top-Right
        cv2.line(frame, (x2, y1), (x2 - L, y1), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x2, y1), (x2, y1 + L), color, thickness, cv2.LINE_AA)
        # Bottom-Left
        cv2.line(frame, (x1, y2), (x1 + L, y2), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x1, y2), (x1, y2 - L), color, thickness, cv2.LINE_AA)
        # Bottom-Right
        cv2.line(frame, (x2, y2), (x2 - L, y2), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x2, y2), (x2, y2 - L), color, thickness, cv2.LINE_AA)

        # Subtle inner bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)

    def draw_radar_minimap(
        self, frame: np.ndarray, targets: List[TrackedTarget], max_range_m: float = 5.0
    ) -> None:
        """Draws a top-down polar spatial radar in the bottom-right corner of the HUD."""
        h, w = frame.shape[:2]
        radius = 85
        cx = w - radius - 24
        cy = h - radius - 24

        # Semi-transparent radar circle
        overlay = frame.copy()
        cv2.circle(overlay, (cx, cy), radius, self.DARK_BG, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

        # Range rings (1.5m, 3.0m, 5.0m)
        for frac in (0.3, 0.6, 1.0):
            cv2.circle(
                frame, (cx, cy), int(radius * frac), (95, 85, 30), 1, cv2.LINE_AA
            )

        # Camera FOV cone lines
        half_fov_rad = math.radians(self.optics.hfov_deg / 2.0)
        lx = int(cx - radius * math.sin(half_fov_rad))
        ly = int(cy - radius * math.cos(half_fov_rad))
        rx = int(cx + radius * math.sin(half_fov_rad))
        ry = int(cy - radius * math.cos(half_fov_rad))
        cv2.line(frame, (cx, cy), (lx, ly), self.CYAN, 1, cv2.LINE_AA)
        cv2.line(frame, (cx, cy), (rx, ry), self.CYAN, 1, cv2.LINE_AA)

        # Plot each detected target in polar/top-down (X, Z) space
        for t in targets:
            x_m, _, z_m = t.coords_3d
            scale = radius / max_range_m
            px = int(np.clip(cx + x_m * scale, cx - radius + 4, cx + radius - 4))
            py = int(np.clip(cy - z_m * scale, cy - radius + 4, cy + radius - 4))
            color = self._zone_color(t.zone)
            cv2.circle(frame, (px, py), 5, color, -1, cv2.LINE_AA)
            cv2.putText(
                frame,
                f"{t.label[:3].upper()} {t.distance_m:.1f}m",
                (px - 18, py - 7),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.33,
                self.WHITE,
                1,
                cv2.LINE_AA,
            )

        cv2.putText(
            frame,
            "SPATIAL RADAR (5m)",
            (cx - 58, cy + radius + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            self.CYAN,
            1,
            cv2.LINE_AA,
        )

    def render(
        self,
        frame: np.ndarray,
        targets: List[TrackedTarget],
        fps: float,
        metadata: Dict[str, object],
    ) -> np.ndarray:
        h, w = frame.shape[:2]

        # 1. Central optical boresight reticle
        cx, cy = int(self.optics.cx), int(self.optics.cy)
        cv2.circle(frame, (cx, cy), 16, (120, 110, 0), 1, cv2.LINE_AA)
        cv2.line(frame, (cx - 24, cy), (cx - 8, cy), self.CYAN, 1, cv2.LINE_AA)
        cv2.line(frame, (cx + 8, cy), (cx + 24, cy), self.CYAN, 1, cv2.LINE_AA)
        cv2.line(frame, (cx, cy - 24), (cx, cy - 8), self.CYAN, 1, cv2.LINE_AA)
        cv2.line(frame, (cx, cy + 8), (cx, cy + 24), self.CYAN, 1, cv2.LINE_AA)

        # 2. Top telemetry bar (matches camera metadata bar with exposure, gain, LensPosition)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 42), self.DARK_BG, -1)
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

        exp_val = metadata.get("ExposureTime")
        exp_us = int(exp_val) if exp_val is not None else 0
        ag_val = metadata.get("AnalogueGain")
        ag = float(ag_val) if ag_val is not None else 0.0
        dg_val = metadata.get("DigitalGain")
        dg = float(dg_val) if dg_val is not None else 0.0
        lens_pos = metadata.get("LensPosition", None)
        af_val = metadata.get("AfState")
        af_state = int(af_val) if af_val is not None else 0
        pdaf_m_str = (
            f"{1.0 / float(lens_pos):.2f}m ({float(lens_pos):.2f}D)"
            if lens_pos is not None and float(lens_pos) > 0.05
            else "INF"
        )

        header_left = (
            f"JARVIS OS // NEURAL VISION HUD | FPS: {fps:.1f} | TARGETS: {len(targets)}"
        )
        header_right = (
            f"IMX708 PDAF: {pdaf_m_str} (AF:{af_state}) | EXP:{exp_us}us AG:{ag:.2f} DG:{dg:.2f}"
        )
        cv2.putText(
            frame,
            header_left,
            (14, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            self.CYAN,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            header_right,
            (max(w - 540, 420), 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.EMERALD,
            1,
            cv2.LINE_AA,
        )

        # 3. Render each tracked object with distance, 3D coordinates, and vector line
        for t in targets:
            x1, y1, x2, y2 = t.bbox
            color = self._zone_color(t.zone)
            self._draw_corner_brackets(frame, t.bbox, color, thickness=2)

            # Target centroid and vector line from bottom-center of HUD
            bx = int(0.5 * (x1 + x2))
            by = int(0.5 * (y1 + y2))
            cv2.circle(frame, (bx, by), 4, color, -1, cv2.LINE_AA)
            cv2.line(frame, (cx, h - 10), (bx, y2), color, 1, cv2.LINE_AA)

            # Primary label banner: [ID] CLASS | CONF | DISTANCE (m & cm)
            dist_cm = int(t.distance_m * 100)
            title_text = (
                f"#{t.track_id} {t.label.upper()} ({int(t.confidence * 100)}%) "
                f"| {t.distance_m:.2f}m ({dist_cm}cm)"
            )
            sub_text = (
                f"XYZ:[{t.coords_3d[0]:+.2f}, {t.coords_3d[1]:+.2f}, {t.coords_3d[2]:.2f}m] "
                f"AZ:{t.bearing_deg[0]:+.1f}deg [{t.zone}]"
            )

            label_y = max(y1 - 28, 54)
            (tw1, th1), _ = cv2.getTextSize(
                title_text, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1
            )
            (tw2, th2), _ = cv2.getTextSize(
                sub_text, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1
            )
            box_w = max(tw1, tw2) + 14

            banner = frame.copy()
            cv2.rectangle(
                banner,
                (x1, label_y - th1 - 6),
                (min(x1 + box_w, w - 4), label_y + th2 + 12),
                self.DARK_BG,
                -1,
            )
            cv2.addWeighted(banner, 0.78, frame, 0.22, 0, frame)

            cv2.putText(
                frame,
                title_text,
                (x1 + 6, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                color,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                sub_text,
                (x1 + 6, label_y + th2 + 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.40,
                self.WHITE,
                1,
                cv2.LINE_AA,
            )

        # 4. Draw top-down spatial radar mini-map
        self.draw_radar_minimap(frame, targets)
        return frame


# ==============================================================================
# 4. PICAMERA2 + ULTRALYTICS YOLO + JARVIS OS TELEMETRY SERVER
# ==============================================================================

class JarvisVisionApp:
    """
    Main application orchestrating Raspberry Pi Camera Module 3 capture,
    Ultralytics YOLO inference, optical/PDAF distance calculation, and JARVIS OS streaming.
    """

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.optics = CameraOpticsConfig(
            width=args.width,
            height=args.height,
            hfov_deg=102.0 if args.wide else 66.0,
            vfov_deg=67.0 if args.wide else 41.0,
            focal_length_mm=2.75 if args.wide else 4.74,
        )
        self.spatial_engine = SpatialDistanceEngine(self.optics)
        self.hud = JarvisHUDRenderer(self.optics)

        self._running = True
        self.backend_name = "unknown"
        self.latest_raw_jpeg: Optional[bytes] = None
        self.latest_raw_timestamp: float = 0.0
        self.latest_annotated_jpeg: Optional[bytes] = None
        self.latest_annotated_timestamp: float = 0.0
        self.latest_jpeg: Optional[bytes] = None
        self.latest_telemetry: Dict[str, object] = {
            "status": "initializing",
            "fps": 0.0,
            "camera": "Raspberry Pi Camera Module 3 (IMX708)",
            "distance_type": "optical_monocular_estimate",
            "distance_note": "Monocular optical/PDAF estimate. Monocular calculation is an optical estimate, not direct 3D depth. Not for safety-critical collision avoidance.",
            "targets": [],
        }
        self._lock = threading.Lock()
        self.active_stream_clients: int = 0
        self.last_client_request_time: float = 0.0
        self.idle_timeout_seconds: float = 4.0

        # Graceful signal handling
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except Exception:
            pass

        self.model = self._load_yolo_model()

    def _handle_signal(self, signum, frame):
        print(f"\n[JARVIS] Received signal {signum}, initiating graceful camera shutdown...")
        self._running = False

    def _load_yolo_model(self):
        global YOLO, YOLO_AVAILABLE
        if YOLO is None:
            try:
                from ultralytics import YOLO as _YOLO
                YOLO = _YOLO
                YOLO_AVAILABLE = True
            except ImportError:
                YOLO_AVAILABLE = False
                print(
                    "[WARNING] `ultralytics` package not detected. "
                    "Install on Pi 5 with: pip install ultralytics"
                )
                return None

        model_path = self.args.model
        if not model_path or model_path.lower() in ("none", "false", "0", "disabled"):
            print("[JARVIS] Object detection model disabled.")
            return None

        # Auto-prefer pre-compiled NCNN model if available on Pi 5 ARM CPU
        if model_path.endswith(".pt"):
            ncnn_candidate = model_path.replace(".pt", "_ncnn_model")
            if os.path.isdir(ncnn_candidate):
                model_path = ncnn_candidate

        if self.args.export_ncnn and not model_path.endswith("_ncnn_model"):
            ncnn_dir = model_path.replace(".pt", "_ncnn_model")
            if not os.path.exists(ncnn_dir):
                print(f"[JARVIS] Exporting {model_path} to NCNN format for Pi 5 acceleration...")
                base_model = YOLO(model_path)
                base_model.export(format="ncnn", imgsz=self.args.imgsz)
            model_path = ncnn_dir

        print(f"[JARVIS] Loading Neural Object Detection Model: {model_path}")
        return YOLO(model_path)

    def _init_camera(self):
        """
        Initializes Raspberry Pi Camera Module 3 via Picamera2 with Continuous Phase
        Detection Autofocus (PDAF) and Fast AF Speed, falling back to V4L2 if needed.
        """
        if PICAMERA2_AVAILABLE and not self.args.use_v4l2:
            picam2 = Picamera2()
            target_fps = min(self.args.fps, 15) if self.model is not None else self.args.fps
            config = picam2.create_video_configuration(
                main={"size": (self.optics.width, self.optics.height), "format": "BGR888"},
                controls={"FrameRate": target_fps},
                buffer_count=4,
            )
            picam2.configure(config)
            picam2.start()

            # Enable Camera Module 3 Continuous Autofocus (PDAF)
            try:
                picam2.set_controls(
                    {
                        "AfMode": controls.AfModeEnum.Continuous,
                        "AfSpeed": controls.AfSpeedEnum.Fast,
                    }
                )
                print("[JARVIS] Camera Module 3 Continuous PDAF enabled.")
            except Exception as exc:
                print(f"[JARVIS] Note: Could not set PDAF controls ({exc}).")

            self.backend_name = "picamera2"
            return picam2, "picamera2"

        print("[JARVIS] Using OpenCV VideoCapture fallback.")
        self.backend_name = "opencv"
        cap = cv2.VideoCapture(self.args.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.optics.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.optics.height)
        cap.set(cv2.CAP_PROP_FPS, self.args.fps)
        return cap, "opencv"

    def process_frame(
        self, frame_bgr: np.ndarray, metadata: Dict[str, object], fps: float
    ) -> Tuple[np.ndarray, List[TrackedTarget]]:
        lens_pos = metadata.get("LensPosition", None)
        af_state = metadata.get("AfState", None)
        targets: List[TrackedTarget] = []

        if self.model is not None:
            results = self.model.track(
                frame_bgr,
                imgsz=self.args.imgsz,
                conf=self.args.conf,
                iou=0.45,
                agnostic_nms=True,
                persist=True,
                verbose=False,
            )
            if results and len(results) > 0:
                r = results[0]
                names = r.names
                boxes = r.boxes
                if boxes is not None and len(boxes) > 0:
                    xyxy = boxes.xyxy.cpu().numpy()
                    confs = boxes.conf.cpu().numpy()
                    clss = boxes.cls.cpu().numpy().astype(int)
                    ids = (
                        boxes.id.cpu().numpy().astype(int)
                        if boxes.id is not None
                        else np.arange(1, len(xyxy) + 1)
                    )
                    for i in range(len(xyxy)):
                        label = names.get(int(clss[i]), "object")
                        target = self.spatial_engine.process_detection(
                            track_id=int(ids[i]),
                            label=label,
                            confidence=float(confs[i]),
                            raw_bbox=tuple(xyxy[i]),
                            lens_position=float(lens_pos) if lens_pos is not None else None,
                            af_state=int(af_state) if af_state is not None else None,
                        )
                        targets.append(target)

        # Sort targets nearest-first so JARVIS prioritizes closest objects
        targets.sort(key=lambda t: t.distance_m)
        annotated = self.hud.render(frame_bgr, targets, fps, metadata)
        return annotated, targets

    def start_web_server(self) -> None:
        if not FLASK_AVAILABLE:
            print("[WARNING] Flask not installed; skipping web telemetry server.")
            return

        # Check if the requested port is already in use (e.g., code-server on 8080)
        port = self.args.port
        def is_port_in_use(p: int) -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                return s.connect_ex(("127.0.0.1", p)) == 0

        if is_port_in_use(port):
            orig_port = port
            for candidate in range(port + 1, port + 30):
                if not is_port_in_use(candidate):
                    port = candidate
                    break
            print(
                f"[JARVIS] Port {orig_port} is already in use by another program. "
                f"Auto-selected available port {port}."
            )
            self.args.port = port

        # Suppress verbose HTTP access logs from Werkzeug in console
        logging.getLogger("werkzeug").setLevel(logging.ERROR)

        app = Flask("JARVIS_Vision_Node")

        @app.route("/api/health")
        @app.route("/api/status")
        def api_health():
            with self._lock:
                self.last_client_request_time = time.time()
                last_ts = self.latest_telemetry.get("timestamp", 0)
                age_s = time.time() - last_ts if last_ts else None
                return jsonify({
                    "status": "ok",
                    "service": "JARVIS_Vision_Node",
                    "backend": self.backend_name,
                    "camera": "Raspberry Pi Camera Module 3 (IMX708)",
                    "fps": self.latest_telemetry.get("fps", 0.0),
                    "model": str(self.args.model),
                    "timestamp": time.time(),
                    "frame_age_s": round(age_s, 3) if age_s is not None else None,
                    "resolution": [self.optics.width, self.optics.height],
                    "target_count": len(self.latest_telemetry.get("targets", [])),
                    "active_stream_clients": self.active_stream_clients,
                    "mode": self.latest_telemetry.get("mode", "active"),
                })

        @app.route("/api/snapshot")
        @app.route("/api/capture")
        def api_snapshot():
            with self._lock:
                self.last_client_request_time = time.time()
                raw_jpg = self.latest_raw_jpeg or self.latest_jpeg
                ts = self.latest_raw_timestamp or time.time()
            if raw_jpg is None:
                return Response("No camera frame captured yet", status=503, mimetype="text/plain")
            resp = Response(raw_jpg, mimetype="image/jpeg")
            resp.headers["Content-Disposition"] = 'inline; filename="snapshot.jpg"'
            resp.headers["X-Capture-Timestamp"] = str(ts)
            resp.headers["X-Resolution"] = f"{self.optics.width}x{self.optics.height}"
            resp.headers["X-Camera-Model"] = "Sony IMX708"
            return resp

        @app.route("/api/snapshot/annotated")
        def api_snapshot_annotated():
            with self._lock:
                self.last_client_request_time = time.time()
                ann_jpg = self.latest_annotated_jpeg or self.latest_jpeg
                ts = self.latest_annotated_timestamp or time.time()
            if ann_jpg is None:
                return Response("No annotated frame captured yet", status=503, mimetype="text/plain")
            resp = Response(ann_jpg, mimetype="image/jpeg")
            resp.headers["Content-Disposition"] = 'inline; filename="snapshot_annotated.jpg"'
            resp.headers["X-Capture-Timestamp"] = str(ts)
            return resp

        @app.route("/api/detections")
        def api_detections():
            with self._lock:
                self.last_client_request_time = time.time()
                return jsonify(self.latest_telemetry)

        @app.route("/video_feed")
        def video_feed():
            def generate():
                with self._lock:
                    self.active_stream_clients += 1
                    self.last_client_request_time = time.time()
                try:
                    while True:
                        with self._lock:
                            self.last_client_request_time = time.time()
                            jpg = self.latest_jpeg
                        if jpg is not None:
                            yield (
                                b"--frame\r\n"
                                b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
                            )
                        time.sleep(0.033)
                finally:
                    with self._lock:
                        self.active_stream_clients = max(0, self.active_stream_clients - 1)

            return Response(
                generate(), mimetype="multipart/x-mixed-replace; boundary=frame"
            )

        @app.route("/")
        def index():
            return (
                "<html><body style='background:#0a0e12;color:#00d7f0;font-family:monospace;text-align:center;'>"
                "<h2>JARVIS OS // NEURAL VISION & SPATIAL DISTANCE STREAM</h2>"
                f"<p>Embed <code>/video_feed</code> and poll <code>/api/detections</code> in your JARVIS OS UI</p>"
                "<img src='/video_feed' style='max-width:95%;border:1px solid #00d7f0;border-radius:6px;'/>"
                "</body></html>"
            )

        bind_host = getattr(self.args, "host", "127.0.0.1")
        thread = threading.Thread(
            target=lambda: app.run(
                host=bind_host, port=self.args.port, debug=False, use_reloader=False
            ),
            daemon=True,
        )
        thread.start()
        print(
            f"[JARVIS] Web Stream & JSON Telemetry active at http://{bind_host}:{self.args.port} "
            f"(/video_feed, /api/snapshot, /api/health & /api/detections)"
        )

    def run(self) -> None:
        # Diagnostic single-image mode (for testing without camera hardware)
        if self.args.test_image:
            frame = cv2.imread(self.args.test_image)
            if frame is None:
                raise FileNotFoundError(f"Could not read test image: {self.args.test_image}")
            self.optics.height, self.optics.width = frame.shape[:2]
            sim_meta = {
                "ExposureTime": 32680,
                "AnalogueGain": 8.90,
                "DigitalGain": 1.01,
                "LensPosition": 0.95,
                "AfState": 2,
            }
            annotated, targets = self.process_frame(frame, sim_meta, fps=30.01)
            if self.args.output_image:
                cv2.imwrite(self.args.output_image, annotated)
                print(f"[JARVIS] Saved annotated diagnostic HUD to {self.args.output_image}")
            print(
                json.dumps(
                    [t.__dict__ for t in targets], indent=2
                )
            )
            return

        if self.args.web:
            self.start_web_server()

        # Write runtime service descriptor for JARVIS backend discovery
        runtime_descriptor = {
            "pid": os.getpid(),
            "host": getattr(self.args, "host", "127.0.0.1"),
            "port": self.args.port,
            "started_at": time.time(),
        }
        try:
            with open("/tmp/jarvis_camera_service.json", "w") as f:
                json.dump(runtime_descriptor, f)
        except Exception:
            pass

        cam, backend = self._init_camera()
        fps_ema = 30.0
        prev_time = time.perf_counter()
        consecutive_cam_fails = 0

        print("[JARVIS] Neural Vision Loop Running. Press 'q' in HUD window or Ctrl+C to exit.")
        try:
            while self._running:
                now_ts = time.time()
                with self._lock:
                    clients_active = self.active_stream_clients
                    last_req_ts = self.last_client_request_time

                is_active_demand = (not self.args.headless) or (clients_active > 0) or ((now_ts - last_req_ts) < self.idle_timeout_seconds)

                if not is_active_demand:
                    # Standby / Idle Mode: Sleep and capture low-rate frame without running YOLO neural inference
                    time.sleep(0.5)
                    if backend == "picamera2":
                        try:
                            frame_bgr = cam.capture_array("main")
                            metadata = cam.capture_metadata()
                            ok_raw, buf_raw = cv2.imencode(
                                ".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                            )
                            if ok_raw:
                                raw_bytes = buf_raw.tobytes()
                                with self._lock:
                                    self.latest_raw_jpeg = raw_bytes
                                    self.latest_raw_timestamp = time.time()
                                    self.latest_jpeg = raw_bytes
                                    self.latest_telemetry["mode"] = "standby_idle"
                                    self.latest_telemetry["fps"] = 0.0
                                    self.latest_telemetry["active_clients"] = 0
                                    self.latest_telemetry["timestamp"] = time.time()
                        except Exception:
                            pass
                    continue

                if backend == "picamera2":
                    frame_bgr = cam.capture_array("main")
                    metadata = cam.capture_metadata()
                else:
                    ok, frame_bgr = cam.read()
                    if not ok:
                        consecutive_cam_fails += 1
                        if consecutive_cam_fails == 60:
                            print(
                                "[WARNING] Cannot read frames via OpenCV VideoCapture fallback. "
                                "If using Raspberry Pi Camera Module 3, please ensure Picamera2 is used."
                            )
                        time.sleep(0.02)
                        continue
                    consecutive_cam_fails = 0
                    metadata = {
                        "ExposureTime": 32680,
                        "AnalogueGain": 8.90,
                        "DigitalGain": 1.01,
                        "LensPosition": 0.0,
                        "AfState": 0,
                    }

                now = time.perf_counter()
                dt = max(now - prev_time, 1e-4)
                prev_time = now
                fps_ema = 0.9 * fps_ema + 0.1 * (1.0 / dt)

                # Store fresh raw frame JPEG for snapshot capture
                if self.args.web:
                    ok_raw, buf_raw = cv2.imencode(
                        ".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92]
                    )
                    if ok_raw:
                        raw_bytes = buf_raw.tobytes()
                        with self._lock:
                            self.latest_raw_jpeg = raw_bytes
                            self.latest_raw_timestamp = time.time()

                annotated, targets = self.process_frame(frame_bgr, metadata, fps_ema)

                # Update web stream & JSON telemetry for JARVIS OS integration
                if self.args.web:
                    ok_jpg, buf = cv2.imencode(
                        ".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                    )
                    with self._lock:
                        if ok_jpg:
                            ann_bytes = buf.tobytes()
                            self.latest_annotated_jpeg = ann_bytes
                            self.latest_annotated_timestamp = time.time()
                            self.latest_jpeg = ann_bytes
                        self.latest_telemetry = {
                            "timestamp": time.time(),
                            "fps": round(fps_ema, 2),
                            "distance_type": "optical_monocular_estimate",
                            "distance_note": "Monocular optical/PDAF estimate. Monocular calculation is an optical estimate, not direct 3D depth. Not for safety-critical collision avoidance.",
                            "lens_position_dioptres": metadata.get("LensPosition"),
                            "af_state": metadata.get("AfState"),
                            "exposure_us": metadata.get("ExposureTime"),
                            "analogue_gain": metadata.get("AnalogueGain"),
                            "targets": [
                                {
                                    "id": t.track_id,
                                    "label": t.label,
                                    "confidence": round(t.confidence, 3),
                                    "distance_m": t.distance_m,
                                    "distance_cm": int(t.distance_m * 100),
                                    "distance_type": "optical_estimate",
                                    "is_direct_depth": False,
                                    "coords_3d_m": {
                                        "x": t.coords_3d[0],
                                        "y": t.coords_3d[1],
                                        "z": t.coords_3d[2],
                                    },
                                    "bearing_deg": {
                                        "azimuth": t.bearing_deg[0],
                                        "elevation": t.bearing_deg[1],
                                    },
                                    "zone": t.zone,
                                    "method": t.method,
                                    "bbox": list(t.bbox),
                                }
                                for t in targets
                            ],
                        }

                if not self.args.headless:
                    try:
                        cv2.imshow("JARVIS OS // Neural Vision & Distance HUD", annotated)
                        if (cv2.waitKey(1) & 0xFF) == ord("q"):
                            break
                    except cv2.error as e:
                        print(
                            f"[JARVIS] Local display window error ({e}). "
                            "Switching to headless mode (stream available via web)."
                        )
                        self.args.headless = True

        except KeyboardInterrupt:
            print("\n[JARVIS] Shutting down Neural Vision HUD...")
        finally:
            try:
                if os.path.exists("/tmp/jarvis_camera_service.json"):
                    os.remove("/tmp/jarvis_camera_service.json")
            except Exception:
                pass
            if backend == "picamera2":
                try:
                    cam.stop()
                except Exception:
                    pass
                try:
                    cam.close()
                except Exception:
                    pass
            else:
                cam.release()
            cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="JARVIS OS ? Raspberry Pi 5 + Camera Module 3 Object Detection & Distance Engine"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n.pt",
        help="Ultralytics YOLO model weight path (e.g. yolo11n.pt or yolov8n.pt)",
    )
    parser.add_argument(
        "--export-ncnn",
        action="store_true",
        help="Export and run NCNN format for maximum FPS on Raspberry Pi 5 CPU",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image resolution (use 416 or 640 on Pi 5)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.40,
        help="Minimum object detection confidence threshold",
    )
    parser.add_argument("--width", type=int, default=1280, help="Camera capture width")
    parser.add_argument("--height", type=int, default=720, help="Camera capture height")
    parser.add_argument("--fps", type=int, default=30, help="Target camera frame rate")
    parser.add_argument(
        "--wide",
        action="store_true",
        help="Set if using Camera Module 3 Wide (102° HFOV, 2.75mm focal length)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        default=True,
        help="Enable MJPEG stream (/video_feed) and JSON API (/api/detections) for JARVIS OS",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind HTTP server (default: 127.0.0.1 loopback for security)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8082,
        help="Port for JARVIS Vision HTTP/MJPEG server (default: 8082, alongside JARVIS OS on 8000 and code-server on 8080)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Disable local OpenCV GUI window (stream via HTTP only)",
    )
    parser.add_argument(
        "--use-v4l2",
        action="store_true",
        help="Force OpenCV V4L2 capture instead of Picamera2",
    )
    parser.add_argument(
        "--camera-index", type=int, default=0, help="V4L2 camera index if using fallback"
    )
    parser.add_argument(
        "--test-image",
        type=str,
        default=None,
        help="Run diagnostic HUD & distance test on a static image file",
    )
    parser.add_argument(
        "--output-image",
        type=str,
        default=None,
        help="Output path when running with --test-image",
    )
    return parser.parse_args()


if __name__ == "__main__":
    JarvisVisionApp(parse_args()).run()
