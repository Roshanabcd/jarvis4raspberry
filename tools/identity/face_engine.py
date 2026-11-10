"""
JARVIS OS — Face Detection and Recognition Engine.
Powered by native OpenCV DNN YuNet (Face Detection) and SFace (Face Recognition).

Features:
- Sub-100ms face detection on Raspberry Pi 5 ARM64 CPU
- 128-dimensional facial embedding extraction via SFace
- Cosine similarity matching with calibrated thresholds
- Rejection of low-confidence and unknown faces
- Zero heavy dependencies (pure OpenCV 5.0 + NumPy)
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger("JARVIS.Identity.FaceEngine")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "vision"
YUNET_MODEL = MODELS_DIR / "face_detection_yunet.onnx"
SFACE_MODEL = MODELS_DIR / "face_recognition_sface.onnx"

# Official OpenCV SFace calibrated thresholds
COSINE_SIMILARITY_THRESHOLD = 0.363  # standard matching threshold
COSINE_HIGH_CONFIDENCE_THRESHOLD = 0.45  # high confidence match


class FaceEngine:
    """Manages face detection, alignment, feature extraction, and identity matching."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._detector: Optional[cv2.FaceDetectorYN] = None
        self._recognizer: Optional[cv2.FaceRecognizerSF] = None
        self._detector_size = (640, 480)
        self._score_threshold = 0.65
        self._nms_threshold = 0.30
        self._top_k = 5

        self._load_models()
        self._initialized = True

    def _load_models(self) -> None:
        """Load YuNet detector and SFace recognizer into OpenCV DNN."""
        if not YUNET_MODEL.exists():
            logger.error("YuNet model not found at %s", YUNET_MODEL)
            return
        if not SFACE_MODEL.exists():
            logger.error("SFace model not found at %s", SFACE_MODEL)
            return

        try:
            self._detector = cv2.FaceDetectorYN.create(
                model=str(YUNET_MODEL),
                config="",
                input_size=self._detector_size,
                score_threshold=self._score_threshold,
                nms_threshold=self._nms_threshold,
                top_k=self._top_k,
            )
            self._recognizer = cv2.FaceRecognizerSF.create(
                model=str(SFACE_MODEL),
                config="",
            )
            logger.info("FaceEngine models successfully loaded (YuNet + SFace).")
        except Exception as e:
            logger.error("Failed to initialize FaceEngine models: %s", e)

    @property
    def is_ready(self) -> bool:
        return self._detector is not None and self._recognizer is not None

    def _read_image(self, image_input: Union[str, Path, np.ndarray]) -> Optional[np.ndarray]:
        """Load image input as BGR NumPy array."""
        if isinstance(image_input, (str, Path)):
            path_str = str(image_input)
            if not os.path.exists(path_str):
                logger.error("Image file not found: %s", path_str)
                return None
            img = cv2.imread(path_str)
            if img is None:
                logger.error("Failed to decode image from %s", path_str)
            return img
        elif isinstance(image_input, np.ndarray):
            return image_input
        return None

    def detect_faces(
        self, image_input: Union[str, Path, np.ndarray]
    ) -> List[Dict[str, Any]]:
        """
        Detect all faces in the image.
        Returns list of detected face dictionaries:
        [{'bbox': {'x': int, 'y': int, 'width': int, 'height': int},
          'confidence': float,
          'landmarks': List[Tuple[float, float]],
          'raw_face': np.ndarray}]
        """
        if not self.is_ready:
            self._load_models()
            if not self.is_ready:
                return []

        img = self._read_image(image_input)
        if img is None:
            return []

        h, w = img.shape[:2]
        # Dynamically set input size for detector
        self._detector.setInputSize((w, h))

        try:
            ret, faces = self._detector.detect(img)
            if faces is None or len(faces) == 0:
                return []

            results = []
            for face in faces:
                # YuNet format: [x, y, w, h, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, score]
                x, y, bw, bh = face[0:4].astype(int)
                score = float(face[-1])
                landmarks = [
                    (float(face[4]), float(face[5])),   # right eye
                    (float(face[6]), float(face[7])),   # left eye
                    (float(face[8]), float(face[9])),   # nose tip
                    (float(face[10]), float(face[11])), # right mouth corner
                    (float(face[12]), float(face[13])), # left mouth corner
                ]

                results.append({
                    "bbox": {
                        "x": max(0, int(x)),
                        "y": max(0, int(y)),
                        "width": int(bw),
                        "height": int(bh),
                    },
                    "confidence": round(score, 3),
                    "landmarks": landmarks,
                    "raw_face": face,
                })

            return results
        except Exception as e:
            logger.error("Error during face detection: %s", e)
            return []

    def extract_embedding(
        self,
        image_input: Union[str, Path, np.ndarray],
        face_info: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[float]]:
        """
        Extract 128-dimensional L2-normalized facial embedding using SFace.
        If face_info is None, detects the primary face automatically.
        """
        if not self.is_ready:
            self._load_models()
            if not self.is_ready:
                return None

        img = self._read_image(image_input)
        if img is None:
            return None

        if face_info is None:
            detected = self.detect_faces(img)
            if not detected:
                logger.info("No face detected for embedding extraction.")
                return None
            # Choose highest confidence face
            face_info = max(detected, key=lambda f: f["confidence"])

        raw_face = face_info.get("raw_face")
        if raw_face is None:
            return None

        try:
            aligned_face = self._recognizer.alignCrop(img, raw_face)
            feature = self._recognizer.feature(aligned_face)
            # Flatten to 128-element list
            feature_vec = feature.flatten().tolist()
            return feature_vec
        except Exception as e:
            logger.error("Error extracting facial embedding: %s", e)
            return None

    def compare_embeddings(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray],
    ) -> Tuple[bool, float]:
        """
        Compute cosine similarity between two 128-D facial feature embeddings.
        Returns: (is_match: bool, similarity_score: float)
        """
        try:
            vec1 = np.array(embedding1, dtype=np.float32).reshape(1, -1)
            vec2 = np.array(embedding2, dtype=np.float32).reshape(1, -1)

            if self._recognizer is not None:
                sim = self._recognizer.match(vec1, vec2, cv2.FaceRecognizerSF_FR_COSINE)
            else:
                # Manual cosine similarity fallback
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                sim = float(np.dot(vec1, vec2.T) / (norm1 * norm2))

            sim = float(sim)
            is_match = sim >= COSINE_SIMILARITY_THRESHOLD
            return is_match, round(sim, 4)
        except Exception as e:
            logger.error("Error comparing facial embeddings: %s", e)
            return False, 0.0


face_engine = FaceEngine()
