# API Reference — Module 28: AI Data Analyst

Base prefix: `/api/v1/ai-data-analyst` (default standalone port: `8128`).

## Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Module liveness, version, contract version, and `simulated` flag |
| `GET` | `/manifest` | Returns `manifest.json` metadata |
| `GET` | `/status` | Adapter name, `simulated` flag, datasets count, total rows indexed, queries count, uptime |
| `GET` | `/datasets` | List datasets (metadata + profile summary) |
| `POST` | `/datasets/csv` | Ingest a dataset from raw CSV text (`name`, `csv_text`, `description`) |
| `POST` | `/datasets/rows` | Ingest a dataset from JSON row objects (`name`, `rows`, `description`) |
| `GET` | `/datasets/{dataset_id}` | Fetch dataset rows, profile, and query history |
| `POST` | `/datasets/{dataset_id}/aggregate` | Group-by aggregation (`group_by`, `metric`, `agg`: `sum\|avg\|min\|max\|count`) |
| `POST` | `/datasets/{dataset_id}/anomalies` | Z-score outlier detection (`column`, `z_threshold`) |
| `POST` | `/datasets/{dataset_id}/ask` | Natural-language Q&A returning grounded answer + optional chart series |
| `GET` | `/datasets/{dataset_id}/report.md` | Export analytical report as `text/markdown` |
| `WS` | `/ws/events` | Real-time status stream (`ws.connected` + `ws.heartbeat`) |
