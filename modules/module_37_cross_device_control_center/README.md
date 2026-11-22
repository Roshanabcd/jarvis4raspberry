# JARVIS OS — Module 37: Cross-Device Control Center (`v1.0.0`)

Unified cross-device mesh registry, capability-guarded remote command bridge (`simulated: true`), and shared clipboard sync bus with a JARVIS HUD for JARVIS OS.

## Key Capabilities
- **Device Mesh Registry & Heartbeats**: Registers laptops, Raspberry Pi nodes, phones, and tablets in SQLite WAL with online status, battery level, and declared capabilities.
- **Capability-Guarded Command Bridge (`simulated: true`)**: Enforces online checks (`409 DEVICE_OFFLINE`) and capability checks (`422 CAPABILITY_NOT_SUPPORTED`) before executing simulated remote actions (`notifications`, `media`, `lock`, `display`, `power`, `clipboard`).
- **Cross-Device Clipboard Sync**: Persists SHA-256-hashed clipboard entries scoped to clipboard-capable mesh nodes.
- **Standalone HUD & Host Mount**: Serves `/devices` directly from FastAPI (`port 8137`) and mounts cleanly into JARVIS OS via `backend.app.main:mount_module`.

## Quick Start
```bash
./scripts/setup.sh
./scripts/run.sh
# Open http://localhost:8137/devices
```
