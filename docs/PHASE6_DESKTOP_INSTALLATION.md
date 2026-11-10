# JARVIS OS — Phase 6 Desktop Installation & Usage Guide

**Deployment Instructions for Raspberry Pi 5**

---

## 1. Quick Launch Options

### Option A: From the Desktop GUI
1. Double-click the **JARVIS OS** icon located on your desktop (`/home/roshan/Desktop/jarvis-os.desktop`).
2. The standalone window opens immediately sized to 1360×768 with dark navy and cyan futuristic theme.

### Option B: From the Application Menu
1. Open the Raspberry Pi Applications Menu (top-left panel).
2. Navigate to **Accessories** or **Utility**.
3. Click **JARVIS OS**.

### Option C: From the Terminal
Type:
```bash
jarvis
```
The universal launcher checks if backend `http://127.0.0.1:8000` is running, boots it automatically if needed, and presents the standalone desktop application window.

---

## 2. CLI and Management Commands

The `jarvis` executable supports system automation and diagnostics:

| Command | Action |
| :--- | :--- |
| `jarvis` | Launch the standalone desktop application window. |
| `jarvis --status` | Check if backend and desktop window are running (returns JSON). |
| `jarvis --stop` | Cleanly terminate running desktop window and backend services. |
| `jarvis --backend-only` | Start backend API service without opening a desktop GUI window. |
| `jarvis cli --status` | Inspect AI and system telemetry via terminal CLI. |
| `jarvis cli -c "What is system uptime?"` | Execute a single query through terminal CLI. |

---

## 3. Desktop Application Profile & Isolation

- **Config Directory:** `/home/roshan/.config/jarvis-os/`
- **Application Profile:** `/home/roshan/.config/jarvis-os/desktop-profile/` (isolated from regular browsing history and cache).
- **Process Lock:** `/home/roshan/.config/jarvis-os/desktop_app.lock` (guarantees single-instance execution).
- **Backend PID File:** `/home/roshan/.config/jarvis-os/backend.pid`.
