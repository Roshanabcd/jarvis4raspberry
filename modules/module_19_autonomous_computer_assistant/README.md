# JARVIS OS — Module 19: Autonomous Computer Assistant (`v1.0.0`)

Permission-controlled computer automation module for **JARVIS OS** (Phase A — Core AI Operating System). Ships with `SafeDemoDesktopAdapter` by default so it **never controls a real host OS** until explicitly configured via `DesktopAutomationAdapter`.

## Implemented Features
- **Desktop Application Discovery** (`GET /apps`, `discover_apps`)
- **Permitted Screenshot Capture** (`capture_screenshot`, real Pillow PNG rendering of the virtual desktop visibly labeled `SIMULATED DESKTOP`)
- **Window Selection** (`GET /windows`, `select_window`)
- **Keyboard & Mouse Actions** (`mouse_move`, `mouse_click`, `keyboard_type`, `keyboard_hotkey`)
- **Sandboxed File Interaction** (`file_list`, `file_read`, `file_write`, `file_delete` — strictly confined to `JARVIS_M19_SANDBOX_DIR` with canonical path-traversal blocking)
- **Allowlisted Application Launch** (`launch_app`, gated by human approval)
- **Human Approval Checkpoints** (high-risk actions pause in `awaiting_approval` until approved or rejected)
- **Emergency Stop (E-STOP)** (persisted kill switch that blocks all actions with HTTP `423` until reset)
- **Dry-Run Mode** (global or per-action validation without state mutation)
- **Action History, Replay & Diagnostics** (`POST /actions/replay`, `GET /diagnostics`, SQLite WAL persistence)

## Quick Start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8119
# Standalone UI: http://localhost:8119/computer-assistant
```
