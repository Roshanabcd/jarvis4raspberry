# JARVIS OS — Module 32: System Health & Diagnostics (`v1.0.0`)

**Module ID:** `jarvis-module-32-system-health-diagnostics`  
**Default Port:** `8132`  
**UI Route:** `/system-health`  
**API Prefix:** `/api/v1/system-health`  
**WebSocket:** `/api/v1/system-health/ws/metrics`

## Overview
JARVIS Module 32 delivers **real local OS telemetry (`simulated: false`)** for Raspberry Pi 5 and Linux hosts using zero external system dependencies. It captures CPU load averages, `/proc/meminfo` RAM usage, disk space, thermal sensor temperature (when exposed by Linux `/sys/class/thermal`), uptime, threshold alerts, localhost TCP service reachability probes, and scored diagnostic reports in SQLite WAL.

## Quickstart
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8132/system-health`.

## Testing & Demo
```bash
bash scripts/test.sh
```
