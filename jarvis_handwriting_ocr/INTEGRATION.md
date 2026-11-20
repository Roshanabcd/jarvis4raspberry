# Integrating Handwritten to Text Converter into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_handwriting_ocr/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_handwriting_ocr/`).

## 2. Install Offline OCR Binary on Raspberry Pi 5 (Recommended)
```bash
sudo apt update && sudo apt install -y tesseract-ocr tesseract-ocr-nep tesseract-ocr-hin
```

## 3. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_handwriting_ocr import HandwritingOCRConfig, create_router

app.include_router(create_router(HandwritingOCRConfig()))
```

## 4. Environment Variables (Optional)
- `JARVIS_OCR_DB_PATH`: SQLite WAL database path (default: `.jarvis_handwriting_ocr/handwriting_ocr.db`).
- `JARVIS_OCR_LANG`: Default Tesseract language code (default: `eng`).
- `OPENROUTER_API_KEY` / `JARVIS_OCR_VISION_MODEL`: Enables Vision LLM handwriting transcription when `use_vision_llm=true`.
- `JARVIS_OCR_PORT`: Standalone server port (default: `8026`).

## 5. Endpoints Added
- `GET /handwriting-ocr` — Interactive Upload + Live Drawing Pad dashboard
- `GET /api/handwriting-ocr/health` — Backend availability (`pillow`, `local_tesseract`, `openrouter_vision_llm`)
- `POST /api/handwriting-ocr/convert` — Convert base64 handwritten image to text
- `GET /api/handwriting-ocr/history` — List past conversions
- `GET /api/handwriting-ocr/history/{id}/export?fmt=txt|md` — Download extracted text
- `DELETE /api/handwriting-ocr/history/{id}` — Delete conversion record
