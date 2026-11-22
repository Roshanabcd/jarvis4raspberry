"""Local Screen Vision Inspection, Bounding-Box Hit Testing & Grounded Q&A Engine (Module 36)."""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
import struct
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from modules.module_36_screen_vision_assistant.backend.app.config import VisionConfig
from modules.module_36_screen_vision_assistant.backend.models.database import VisionDB, utc_now_iso


class VisionError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def inspect_image_bytes(raw: bytes) -> Tuple[str, int, int]:
    """Inspect real PNG, BMP, or JPEG headers using stdlib struct."""
    if len(raw) >= 24 and raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[12:16] == b"IHDR":
        width, height = struct.unpack(">II", raw[16:24])
        return ("PNG", int(width), int(height))

    if len(raw) >= 26 and raw[:2] == b"BM":
        width, height = struct.unpack("<ii", raw[18:26])
        return ("BMP", abs(int(width)), abs(int(height)))

    if len(raw) >= 4 and raw[:2] == b"\xff\xd8":
        idx = 2
        while idx + 4 < len(raw):
            if raw[idx] != 0xFF:
                idx += 1
                continue
            marker = raw[idx + 1]
            if marker in (0xC0, 0xC1, 0xC2) and idx + 9 <= len(raw):
                height, width = struct.unpack(">HH", raw[idx + 5 : idx + 9])
                return ("JPEG", int(width), int(height))
            if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
                idx += 2
            else:
                seg_len = struct.unpack(">H", raw[idx + 2 : idx + 4])[0]
                if seg_len < 2:
                    break
                idx += 2 + seg_len
        raise VisionError("UNSUPPORTED_JPEG_HEADER", "Could not extract SOF dimensions from JPEG stream.", 422)

    raise VisionError("UNSUPPORTED_IMAGE_FORMAT", "Image must be a valid PNG, BMP, or JPEG binary.", 422)


def _tokenize(text: str) -> List[str]:
    return [tok for tok in re.findall(r"[a-z0-9_]+", text.lower()) if len(tok) >= 2]


class VisionEngine:
    adapter_name: str = "local_screen_vision_engine"
    is_simulated: bool = False

    def __init__(self, config: Optional[VisionConfig] = None, db: Optional[VisionDB] = None) -> None:
        self.config = config or VisionConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or VisionDB(self.config.db_path)
        self._started_at = time.monotonic()

    def _validate_elements(self, elements: List[Dict[str, Any]], width: int, height: int) -> None:
        seen = set()
        for el in elements:
            eid = el["element_id"]
            if eid in seen:
                raise VisionError("DUPLICATE_ELEMENT_ID", f"Duplicate element_id '{eid}'.", 422)
            seen.add(eid)
            if el["x"] + el["width"] > width or el["y"] + el["height"] > height:
                raise VisionError(
                    "BOUNDING_BOX_OUT_OF_BOUNDS",
                    f"Element '{eid}' exceeds capture dimensions ({width}x{height}).",
                    422,
                )

    def create_capture(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        image_b64 = payload.get("image_base64")
        if image_b64:
            if "," in image_b64 and image_b64.strip().startswith("data:"):
                image_b64 = image_b64.split(",", 1)[1]
            try:
                raw = base64.b64decode(image_b64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise VisionError("INVALID_BASE64_IMAGE", f"Invalid base64 image payload: {exc}", 422) from exc
            img_format, width, height = inspect_image_bytes(raw)
            byte_size = len(raw)
            digest = hashlib.sha256(raw).hexdigest()
        else:
            width = int(payload.get("width") or 1280)
            height = int(payload.get("height") or 720)
            img_format = "METADATA_ONLY"
            byte_size = 0
            digest = hashlib.sha256(
                f"{payload['title']}|{width}x{height}|{payload.get('ocr_text', '')}".encode("utf-8")
            ).hexdigest()

        elements = list(payload.get("elements") or [])
        self._validate_elements(elements, width, height)

        item = {
            "capture_id": f"cap_{uuid.uuid4().hex[:10]}",
            "title": payload["title"].strip(),
            "source": payload.get("source", "desktop_primary").strip(),
            "image_format": img_format,
            "width": width,
            "height": height,
            "byte_size": byte_size,
            "sha256": digest,
            "ocr_text": payload.get("ocr_text", "").strip(),
            "elements": elements,
            "created_at": utc_now_iso(),
        }
        return self.db.add_capture(item)

    def hit_test(self, capture_id: str, x: int, y: int) -> Dict[str, Any]:
        cap = self.db.get_capture(capture_id)
        if not cap:
            raise VisionError("CAPTURE_NOT_FOUND", f"Capture '{capture_id}' not found.", 404)
        if x > cap["width"] or y > cap["height"]:
            raise VisionError(
                "COORDINATE_OUT_OF_BOUNDS",
                f"Point ({x}, {y}) is outside capture bounds ({cap['width']}x{cap['height']}).",
                422,
            )
        hits = []
        for el in cap["elements"]:
            if el["x"] <= x <= el["x"] + el["width"] and el["y"] <= y <= el["y"] + el["height"]:
                hits.append(el)
        hits.sort(key=lambda e: e["width"] * e["height"])
        return {
            "capture_id": capture_id,
            "point": {"x": x, "y": y},
            "hits": hits,
            "count": len(hits),
        }

    def query_capture(self, capture_id: str, question: str) -> Dict[str, Any]:
        cap = self.db.get_capture(capture_id)
        if not cap:
            raise VisionError("CAPTURE_NOT_FOUND", f"Capture '{capture_id}' not found.", 404)
        q_tokens = set(_tokenize(question))
        scored: List[Tuple[int, Dict[str, Any]]] = []
        for el in cap["elements"]:
            haystack = set(_tokenize(f"{el['label']} {el['role']} {el.get('text', '')}"))
            overlap = len(q_tokens & haystack)
            if overlap > 0:
                scored.append((overlap, el))
        scored.sort(key=lambda pair: (-pair[0], -pair[1].get("confidence", 0.0)))
        matched = [pair[1] for pair in scored[:5]]

        if matched:
            top = matched[0]
            cx = top["x"] + top["width"] // 2
            cy = top["y"] + top["height"] // 2
            answer = (
                f"Found {len(matched)} matching UI element(s). Top match: '{top['label']}' "
                f"({top['role']}) at ({top['x']}, {top['y']}, {top['width']}x{top['height']}), "
                f"center ({cx}, {cy})."
            )
        elif cap["ocr_text"] and (q_tokens & set(_tokenize(cap["ocr_text"]))):
            answer = f"Matched screen OCR text in capture '{cap['title']}': {cap['ocr_text'][:180]}"
        else:
            answer = (
                f"No matching UI elements or OCR terms found in capture '{cap['title']}' "
                f"({cap['width']}x{cap['height']}, {len(cap['elements'])} indexed elements)."
            )

        record = {
            "query_id": f"vq_{uuid.uuid4().hex[:10]}",
            "capture_id": capture_id,
            "question": question.strip(),
            "answer": answer,
            "matched_elements": matched,
            "created_at": utc_now_iso(),
        }
        return self.db.add_query(record)

    def get_status(self) -> Dict[str, Any]:
        captures = self.db.list_captures(limit=500)
        queries = self.db.list_queries(limit=500)
        total_elements = sum(len(c["elements"]) for c in captures)
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "captures_count": len(captures),
            "indexed_elements_count": total_elements,
            "queries_count": len(queries),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
