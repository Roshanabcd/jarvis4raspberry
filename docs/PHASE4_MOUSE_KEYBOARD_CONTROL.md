# JARVIS OS — Phase 4 Mouse & Keyboard Control Subsystem

## 1. Input Dispatch Architecture
All synthetic input events are dispatched through the centralized `ComputerActionEngine` (`tools/desktop/computer_action_engine.py`) communicating with the X11 display server on `DISPLAY=:0`.

### 1.1 Mouse Automation Primitives
- **Single Click**: `xdotool mousemove <x> <y> click 1`
- **Double Click**: `xdotool mousemove <x> <y> click --repeat 2 1`
- **Right Click**: `xdotool mousemove <x> <y> click 3`
- **Scroll Down**: `xdotool click --repeat <clicks> 5`
- **Scroll Up**: `xdotool click --repeat <clicks> 4`
- **Semantic Click**: `click_named_element(query)` resolves target coordinates via `ElementDetector` before dispatching physical cursor movement and click events.

### 1.2 Keyboard Automation Primitives
- **Text Typing**: `xdotool type --delay 12 <text>`
  - A 12ms inter-key delay is enforced to prevent buffer overflow and input dropping in complex GUI applications like Chrome and VS Code.
- **Key Presses**: `xdotool key <key>` (supports `Return`, `BackSpace`, `Tab`, `Escape`, `Page_Down`, `Page_Up`).
- **Keyboard Shortcuts (Hotkeys)**: `xdotool key <hotkey>` (e.g. `ctrl+t`, `ctrl+w`, `alt+Left`, `ctrl+r`, `ctrl+Shift+p`).

---

## 2. Observable State Verification
To ensure honesty and prevent simulated assertions, every action executes pre- and post-action verification:
1. Prior to action execution, the system captures pre-action window state and screenshot hash.
2. The action is dispatched.
3. The engine waits a 250ms settling interval for GUI rendering and process scheduling.
4. Post-action state is captured.
5. The pixel difference between pre- and post-screenshots is computed via `numpy` array delta calculation.
6. If the focused window changed OR changed pixel ratio exceeds 0.2%, the action is certified as **VERIFIED**. Otherwise, the action is marked as **DISPATCHED (Unverified)**.

---

## 3. Window Management & Application Switching
- **Window Activation**: `wmctrl -i -a <hex_id>` (focus by window ID) or `wmctrl -a <title>` (focus by title substring).
- **Application Switching**: Uses canonical alias mappings (`terminal` &rarr; `x-terminal-emulator`, `vscode` &rarr; `com.microsoft.vscode`, `chrome` &rarr; `google-chrome`, `files` &rarr; `pcmanfm`).
- **Window State Toggles**: Minimization (`xdotool windowminimize`) and Maximization (`wmctrl -b toggle,maximized_vert,maximized_horz`).
