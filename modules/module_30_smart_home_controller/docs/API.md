# API Reference — JARVIS Module 30: Smart Home Controller (`v1.0.0`)

**Base URL:** `http://127.0.0.1:8130/api/v1/smart-home`  
**WebSocket:** `ws://127.0.0.1:8130/api/v1/smart-home/ws/events`

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Module health check, version, contract version, and `simulated` flag |
| `GET` | `/manifest` | Returns `manifest.json` |
| `GET` | `/status` | Live adapter name, device/scene/rule counts, active watts, uptime |
| `GET` | `/devices` | List all devices (optional `?room=<name>` filter) |
| `POST` | `/devices` | Register a device (`light`, `thermostat`, `smart_plug`, `lock`, `sensor`) |
| `POST` | `/devices/{device_id}/command` | Dispatch a command (`turn_on`, `turn_off`, `set_brightness`, `set_temp`, `lock`, `unlock`, `update_reading`) |
| `GET` | `/scenes` | List all configured scenes |
| `POST` | `/scenes` | Create a multi-device scene |
| `POST` | `/scenes/{scene_id}/activate` | Atomically run all actions in a scene |
| `GET` | `/rules` | List all sensor automation rules |
| `POST` | `/rules` | Create a threshold-based sensor rule |
| `POST` | `/rules/evaluate` | Evaluate all rules against current sensor readings |
| `GET` | `/energy` | Total active wattage and per-room breakdown |
| `GET` | `/events` | Audit log of device registrations, commands, and automations |
| `WS` | `/ws/events` | Real-time connection & heartbeat status stream |

## Safety Error Codes
- **`409 Conflict` (`UNLOCK_CONFIRMATION_REQUIRED`)**: Returned when `command: "unlock"` is sent without `confirm_unlock: true`.
- **`404 Not Found` (`DEVICE_NOT_FOUND` / `SCENE_NOT_FOUND`)**: Returned when referencing an unknown device or scene ID.
