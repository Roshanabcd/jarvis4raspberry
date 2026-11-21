# JARVIS OS — Module 28: AI Data Analyst (`v1.0.0`)

An independent, portable, integration-ready AI Data Analyst module for JARVIS OS. Ingests CSV or JSON tabular datasets into an isolated SQLite WAL database, computes automated column profiles and descriptive statistics (`min`, `max`, `mean`, `median`, `stdev`, `sum`), detects Z-score anomalies, runs group-by aggregations, answers natural-language questions with chart-ready series, and exports Markdown analytical reports.

## Core Capabilities
- **CSV & JSON Ingestion**: Parse tabular data with zero heavy numeric dependencies (ideal for Raspberry Pi 5).
- **Automated Statistical Profiling**: Infers `numeric` vs `categorical` types, missing values, unique counts, and full descriptive statistics.
- **Z-Score Anomaly Detection**: Flags rows where `|z| >= threshold` with exact z-scores and row payloads.
- **Group-By Aggregations**: Supports `sum`, `avg`, `min`, `max`, and `count` grouped by any categorical column.
- **Natural-Language Q&A**: Translates natural questions (`"total revenue by region"`, `"find outliers in latency_ms"`) into grounded numerical answers and chart series.
- **Markdown Report Export**: Downloadable summary via `GET /api/v1/ai-data-analyst/datasets/{id}/report.md`.
- **Pluggable Narrative Adapter**: Uses `LocalDataInsightAdapter` (`simulated: true`) behind `DataInsightAdapter` so external LLM narrative providers can be connected cleanly later.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8128/ai-data-analyst` for the built-in zero-build JARVIS Control UI.

## Running Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_analyst_demo.py
```

## Integrating Into JARVIS OS
```python
from backend.app.main import mount_module
mount_module(app)  # Mounts /api/v1/ai-data-analyst/* and /ai-data-analyst
```
