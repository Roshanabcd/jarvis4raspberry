# JARVIS OS — Module 33: Defensive Cybersecurity Agent (`v1.0.0`)

**Module ID:** `jarvis-module-33-defensive-cybersecurity-agent`  
**Default Port:** `8133`  
**UI Route:** `/cybersecurity`  
**API Prefix:** `/api/v1/cybersecurity`  
**WebSocket:** `/api/v1/cybersecurity/ws/alerts`

## Overview
JARVIS Module 33 is a **strictly defensive, local-first security operations agent (`simulated: false`)** for Raspberry Pi 5 and Linux workspaces. It performs sandboxed secret & world-writable file scanning (with automatic redaction of matched values), SHA-256 File Integrity Monitoring (FIM), SSH/sudo/HTTP log anomaly analysis, and structured incident triage with remediation playbooks.

## Quickstart
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8133/cybersecurity`.

## Testing & Demo
```bash
bash scripts/test.sh
```
