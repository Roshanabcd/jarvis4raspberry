# JARVIS OS — Module 30: Smart Home Controller (`v1.0.0`)

**Module ID:** `jarvis-module-30-smart-home-controller`  
**Default Port:** `8130`  
**UI Route:** `/smart-home`  
**API Prefix:** `/api/v1/smart-home`  
**WebSocket:** `/api/v1/smart-home/ws/events`

## Overview
JARVIS Module 30 provides a unified, local-first Smart Home Controller with a versioned `SmartHomeBridgeAdapter` abstraction, SQLite WAL persistence, safety-gated smart lock unlocking, multi-device scene activation, sensor-driven automation rule evaluation, and real-time per-room energy telemetry.

Out of the box, the module ships with `SimulatedSmartHomeBridgeAdapter` (`simulated: true`) so you can run, test, and integrate the complete control plane on Raspberry Pi 5 or any development host without physical IoT hardware. To connect real devices (Home Assistant, MQTT, Zigbee2MQTT, Matter), implement the `SmartHomeBridgeAdapter` interface in `backend/adapters/bridge_adapter.py`.

## Key Features
- **Device Registry & Control**: Register and control `light`, `thermostat`, `smart_plug`, `lock`, and `sensor` devices with room grouping and rated wattage metadata.
- **Safety-Gated Smart Lock Control**: Unlocking a `lock` device requires `confirm_unlock: true`; unconfirmed unlock requests are rejected with `409 Conflict` (`UNLOCK_CONFIRMATION_REQUIRED`) and logged to the audit stream.
- **Multi-Device Scenes**: Bundle multiple device commands (`turn_on`, `turn_off`, `set_brightness`, `set_temp`, `lock`) into reusable scenes and activate them atomically with one API call.
- **Sensor Automation Rules**: Create threshold-based rules (`>`, `>=`, `<`, `<=`, `==`) linking sensor readings to target device commands and evaluate them on demand.
- **Room Energy Telemetry**: Real-time estimated power draw (watts) per room and across all active devices.
- **Zero-Build Control UI + React/Vite Frontend**: Ready-to-use futuristic JARVIS HUD served directly at `/smart-home` plus a full React/TypeScript/Tailwind workspace in `frontend/`.

## Quickstart
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8130/smart-home` in your browser.

## Testing & Demo
```bash
bash scripts/test.sh
```

## Documentation
- [API Reference](docs/API.md)
- [JARVIS OS Integration Guide](docs/INTEGRATION.md)
- [Security & Safety Model](docs/SECURITY.md)
- [Test Verification Report](docs/TEST_REPORT.md)
- [Changelog](CHANGELOG.md)
