"""End-to-end tests for JARVIS Handwritten to Text Converter."""

from __future__ import annotations

import base64
import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_handwriting_ocr.app import create_app
from jarvis_handwriting_ocr.config import HandwritingOCRConfig
from jarvis_handwriting_ocr.postprocessor import clean_ocr_text


def _make_sample_png_base64() -> str:
    """Generate a valid PNG image with clean dark text on white background."""
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (480, 120), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((24, 44), "JARVIS OCR TEST 2026", fill=(0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        # 1x1 white PNG fallback if Pillow is absent
        tiny_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?"
            b"\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return "data:image/png;base64," + base64.b64encode(tiny_png).decode("ascii")


class TestHandwritingOCR(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_ocr.db"
        cfg = HandwritingOCRConfig(db_path=db_path)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/handwriting-ocr")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Handwritten to Text Converter", ui.text)

        health = self.client.get("/api/handwriting-ocr/health")
        self.assertEqual(health.status_code, 200)
        self.assertIn("local_tesseract", health.json()["backends"])

    def test_postprocessor_cleanup(self) -> None:
        raw = "Hand-\nwritten   notes\r\n\r\n\r\nfor   JARVIS  OS"
        cleaned = clean_ocr_text(raw)
        self.assertEqual(cleaned, "Handwritten notes\n\nfor JARVIS OS")

    def test_convert_history_export_and_delete(self) -> None:
        sample_b64 = _make_sample_png_base64()
        conv = self.client.post(
            "/api/handwriting-ocr/convert",
            json={
                "filename": "notes_page1.png",
                "image_base64": sample_b64,
                "language": "eng",
                "preprocess": True,
                "cleanup_text": True,
            },
        )
        self.assertEqual(conv.status_code, 200)
        data = conv.json()
        self.assertIn(data["engine_used"], {"local_tesseract", "diagnostic_no_ocr_backend", "openrouter_vision_llm"})
        cid = data["id"]

        # History contains conversion
        hist = self.client.get("/api/handwriting-ocr/history")
        self.assertEqual(hist.status_code, 200)
        self.assertEqual(hist.json()["total"], 1)

        # Export as Markdown & TXT
        md_exp = self.client.get(f"/api/handwriting-ocr/history/{cid}/export?fmt=md")
        self.assertEqual(md_exp.status_code, 200)
        self.assertIn("notes_page1.png", md_exp.text)

        # Delete conversion
        del_resp = self.client.delete(f"/api/handwriting-ocr/history/{cid}")
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(self.client.get("/api/handwriting-ocr/history").json()["total"], 0)


if __name__ == "__main__":
    unittest.main()
