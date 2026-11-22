# Raspberry Pi 5 (ARM64) & Linux Deployment Guide — Module 43

This guide targets the primary deployment environment:
- **Raspberry Pi 5** (8 GB RAM, ARM64 / aarch64 Linux, Raspberry Pi OS Desktop, TigerVNC, Chromium)
- **HP Pavilion** (AMD Ryzen 5 5625U, 8 GB RAM, Ubuntu Linux)

## 1. System Packages (APT)

Install Tesseract OCR and X11/Wayland screen capture utilities:

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  tesseract-ocr tesseract-ocr-eng \
  libgl1 libglib2.0-0 \
  x11-xserver-utils scrot
```

Optional for Wayland / PipeWire sessions (Raspberry Pi OS Bookworm with Wayfire/labwc or Ubuntu Wayland):

```bash
sudo apt install -y grim xdg-desktop-portal
```

Verify Tesseract on ARM64:

```bash
tesseract --version
```

## 2. Display Server Behavior (TigerVNC / X11 vs Wayland)

Module 43 inspects `$XDG_SESSION_TYPE`, `$DISPLAY`, and `$WAYLAND_DISPLAY` automatically:

- **TigerVNC / X11 (`DISPLAY=:1` or `:0`)**:
  - Uses `xrandr --query` to enumerate connected displays.
  - Captures screens via `mss` (fastest, in-memory) with fallback to `scrot`.
  - Works reliably even when the Chromium browser tab showing JARVIS is minimized or on another workspace.
- **Wayland (`WAYLAND_DISPLAY=wayland-0`)**:
  - Uses `grim` (wlroots/Wayfire/labwc) where permitted, or surfaces an actionable `xdg-desktop-portal` ScreenCast notice if the compositor restricts unprompted capture.
  - Never assumes browser `getDisplayMedia()` can run indefinitely in the background.

## 3. Resource Guardrails for 8 GB RAM Systems

Module 43 is tuned for Raspberry Pi 5 and 8 GB laptops:
- **Default capture interval**: `2.5` seconds (configurable between `0.5s` and `60s`).
- **Frame change gating**: Skips OCR and vision inference when pixel diff & SHA-256 hash show no meaningful screen change.
- **Bounded concurrency**: Vision and OCR pipelines use bounded `asyncio.Semaphore` guards to prevent CPU/RAM spikes.
- **Zero `psutil` dependency**: System telemetry reads `/proc/meminfo`, `/proc/loadavg`, `/proc/net/dev`, and `shutil.disk_usage("/")` directly.
- **SQLite WAL mode**: Low-overhead local persistence with bounded history retention.

## 4. Installing & Running Standalone

```bash
cd JARVIS_Module_43_Autonomous_Screen_Guardian_v1.0.0
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/run.sh
```

Open in Chromium:
- Standalone HUD: `http://127.0.0.1:8143/screen-guardian`
- API Health: `http://127.0.0.1:8143/api/v1/screen-guardian/health`

## 5. Optional Frontend Dev / Build (Node.js)

If you want to run or build the React/TypeScript frontend separately:

```bash
cd frontend
npm install
npm run dev
# or production build:
npm run build
```

## 6. Optional External Coding Agent CLIs

Module 43 automatically discovers installed CLIs without failing if they are absent:
- `agy` (Google Antigravity CLI)
- `codex` (OpenAI Codex CLI)
- `gh copilot` (GitHub Copilot CLI)

When none of those CLIs are installed, Module 43 honestly reports them as `available: false` and remains fully functional via the built-in `ReferenceLocalRepairAgent` for authorized local Python workspace repairs.
