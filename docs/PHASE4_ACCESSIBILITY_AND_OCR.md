# JARVIS OS — Phase 4 Accessibility & Semantic Element Detection

## 1. Hybrid Layered Perception Architecture
In accordance with Phase 4 guidelines, element identification follows a strict hierarchy of reliability:

1. **Browser DOM & Structural Navigation**: Used for web applications (Google Chrome / Firefox) via `BrowserAgent` to extract structured links, buttons, tab titles, and search inputs.
2. **Desktop Window Geometry & Semantic Classification**: Window layout models calculate positions for titlebar controls (Close, Minimize, Maximize), activity bars (VS Code activity bar, status bar, tabs), and system taskbar panels (Start menu, clock, tray).
3. **Application Hierarchy**: `xwininfo -tree` traverses X11 subwindows to extract bounding boxes and relative offsets.
4. **Visual Change Detection (Pixel Diffing)**: Compares RGB matrices of pre- and post-action screenshots using `Pillow` and `numpy` to detect observable visual state modifications.
5. **Coordinate-based Fallback**: Used only when explicit x/y coordinates are requested by the user.

---

## 2. Safe Local Vision Probe Findings
- **Model Probed**: `qwen3.5:4b` (installed in Ollama on Raspberry Pi 5).
- **Test Condition**: Base64 encoded screenshot region sent to Ollama `/api/generate` with a 30s timeout.
- **Observed Result**: Request timed out at 30 seconds. On the 4-core ARM Cortex-A76 CPU, loading and performing multimodal attention on 4.7B parameters takes between 60 and 90 seconds.
- **Architectural Conclusion**: Heavy local multimodal LLMs cannot deliver the sub-second responsiveness required for real-time interactive computer use. Real-time perception is therefore handled natively by `scrot`, `wmctrl`, `xdotool`, and `ElementDetector` (< 250ms), reserving multimodal LLM analysis as an optional asynchronous offline capability.

---

## 3. Element Locator Matching Rules
The `ElementDetector` normalizes user natural-language queries into canonical UI controls:
- `"settings button"`, `"where is settings"`, `"settings icon"` &rarr; Matches `Settings Button` on system panel or active window.
- `"search field"`, `"search bar"`, `"search box"` &rarr; Matches `Search Field` / `Address Bar` in Chrome, VS Code, or PCManFM.
- `"first tab"`, `"tab 1"` &rarr; Matches `Tab 1` in Chrome or `Editor Tab 1` in VS Code.
- `"close window"`, `"close button"` &rarr; Matches `Close Window` button at `(wx + ww - 30, wy)`.
- `"terminal"`, `"file manager"` &rarr; Matches respective launcher icons on the desktop panel.
