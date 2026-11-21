"""Unit tests for Module 36 VisionEngine (image header inspection, hit-testing, grounded Q&A)."""

from __future__ import annotations

import base64
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from modules.module_36_screen_vision_assistant.backend.app.config import VisionConfig
from modules.module_36_screen_vision_assistant.backend.services.vision_engine import VisionEngine, VisionError


def _make_png_b64(width: int = 320, height: int = 200) -> str:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + (b"\x00\x00\x00" * width) for _ in range(height))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 1)) + chunk(b"IEND", b"")
    return base64.b64encode(png).decode("ascii")


class TestVisionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = VisionConfig(db_path=str(Path(self._tmp.name) / "vision.db"))
        self.engine = VisionEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_real_png_header_inspection_and_hit_test(self) -> None:
        cap = self.engine.create_capture(
            {
                "title": "Desktop Frame",
                "source": "hdmi_0",
                "image_base64": _make_png_b64(320, 200),
                "ocr_text": "Save File | Cancel",
                "elements": [
                    {"element_id": "panel", "role": "panel", "label": "Dialog", "text": "", "x": 10, "y": 10, "width": 300, "height": 180, "confidence": 0.95},
                    {"element_id": "btn_save", "role": "button", "label": "Save File", "text": "Save", "x": 40, "y": 40, "width": 100, "height": 40, "confidence": 0.99},
                ],
            }
        )
        self.assertEqual(cap["image_format"], "PNG")
        self.assertEqual(cap["width"], 320)
        self.assertEqual(cap["height"], 200)
        self.assertGreater(cap["byte_size"], 50)
        self.assertEqual(len(cap["sha256"]), 64)

        hit = self.engine.hit_test(cap["capture_id"], 60, 55)
        self.assertEqual(hit["count"], 2)
        # Innermost (smallest area) element must come first
        self.assertEqual(hit["hits"][0]["element_id"], "btn_save")
        self.assertEqual(hit["hits"][1]["element_id"], "panel")

    def test_validation_rejects_bad_image_and_out_of_bounds_boxes(self) -> None:
        with self.assertRaises(VisionError) as ctx1:
            self.engine.create_capture({"title": "Bad", "image_base64": "not-valid-base64!!!"})
        self.assertEqual(ctx1.exception.code, "INVALID_BASE64_IMAGE")
        self.assertEqual(ctx1.exception.status_code, 422)

        with self.assertRaises(VisionError) as ctx2:
            self.engine.create_capture(
                {
                    "title": "Bad Format",
                    "image_base64": base64.b64encode(b"PLAIN_TEXT_NOT_AN_IMAGE").decode("ascii"),
                }
            )
        self.assertEqual(ctx2.exception.code, "UNSUPPORTED_IMAGE_FORMAT")

        with self.assertRaises(VisionError) as ctx3:
            self.engine.create_capture(
                {
                    "title": "Overflow",
                    "width": 200,
                    "height": 100,
                    "elements": [
                        {"element_id": "e1", "role": "button", "label": "Too Wide", "x": 150, "y": 10, "width": 80, "height": 20}
                    ],
                }
            )
        self.assertEqual(ctx3.exception.code, "BOUNDING_BOX_OUT_OF_BOUNDS")

    def test_grounded_screen_qa_matches_elements_and_ocr(self) -> None:
        cap = self.engine.create_capture(
            {
                "title": "Build Console",
                "width": 1280,
                "height": 720,
                "ocr_text": "Pipeline status: GREEN | Thermal 46C",
                "elements": [
                    {"element_id": "btn_retry", "role": "button", "label": "Retry Build", "text": "Retry", "x": 100, "y": 100, "width": 140, "height": 40, "confidence": 0.99}
                ],
            }
        )
        qa = self.engine.query_capture(cap["capture_id"], "Where is Retry Build?")
        self.assertEqual(len(qa["matched_elements"]), 1)
        self.assertIn("Retry Build", qa["answer"])

        qa_ocr = self.engine.query_capture(cap["capture_id"], "What is thermal status?")
        self.assertEqual(len(qa_ocr["matched_elements"]), 0)
        self.assertIn("Thermal 46C", qa_ocr["answer"])
        self.assertFalse(self.engine.get_status()["simulated"])


if __name__ == "__main__":
    unittest.main()
