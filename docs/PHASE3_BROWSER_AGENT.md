# JARVIS OS — Phase 3B: Real Browser Agent Architecture & Specification

## Executive Overview
Phase 3B delivers an authentic desktop browser automation agent that interfaces directly with Google Chrome (and Mozilla Firefox) on native Linux X11 (`DISPLAY=:0`) on the Raspberry Pi 5. Unlike conventional sandbox solutions that spin up ephemeral, unauthenticated browser profiles, the JARVIS Browser Agent preserves the user's permanent browser profile (`/home/roshan/.config/google-chrome`), active cookies, history, and logins.

---

## Architecture & Interaction Matrix

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        JARVIS Natural Language UI                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                       Intent Router / Fast-Path
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  BrowserAgent (tools/browser/browser_agent.py)         │
│  - Environment: DISPLAY=:0, XAUTHORITY=~/.Xauthority                   │
│  - Process Management: Popen(close_fds=True, start_new_session=True)   │
│  - Profile: /home/roshan/.config/google-chrome (User Session Kept)     │
└───────────────┬──────────────────────────────────────┬─────────────────┘
                │                                      │
                ▼                                      ▼
┌───────────────────────────────┐      ┌─────────────────────────────────┐
│     Google Chrome (X11)       │      │   X11 Window Manager (wmctrl /  │
│  - Direct URL navigation      │      │               xdotool)          │
│  - Profile preserved          │      │  - Window focusing: wmctrl -a   │
│  - Hardware audio routing     │      │  - Keystroke dispatch: xdotool  │
└───────────────────────────────┘      └─────────────────────────────────┘
```

---

## Implemented Capabilities

### 1. User Profile Preservation
- **Path:** `/home/roshan/.config/google-chrome`
- **Execution Mechanism:** Commands are executed through detached subprocesses (`start_new_session=True`, `close_fds=True`, `stdin=subprocess.DEVNULL`) directly referencing the installed binary (`/usr/bin/google-chrome`).
- **Authentication Continuity:** All logged-in Google, YouTube, and website accounts remain active. No headless mock environments are created.

### 2. Tab & Window Operations
- **`open_url(url, browser="chrome", new_tab=False)`**: Launches the target URL into the running Chrome window as a new tab or window, and automatically focuses the window on `DISPLAY=:0`.
- **`find_browser_windows(browser="chrome")`**: Queries `wmctrl -l` to inspect window IDs, desktops, and page titles.
- **`activate_window(window_id_or_title)`**: Brings the browser to the foreground.
- **`go_back()` / `go_forward()` / `reload()`**: Dispatches X11 keyboard shortcuts (`Alt+Left`, `Alt+Right`, `Ctrl+r`) directly to the window ID via `xdotool`.
- **`switch_tab(tab_num)`**: Switches active tab via `Ctrl+1..9`.
- **`close_tab()`**: Closes active tab via `Ctrl+w`.
- **`scroll(direction)`**: Smoothly scrolls pages using `Page_Down` / `Page_Up`.

---

## Verification & Telemetry
- **X11 Session:** Verified on `DISPLAY=:0`.
- **Launch Latency:** ~1.09 seconds to spawn and focus window on Raspberry Pi 5.
- **Process Decoupling:** Verified that parent Python / Uvicorn threads do not block or inherit open standard I/O pipes.
