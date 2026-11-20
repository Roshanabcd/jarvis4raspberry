# JARVIS OS — Handwritten to Text Converter

Convert handwritten notebook photos or live canvas drawings into clean digital text (`.txt` / `.md`) on **Raspberry Pi 5 (8GB)** or any Linux/macOS/Windows machine.

## Features
- **Upload & Live Drawing Pad UI (`static/index.html`)**: Upload PNG/JPG/WEBP photos of handwritten notes or write directly on an HTML5 mouse/touch/stylus canvas.
- **Handwriting Image Preprocessor (`preprocessor.py`)**: Grayscale conversion, upscaling, auto-contrast, stroke sharpening, and adaptive binarization via Pillow.
- **Multi-Tier OCR Engine (`ocr_engine.py`)**:
  - **Local Offline Tesseract** (`sudo apt install -y tesseract-ocr tesseract-ocr-nep tesseract-ocr-hin`)
  - **OpenRouter Vision LLM** (highest accuracy for cursive handwriting when `OPENROUTER_API_KEY` is set and `use_vision_llm=true`)
- **Post-Processing & Export (`postprocessor.py`, `storage.py`)**: Repairs hyphenated line wraps, normalizes whitespace, saves history in SQLite WAL, and exports `.txt` or `.md`.

## Quick Start (Standalone)
```bash
sudo apt install -y tesseract-ocr   # Optional: enables offline OCR on Raspberry Pi 5
pip install -r requirements.txt
python3 -m jarvis_handwriting_ocr.app
# Open http://localhost:8026/handwriting-ocr
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_handwriting_ocr/tests -v
```
