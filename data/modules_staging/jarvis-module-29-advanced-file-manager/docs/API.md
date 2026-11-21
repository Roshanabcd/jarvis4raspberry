# API Reference — Module 29: Advanced File Manager

Base prefix: `/api/v1/file-manager` (default standalone port: `8129`).

## Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Module liveness, version, contract version, and `simulated` flag (`false`) |
| `GET` | `/manifest` | Returns `manifest.json` metadata |
| `GET` | `/status` | File count, total bytes, trash count, classifier adapter, uptime |
| `GET` | `/files?dir=...` | List files and folders inside sandboxed `ROOT_DIR` |
| `POST` | `/files` | Create or overwrite a text file (`rel_path`, `content`) |
| `GET` | `/files/read?path=...` | Read text file content |
| `POST` | `/dirs` | Create a directory (`rel_path`) |
| `POST` | `/files/move` | Move or rename a file/directory (`src_path`, `dst_path`) |
| `DELETE` | `/files?path=...` | Soft-delete file into `_trash/` |
| `GET` | `/trash` | List soft-deleted items |
| `POST` | `/trash/{trash_id}/restore` | Restore a trashed file to its original path |
| `POST` | `/tags` | Attach persistent tags to a relative file path |
| `GET` | `/duplicates` | Run SHA-256 duplicate content scan |
| `POST` | `/organize` | Preview (`dry_run: true`) or execute (`dry_run: false`) smart root organization |
| `GET` | `/search?q=...` | Search filenames and text content |
| `GET` | `/audit` | View recent file operation audit logs |
| `WS` | `/ws/events` | Real-time status stream (`ws.connected` + `ws.heartbeat`) |
