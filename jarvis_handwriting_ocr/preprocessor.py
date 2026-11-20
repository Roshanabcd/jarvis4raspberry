"""Image decoding and handwriting-optimized preprocessing (grayscale, contrast, sharpen, binarize)."""

from __future__ import annotations

import base64
import io
from typing import Tuple


def pillow_available() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def decode_base64_image(image_base64: str, max_bytes: int) -> Tuple[bytes, str]:
    """Decode raw or data-URI base64 image payload, returning (bytes, mime_type)."""
    raw_str = image_base64.strip()
    mime = "image/png"
    if raw_str.lower().startswith("data:") and "," in raw_str:
        header, raw_str = raw_str.split(",", 1)
        if ";" in header:
            mime = header[5:].split(";", 1)[0] or "image/png"

    try:
        img_bytes = base64.b64decode(raw_str)
    except Exception as exc:
        raise ValueError("Invalid base64 image payload.") from exc

    if not img_bytes:
        raise ValueError("Decoded image payload is empty.")
    if len(img_bytes) > max_bytes:
        raise ValueError(f"Image exceeds maximum allowed size ({max_bytes} bytes).")
    return img_bytes, mime


def preprocess_handwriting_image(img_bytes: bytes, enable_preprocess: bool = True) -> Tuple[bytes, int, int]:
    """Return (processed_png_bytes, width, height) optimized for handwriting OCR."""
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    except Exception:
        # Graceful fallback if Pillow is unavailable
        return img_bytes, 0, 0

    try:
        with Image.open(io.BytesIO(img_bytes)) as img:
            width, height = img.size
            if not enable_preprocess:
                out = io.BytesIO()
                img.convert("RGB").save(out, format="PNG")
                return out.getvalue(), width, height

            # Upscale small handwriting images for better character segmentation
            if width < 900:
                scale = min(2.0, 900.0 / max(width, 1))
                img = img.resize((int(width * scale), int(height * scale)))

            # Convert to grayscale, auto-contrast, sharpen strokes, and mild denoise
            gray = ImageOps.grayscale(img)
            gray = ImageOps.autocontrast(gray, cutoff=2)
            gray = ImageEnhance.Contrast(gray).enhance(1.6)
            gray = gray.filter(ImageFilter.SHARPEN)

            # Soft adaptive-style thresholding around image mean
            hist = gray.histogram()
            total = sum(hist) or 1
            mean_val = sum(i * h for i, h in enumerate(hist)) / total
            thresh = max(90, min(195, int(mean_val * 0.85)))
            bw = gray.point(lambda p: 255 if p > thresh else 0, mode="L")

            out = io.BytesIO()
            bw.save(out, format="PNG")
            return out.getvalue(), width, height
    except Exception as exc:
        raise ValueError(f"Unable to decode image file: {exc}") from exc
