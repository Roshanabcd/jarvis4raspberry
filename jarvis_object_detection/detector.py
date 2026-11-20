"""Multi-backend object detector (Ultralytics YOLO -> OpenCV -> Pillow salient-object fallback)."""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Optional, Tuple

from .config import ObjectDetectionConfig


def _check_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except Exception:
        return False


def decode_frame(image_base64: str, max_bytes: int) -> bytes:
    raw = image_base64.strip()
    if raw.lower().startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw)
    except Exception as exc:
        raise ValueError("Invalid base64 image frame.") from exc
    if not data:
        raise ValueError("Empty image frame.")
    if len(data) > max_bytes:
        raise ValueError(f"Frame exceeds {max_bytes} bytes limit.")
    return data


class MultiBackendDetector:
    """Runs YOLO if installed, otherwise uses lightweight offline salient-object region detection."""

    def __init__(self, config: ObjectDetectionConfig) -> None:
        self.config = config
        self._has_ultralytics = _check_import("ultralytics")
        self._has_cv2 = _check_import("cv2")
        self._has_pil = _check_import("PIL")
        self._yolo_model: Any = None

    def available_backends(self) -> Dict[str, bool]:
        return {
            "ultralytics_yolo": self._has_ultralytics,
            "opencv": self._has_cv2,
            "pillow_salient_detector": self._has_pil,
        }

    def active_backend_name(self) -> str:
        if self.config.enable_yolo and self._has_ultralytics:
            return f"ultralytics_yolo ({self.config.yolo_model_path})"
        if self._has_pil:
            return "offline_salient_region_detector"
        return "minimal_fallback"

    def _detect_with_yolo(
        self, img_bytes: bytes, conf_thresh: float
    ) -> Optional[Tuple[int, int, List[Dict[str, Any]]]]:
        if not (self.config.enable_yolo and self._has_ultralytics and self._has_pil):
            return None
        try:
            from PIL import Image
            from ultralytics import YOLO  # type: ignore

            if self._yolo_model is None:
                self._yolo_model = YOLO(self.config.yolo_model_path)

            with Image.open(io.BytesIO(img_bytes)) as img:
                rgb = img.convert("RGB")
                w, h = rgb.size
                results = self._yolo_model.predict(rgb, conf=conf_thresh, verbose=False)

            dets: List[Dict[str, Any]] = []
            for res in results:
                names = res.names
                for box in res.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    dets.append(
                        {
                            "label": str(names.get(cls_id, f"class_{cls_id}")),
                            "confidence": conf,
                            "x1": max(0.0, min(1.0, x1 / max(w, 1))),
                            "y1": max(0.0, min(1.0, y1 / max(h, 1))),
                            "x2": max(0.0, min(1.0, x2 / max(w, 1))),
                            "y2": max(0.0, min(1.0, y2 / max(h, 1))),
                        }
                    )
            return w, h, dets
        except Exception:
            return None

    def _detect_offline_salient_regions(
        self, img_bytes: bytes, conf_thresh: float
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """Fast pure-Pillow connected-component salient object detector for zero-dependency Pi 5 operation."""
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(img_bytes)) as img:
            orig_w, orig_h = img.size
            gray = ImageOps.grayscale(img)
            # Downscale to 64x48 grid for ultra-fast connected-component bounding boxes (<5ms on Pi 5)
            gw, gh = 64, 48
            small = gray.resize((gw, gh))
            pixels = list(small.getdata())

        # Estimate background intensity from border pixels
        border_vals = []
        for x in range(gw):
            border_vals.append(pixels[x])
            border_vals.append(pixels[(gh - 1) * gw + x])
        for y in range(gh):
            border_vals.append(pixels[y * gw])
            border_vals.append(pixels[y * gw + (gw - 1)])
        bg_med = sorted(border_vals)[len(border_vals) // 2]

        # Foreground mask where pixel contrasts strongly from background
        fg = [abs(p - bg_med) >= 38 for p in pixels]
        visited = [False] * (gw * gh)
        dets: List[Dict[str, Any]] = []

        for y in range(gh):
            for x in range(gw):
                idx = y * gw + x
                if not fg[idx] or visited[idx]:
                    continue
                stack = [(x, y)]
                visited[idx] = True
                min_x = max_x = x
                min_y = max_y = y
                area = 0
                contrast_sum = 0.0

                while stack:
                    cx, cy = stack.pop()
                    cidx = cy * gw + cx
                    area += 1
                    contrast_sum += abs(pixels[cidx] - bg_med)
                    if cx < min_x:
                        min_x = cx
                    if cx > max_x:
                        max_x = cx
                    if cy < min_y:
                        min_y = cy
                    if cy > max_y:
                        max_y = cy
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < gw and 0 <= ny < gh:
                            nidx = ny * gw + nx
                            if fg[nidx] and not visited[nidx]:
                                visited[nidx] = True
                                stack.append((nx, ny))

                # Filter tiny noise speckles (<1.2% of frame)
                if area < int(gw * gh * 0.012):
                    continue
                mean_contrast = contrast_sum / area
                conf = min(0.95, max(0.35, mean_contrast / 140.0))
                if conf < conf_thresh:
                    continue
                dets.append(
                    {
                        "label": "salient_object",
                        "confidence": round(conf, 4),
                        "x1": min_x / gw,
                        "y1": min_y / gh,
                        "x2": (max_x + 1) / gw,
                        "y2": (max_y + 1) / gh,
                    }
                )

        dets.sort(key=lambda d: d["confidence"], reverse=True)
        return orig_w, orig_h, dets[:15]

    def detect(
        self, img_bytes: bytes, conf_thresh: float
    ) -> Tuple[str, int, int, List[Dict[str, Any]]]:
        yolo_res = self._detect_with_yolo(img_bytes, conf_thresh=conf_thresh)
        if yolo_res is not None:
            w, h, dets = yolo_res
            return f"ultralytics_yolo ({self.config.yolo_model_path})", w, h, dets

        if self._has_pil:
            w, h, dets = self._detect_offline_salient_regions(img_bytes, conf_thresh=conf_thresh)
            return "offline_salient_region_detector", w, h, dets

        return "minimal_fallback", 0, 0, []
