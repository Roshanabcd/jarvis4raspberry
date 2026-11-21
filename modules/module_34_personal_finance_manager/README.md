# JARVIS OS — Module 34: Personal Finance Manager (`v1.0.0`)

**Module ID:** `jarvis-module-34-personal-finance-manager`  
**Default Port:** `8134`  
**UI Route:** `/finance`  
**API Prefix:** `/api/v1/finance`  
**WebSocket:** `/api/v1/finance/ws/updates`

## Overview
JARVIS Module 34 is a **100% local-first Personal Finance Manager (`simulated: false`)** backed by SQLite WAL. Track multi-account balances, categorized income and expenses, monthly budget burn alerts (`ok` / `warning` / `exceeded`), savings goal progress, net worth & savings rate analytics, and RFC 4180 CSV exports without sending personal financial data to external servers.

## Quickstart
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8134/finance`.

## Testing & Demo
```bash
bash scripts/test.sh
```
