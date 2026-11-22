# API Reference — JARVIS Module 31: JARVIS Robot Brain (`v1.0.0`)

**Base URL:** `http://127.0.0.1:8131/api/v1/robot-brain`  
**WebSocket:** `ws://127.0.0.1:8131/api/v1/robot-brain/ws/telemetry`

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check, version, contract version, `simulated` flag |
| `GET` | `/manifest` | Returns `manifest.json` |
| `GET` | `/status` | Mode, E-STOP flag, 2D pose, battery %, obstacle distance, CPU temp |
| `POST` | `/estop` | Engage hardware E-STOP and zero velocities |
| `POST` | `/estop/reset` | Clear E-STOP (requires `confirm_reset: true`) |
| `POST` | `/sensors/reading` | Update `front_obstacle_m`, `battery_pct`, `cpu_temp_c` |
| `POST` | `/motion/cmd` | Execute bounded velocity command `(linear_mps, angular_rps, duration_s)` |
| `GET` | `/waypoints` | List saved 2D waypoints |
| `POST` | `/waypoints` | Register a named waypoint `(name, zone, x, y)` |
| `GET` | `/missions` | List autonomous missions |
| `POST` | `/missions` | Create a multi-step mission |
| `POST` | `/missions/{mission_id}/execute` | Execute a mission subject to E-STOP, obstacle, and battery guards |
| `GET` | `/events` | List telemetry audit log entries |
| `WS` | `/ws/telemetry` | Real-time connection & heartbeat status stream |

## Safety Error Codes
- `409 Conflict` (`ESTOP_ENGAGED`): Motion or mission attempted while E-STOP is active.
- `409 Conflict` (`ESTOP_RESET_CONFIRMATION_REQUIRED`): Reset attempted without `confirm_reset: true`.
- `409 Conflict` (`OBSTACLE_PROXIMITY_HALT`): Forward motion or mission attempted with obstacle closer than `min_obstacle_m`.
- `409 Conflict` (`LOW_BATTERY_LOCKOUT`): Mission attempted with battery below `min_battery_pct`.
