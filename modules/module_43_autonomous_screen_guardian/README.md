# JARVIS OS — Module 43: Autonomous Screen Guardian & AI Repair Agent (`v1.0.0`)

User-authorized desktop screen monitoring, real-time local Tesseract OCR, configurable multimodal vision adapters, contextual error detection, severity notifications, voice command adapter, and permission-controlled AI coding-agent repair with automated test verification.

## Core Capabilities
- **Explicit-Consent Screen Monitoring (`backend/services/screen_capture.py`)**: Detects X11/Wayland/PipeWire display servers and monitors via `xrandr`, captures frames via `mss`/`scrot`/`grim`, masks excluded regions in-memory, skips excluded sensitive windows, performs frame change detection, and never stores raw screenshots to disk by default.
- **Real-Time Local OCR (`backend/services/ocr_engine.py`)**: Uses local **Tesseract OCR** (`pytesseract` + Pillow grayscale/upscale/autocontrast preprocessing) to extract normalized text, average confidence, and word bounding boxes.
- **Configurable Multimodal Vision (`backend/adapters/vision_providers.py`)**: Local heuristic analysis by default; optional Gemini/OpenAI adapters strictly gated behind `JARVIS_M43_ALLOW_REMOTE_VISION_UPLOAD=true`, bounded concurrency semaphore, and graceful fallback on provider failure.
- **Contextual Error Detection & Prompt-Injection Defense (`backend/services/error_detector.py`)**: Detects Python/Node/system/browser/AI-agent errors using contextual signals (harmless prose containing the word `"error"` does not trigger false alarms), deduplicates alerts by fingerprint, and treats all screen text as untrusted data (never executed as commands).
- **Controlled Coding-Agent Repair (`backend/adapters/coding_agents.py`, `backend/services/repair_engine.py`)**: Discovers real installed CLI tools (`agy`, `codex`, `gh copilot`) via PATH/`--version`/`--help` without inventing flags, hard-blocks `--dangerously-skip-permissions`, enforces protected system path & `trusted_workspaces` boundaries, supports 4 repair modes (`observe_only`, `suggest_fix`, `assisted_repair`, `trusted_workspace_autopilot`), generates unified diffs, runs focused `unittest` verification, supports live cancellation, and marks errors resolved **only** when verification tests pass (`verified_fixed`).

## Quick Start
```bash
./scripts/setup.sh
./scripts/run.sh
# Open http://127.0.0.1:8143/screen-guardian
```
