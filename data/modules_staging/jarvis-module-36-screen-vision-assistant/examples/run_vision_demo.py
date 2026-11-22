"""Runnable CLI demo for JARVIS Module 36 — Screen Vision Assistant."""

from __future__ import annotations

import base64
import json
import struct
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import VisionConfig
from backend.services.vision_engine import VisionEngine


def _make_sample_png(width: int = 640, height: int = 360) -> str:
    """Create a minimal valid PNG binary in memory (zero external deps)."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw_scanlines = b"".join(b"\x00" + (b"\x05\x0b\x16" * width) for _ in range(height))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw_scanlines, 1)) + chunk(b"IEND", b"")
    return base64.b64encode(png).decode("ascii")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = VisionConfig(db_path=str(Path(tmp) / "demo_vision.db"))
        engine = VisionEngine(config=cfg)
        cap = engine.create_capture(
            {
                "title": "JARVIS Telemetry HUD",
                "source": "hdmi_primary",
                "image_base64": _make_sample_png(640, 360),
                "ocr_text": "JARVIS OS | Deploy | CPU 21% | Thermal OK",
                "elements": [
                    {"element_id": "btn_deploy", "role": "button", "label": "Deploy", "text": "Deploy", "x": 40, "y": 40, "width": 160, "height": 50, "confidence": 0.99},
                    {"element_id": "card_cpu", "role": "metric", "label": "CPU Load", "text": "CPU 21%", "x": 240, "y": 40, "width": 200, "height": 90, "confidence": 0.97},
                ],
            }
        )
        hit = engine.hit_test(cap["capture_id"], 100, 60)
        qa = engine.query_capture(cap["capture_id"], "Where is the Deploy button?")
        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "image_format": cap["image_format"],
                    "dimensions": [cap["width"], cap["height"]],
                    "hit_ids": [h["element_id"] for h in hit["hits"]],
                    "qa_answer": qa["answer"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
