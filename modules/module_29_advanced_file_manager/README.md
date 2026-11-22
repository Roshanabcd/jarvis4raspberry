# JARVIS OS — Module 29: Advanced File Manager (`v1.0.0`)

An independent, portable, integration-ready sandboxed file manager for JARVIS OS. Provides path-traversal-safe directory browsing and CRUD, soft-delete trash with one-click restore, SHA-256 duplicate scanning, dry-run/live smart auto-organization, filename & content search, metadata tagging, and persistent audit logs in an isolated SQLite WAL database.

## Core Capabilities
- **Sandboxed File Operations**: All reads, writes, moves, and deletes are strictly jailed inside `JARVIS_M29_ROOT_DIR` (`./data/managed_files`) via canonical path validation (`403 PATH_TRAVERSAL_BLOCKED` on escape attempts).
- **Soft-Delete Trash & Restore**: Deleted files move into `_trash/` with SQLite metadata so they can be restored to their original paths.
- **SHA-256 Duplicate Scanner**: Computes real SHA-256 digests across managed files and reports exact duplicate groups plus reclaimable bytes.
- **Smart Auto-Organizer**: Preview (`dry_run=True`) or execute automatic sorting of loose root files into `documents/`, `code/`, `data/`, `media/`, `archives/`, and `other/`.
- **Search, Tagging & Audit Trail**: Search by filename and text content, attach persistent tags, and inspect audit history.

## Quick Start
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8129/file-manager` for the built-in zero-build JARVIS Control UI.

## Running Tests & Demo
```bash
bash scripts/test.sh
python3 examples/run_file_manager_demo.py
```

## Integrating Into JARVIS OS
```python
from backend.app.main import mount_module
mount_module(app)  # Mounts /api/v1/file-manager/* and /file-manager
```
