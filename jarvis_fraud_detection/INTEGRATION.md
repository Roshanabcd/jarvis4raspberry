# Integrating Fraud Detection System into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_fraud_detection/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_fraud_detection/`).

## 2. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_fraud_detection import FraudDetectionConfig, create_router

app.include_router(create_router(FraudDetectionConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_FRAUD_DB_PATH`: SQLite WAL database path (default: `.jarvis_fraud_detection/fraud_detection.db`).
- `JARVIS_FRAUD_REVIEW_THRESHOLD`: Risk score threshold for `review` + alert creation (default: `45.0`).
- `JARVIS_FRAUD_BLOCK_THRESHOLD`: Risk score threshold for `critical` / `block` (default: `75.0`).
- `JARVIS_FRAUD_VELOCITY_WINDOW_MIN`: Sliding velocity window in minutes (default: `15`).
- `JARVIS_FRAUD_PORT`: Standalone server port (default: `8022`).

## 4. Endpoints Added
- `GET /fraud-detection` — Interactive JARVIS OS Fraud Detection dashboard
- `GET /api/fraud-detection/health` — Engine status and open alert count
- `POST /api/fraud-detection/events` — Score and persist a transaction, auth log, or audit event
- `POST /api/fraud-detection/events/batch` — Score a batch of events
- `GET /api/fraud-detection/events` — List recent scored events
- `GET /api/fraud-detection/alerts` — List alerts filtered by status/severity
- `PATCH /api/fraud-detection/alerts/{alert_id}` — Update alert triage status and analyst note
- `GET /api/fraud-detection/summary` — Risk distribution and top risky actors

## 5. Dashboard Card Update
Once mounted, update the **Fraud Detection System** card in your JARVIS OS dashboard from `PLANNED` to `AVAILABLE` and point its **Open** button to `/fraud-detection`.
