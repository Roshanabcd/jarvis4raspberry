"""
JARVIS OS — Object Detection Subsystem.
Powered by YOLOv8n ONNX model executed via OpenCV DNN.

Features:
- Fast object detection on Raspberry Pi 5 ARM64 CPU (~700-900ms)
- 80 COCO object classes (person, bottle, chair, laptop, phone, cup, etc.)
- Strict bounding box normalization and scaling back to original image resolution
- Non-Maximum Suppression (NMS) for clean single-box detections
- Bounding box rendering with distinct colors and confidence labels
- Zero external Python dependencies beyond OpenCV and NumPy
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger("JARVIS.Vision.ObjectDetector")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "vision"
YOLOV8N_MODEL = MODELS_DIR / "yolov8n.onnx"

COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
    "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

# Color palette for bounding boxes (BGR format)
PALETTE = [
    (0, 255, 255),    # Cyan
    (0, 255, 0),      # Green
    (255, 128, 0),    # Orange/Blue
    (255, 0, 128),    # Purple/Magenta
    (0, 165, 255),    # Orange
    (255, 255, 0),    # Bright Cyan/Yellow
    (50, 205, 50),    # Lime Green
    (238, 130, 238),  # Violet
]


class ObjectDetector:
    """YOLOv8n ONNX object detection engine running on OpenCV DNN."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_path: Optional[Union[str, Path]] = None):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._model_path = Path(model_path) if model_path else YOLOV8N_MODEL
        self._net: Optional[cv2.dnn.Net] = None
        self._input_size = (640, 640)
        self._conf_threshold = 0.35
        self._nms_threshold = 0.45

        self._load_model()
        self._initialized = True

    def _load_model(self) -> None:
        """Load YOLOv8n ONNX model into OpenCV DNN."""
        if not self._model_path.exists():
            logger.error("YOLOv8n model not found at %s", self._model_path)
            return

        try:
            net = cv2.dnn.readNetFromONNX(str(self._model_path))
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            self._net = net
            logger.info("YOLOv8n object detection model successfully loaded from %s", self._model_path)
        except Exception as e:
            logger.error("Failed to load YOLOv8n ONNX model: %s", e)
            self._net = None

    @property
    def is_ready(self) -> bool:
        return self._net is not None

    def detect_objects(
        self,
        image_input: Union[str, Path, np.ndarray],
        conf_threshold: Optional[float] = None,
        nms_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run object detection on an image.

        Args:
            image_input: Filepath or BGR NumPy array
            conf_threshold: Minimum confidence score (defaults to 0.35)
            nms_threshold: IOU threshold for Non-Maximum Suppression (defaults to 0.45)

        Returns:
            Dictionary with:
            - success: bool
            - count: int (total objects found)
            - objects: list of dicts {label, confidence, bbox: {x, y, width, height}}
            - labels: list of detected class names
            - inference_ms: float
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": f"YOLOv8n model not loaded from {self._model_path}",
                "count": 0,
                "objects": [],
                "labels": [],
                "inference_ms": 0.0,
            }

        conf_thresh = conf_threshold if conf_threshold is not None else self._conf_threshold
        nms_thresh = nms_threshold if nms_threshold is not None else self._nms_threshold

        # Load image
        img: Optional[np.ndarray] = None
        image_path: Optional[str] = None
        if isinstance(image_input, (str, Path)):
            image_path = str(image_input)
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}",
                    "count": 0,
                    "objects": [],
                    "labels": [],
                    "inference_ms": 0.0,
                }
            img = cv2.imread(image_path)
        elif isinstance(image_input, np.ndarray):
            img = image_input

        if img is None:
            return {
                "success": False,
                "error": "Failed to decode image input",
                "count": 0,
                "objects": [],
                "labels": [],
                "inference_ms": 0.0,
            }

        orig_h, orig_w = img.shape[:2]
        if orig_h == 0 or orig_w == 0:
            return {
                "success": False,
                "error": "Image has invalid dimensions (0x0)",
                "count": 0,
                "objects": [],
                "labels": [],
                "inference_ms": 0.0,
            }

        t0 = time.perf_counter()

        # Prepare YOLOv8 input blob: normalize to 1/255.0, resize to 640x640, BGR->RGB
        blob = cv2.dnn.blobFromImage(
            img,
            scalefactor=1.0 / 255.0,
            size=self._input_size,
            mean=[0, 0, 0],
            swapRB=True,
            crop=False,
        )

        self._net.setInput(blob)
        # Output shape is [1, 84, 8400]
        output = self._net.forward()
        # Transpose to [8400, 84]
        predictions = np.squeeze(output, axis=0).T

        boxes = []
        confidences = []
        class_ids = []

        x_factor = orig_w / float(self._input_size[0])
        y_factor = orig_h / float(self._input_size[1])

        for row in predictions:
            # First 4 values are cx, cy, w, h in 640x640 coordinate space
            scores = row[4:]
            class_id = int(np.argmax(scores))
            confidence = float(scores[class_id])

            if confidence >= conf_thresh:
                cx, cy, w, h = row[0:4]
                # Scale back to original image dimensions
                left = int((cx - 0.5 * w) * x_factor)
                top = int((cy - 0.5 * h) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)

                # Clamp to image boundaries
                left = max(0, min(left, orig_w - 1))
                top = max(0, min(top, orig_h - 1))
                width = max(1, min(width, orig_w - left))
                height = max(1, min(height, orig_h - top))

                boxes.append([left, top, width, height])
                confidences.append(confidence)
                class_ids.append(class_id)

        # Apply Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_thresh, nms_thresh)

        detected_objects: List[Dict[str, Any]] = []
        detected_labels: List[str] = []

        if len(indices) > 0:
            for idx in indices:
                # In OpenCV 5.0, idx is often an integer or 1D scalar
                i = int(idx[0]) if hasattr(idx, "__len__") else int(idx)
                cid = class_ids[i]
                label = COCO_CLASSES[cid] if cid < len(COCO_CLASSES) else f"object_{cid}"
                conf = round(confidences[i], 3)
                box = boxes[i]

                detected_objects.append({
                    "label": label,
                    "confidence": conf,
                    "class_id": cid,
                    "bbox": {
                        "x": box[0],
                        "y": box[1],
                        "width": box[2],
                        "height": box[3],
                    },
                })
                if label not in detected_labels:
                    detected_labels.append(label)

        # Sort detections by confidence descending
        detected_objects.sort(key=lambda x: x["confidence"], reverse=True)
        inference_ms = round((time.perf_counter() - t0) * 1000.0, 1)

        logger.info(
            "Detected %d objects in %s ms (labels: %s)",
            len(detected_objects),
            inference_ms,
            detected_labels,
        )

        return {
            "success": True,
            "count": len(detected_objects),
            "objects": detected_objects,
            "labels": detected_labels,
            "inference_ms": inference_ms,
            "image_path": image_path,
        }

    def draw_bounding_boxes(
        self,
        image_input: Union[str, Path, np.ndarray],
        detections: List[Dict[str, Any]],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Optional[np.ndarray]:
        """
        Draw visual bounding boxes and labels onto an image and optionally save to disk.

        Args:
            image_input: Filepath or BGR NumPy array
            detections: List of detections from detect_objects()
            output_path: Filepath to save annotated image (optional)

        Returns:
            Annotated BGR NumPy array or None on failure
        """
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))
        elif isinstance(image_input, np.ndarray):
            img = image_input.copy()
        else:
            return None

        if img is None:
            return None

        for item in detections:
            bbox = item.get("bbox", {})
            x = int(bbox.get("x", 0))
            y = int(bbox.get("y", 0))
            w = int(bbox.get("width", 0))
            h = int(bbox.get("height", 0))
            label = str(item.get("label", "object"))
            conf = float(item.get("confidence", 0.0))
            cid = int(item.get("class_id", 0))

            color = PALETTE[cid % len(PALETTE)]

            # Draw rectangle
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)

            # Draw label banner
            text = f"{label} {int(conf * 100)}%"
            (text_w, text_h), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            banner_top = max(0, y - text_h - 6)
            cv2.rectangle(
                img,
                (x, banner_top),
                (x + text_w + 6, banner_top + text_h + 6),
                color,
                -1,
            )
            # Text inside banner (black or white for contrast)
            cv2.putText(
                img,
                text,
                (x + 3, banner_top + text_h + 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_p), img)
            logger.info("Saved annotated object detection image to %s", out_p)

        return img


# Global singleton instance
object_detector = ObjectDetector()
