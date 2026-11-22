# Module 36 — API Reference (`/api/v1/vision`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/vision/health` | Module health & contract metadata (`simulated: false`) |
| `GET` | `/api/v1/vision/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/vision/status` | Capture, indexed element, and query counts + uptime |
| `GET` | `/api/v1/vision/captures` | List persisted screen captures |
| `POST` | `/api/v1/vision/captures` | Ingest base64 PNG/BMP/JPEG or metadata capture + UI bounding boxes |
| `POST` | `/api/v1/vision/captures/{capture_id}/hit-test` | Spatial `(x, y)` hit-test returning matched elements sorted smallest-first |
| `POST` | `/api/v1/vision/captures/{capture_id}/query` | Grounded screen Q&A over indexed UI elements & OCR text |
| `GET` | `/api/v1/vision/queries` | List screen Q&A history (optional `?capture_id=`) |
| `WS` | `/api/v1/vision/ws/captures` | Live status & heartbeat WebSocket stream |
