# Security & Safety — Module 19 (`v1.0.0`)

- **Default Safe Adapter**: `SafeDemoDesktopAdapter` never touches host OS windows, keyboard, or mouse.
- **Emergency Stop (E-STOP)**: Persisted in SQLite; blocks all actions with HTTP `423` until explicitly reset.
- **High-Risk Approval Gate**: `launch_app`, `keyboard_hotkey`, `file_write`, and `file_delete` require human approval by default.
- **Path Traversal Protection**: File actions reject absolute paths and `..` segments and verify `candidate.relative_to(sandbox_root)`.
- **Limitation**: Standalone mode does not include JWT/OAuth operator authentication; protect behind JARVIS Core / Module 40 before enabling any live OS adapter.
