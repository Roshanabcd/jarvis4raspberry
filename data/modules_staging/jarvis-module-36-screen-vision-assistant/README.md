# JARVIS OS — Module 36: Screen Vision Assistant (`v1.0.0`)

Local-first screen capture inspector, UI bounding-box region analyzer, spatial hit-tester, and grounded screen Q&A assistant with an interactive SVG overlay HUD for JARVIS OS.

## Key Capabilities
- **Real Local Image Header & SHA-256 Inspection (`simulated: false`)**: Parses PNG (`IHDR`), BMP, and JPEG (`SOF`) binary headers via Python `struct` with zero external C/vision dependencies.
- **UI Bounding-Box Indexing & Bounds Validation**: Persists structured screen elements (`role`, `label`, `text`, `x`, `y`, `width`, `height`, `confidence`) in SQLite WAL and rejects out-of-bounds or duplicate IDs (`422`).
- **Spatial Hit-Testing**: Resolves screen coordinates `(x, y)` to matching UI regions sorted from innermost to outermost.
- **Grounded Screen Q&A**: Answers natural-language UI location and OCR queries against indexed captures and records query history.
- **Standalone HUD & Host Mount**: Serves `/vision` directly from FastAPI (`port 8136`) and mounts cleanly into JARVIS OS via `backend.app.main:mount_module`.

## Quick Start
```bash
./scripts/setup.sh
./scripts/run.sh
# Open http://localhost:8136/vision
```
