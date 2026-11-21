# JARVIS OS — Module 31: JARVIS Robot Brain (`v1.0.0`)

**Module ID:** `jarvis-module-31-robot-brain`  
**Default Port:** `8131`  
**UI Route:** `/robot-brain`  
**API Prefix:** `/api/v1/robot-brain`  
**WebSocket:** `/api/v1/robot-brain/ws/telemetry`

## Overview
JARVIS Module 31 implements a safety-first robotics autonomy and control plane designed for Raspberry Pi 5 robots and ROS2/GPIO hardware bridges. It ships with `SimulatedRobotHardwareAdapter` (`simulated: true`) so you can test E-STOP interlocks, differential-drive kinematics, obstacle clearance halts, low-battery lockouts, waypoints, and multi-step autonomous missions locally without physical motors or LiDAR attached.

## Key Features
- **Hardware E-STOP Interlock**: `POST /estop` immediately zeroes all velocities and blocks motion/mission commands (`409 ESTOP_ENGAGED`) until cleared via `POST /estop/reset` with `confirm_reset: true`.
- **Safety Guards**: Automatic velocity clamping (`max_linear_mps`, `max_angular_rps`), forward obstacle proximity halt (`409 OBSTACLE_PROXIMITY_HALT`), and low-battery mission lockout (`409 LOW_BATTERY_LOCKOUT`).
- **2D Kinematics & Waypoints**: Differential-drive pose integration `(x, y, heading_deg)` and named 2D waypoint storage in SQLite WAL.
- **Autonomous Missions**: Multi-step mission execution (`navigate_to_waypoint`, `inspect_zone`, `return_to_dock`) with distance tracking, battery consumption, and telemetry audit logs.
- **Standalone HUD & React Frontend**: Zero-build JARVIS HUD at `/robot-brain` plus a React/TypeScript/Vite/Tailwind workspace in `frontend/`.

## Quickstart
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8131/robot-brain`.

## Testing & Demo
```bash
bash scripts/test.sh
```
