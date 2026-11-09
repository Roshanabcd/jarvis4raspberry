# JARVIS OS — Phase 4 Cross-Application Workflows

## 1. Supported Desktop Applications
JARVIS OS interacts with all primary desktop environments installed on the Raspberry Pi 5:

1. **Google Chrome**:
   - Window activation, tab inspection, and active tab title extraction.
   - Keystroke navigation (`ctrl+t` new tab, `ctrl+w` close tab, `alt+Left` back, `ctrl+r` reload).
   - Omnibox focus and URL search input.
   - Preservation of user profile (`/home/roshan/.config/google-chrome`).

2. **Visual Studio Code**:
   - Project directory opening (`code /path/to/project`).
   - Source file opening with specific line targeting (`code -g /path/to/file:line`).
   - Window focus and editor tab classification.
   - Verification of Problems panel and integrated terminal.

3. **Google Antigravity IDE**:
   - Project switching and workspace opening (`/home/roshan/Downloads/Antigravity-arm64/antigravity /path/to/project`).
   - Project inspection and code review workflows.

4. **PCManFM (File Manager)**:
   - Directory navigation (`pcmanfm /path/to/folder`).
   - Location bar focus and file selection.

5. **Integrated Terminal Console**:
   - Execution of shell commands via `terminal_engine` (Phase 2).
   - Non-blocking execution, exit code capture, and streaming stdout/stderr.

---

## 2. Multi-Step Workflow Case Studies

### Case Study 1: Open and Inspect Project
- **Command**: *"Open my project in VS Code, inspect its README, then find all Python files."*
- **Execution**:
  1. Resolves `GameProject` path (`/home/roshan/UnityGameWorkspace/GameProject`).
  2. Launches/focuses VS Code with project directory.
  3. Reads `README.md` via `CodeEditorAgent` directly from filesystem without OCR errors.
  4. Scans directory for `.py` files, returning `controller.py` and `build.py`.
- **Duration**: 1.84 seconds total.

### Case Study 2: Controlled Code Defect Repair
- **Command**: *"Fix the simple Python error in the test project, save it, run it and show the output."*
- **Execution**:
  1. Reads source file with line numbers.
  2. Applies targeted string replacement (`return a - b` &rarr; `return a + b`).
  3. Generates unified git diff.
  4. Runs the script via `terminal_engine` and reports verified stdout (`5`).
- **Duration**: 0.42 seconds total.

### Case Study 3: Browser Search & Second Organic Site Navigation
- **Command**: *"Search Google for Raspberry Pi robotics and open the second website."*
- **Execution**:
  1. DuckDuckGo Lite retrieves organic results without ads.
  2. Result #2 (`Beginner-friendly robotics projects - Raspberry Pi`) is selected.
  3. URL is opened in Google Chrome on `DISPLAY=:0`.
  4. Window title is confirmed via `xdotool`.
- **Duration**: 2.31 seconds total.
