# JARVIS OS — Fraud Detection System

Real-time anomaly detection and suspicious pattern analysis across **transaction streams**, **authentication logs**, and **audit entries** for **Raspberry Pi 5 (8GB)**.

## Features
- **Statistical + Heuristic Scorer (`detector.py`)**: Per-actor rolling Z-score amount spike detection, sliding-window velocity bursts, unseen geo/device/IP shifts, brute-force & post-failure login detection, and sensitive administrative audit triggers (`disable_mfa`, `delete_logs`, `bypass_estop`, `privilege_escalation`).
- **Alert Triage Queue (`storage.py`, `engine.py`)**: Automatically generates SQLite WAL alerts whenever risk exceeds `review_threshold` (`45.0`) and supports `open`, `investigating`, `resolved`, and `false_positive` dispositions.
- **Batch Ingestion & Analytics**: Score up to 200 events per batch and monitor top risky actors and severity breakdowns at `/fraud-detection`.

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
python3 -m jarvis_fraud_detection.app
# Open http://localhost:8022/fraud-detection
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_fraud_detection/tests -v
```
