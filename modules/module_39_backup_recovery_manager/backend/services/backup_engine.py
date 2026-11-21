"""Local Sandboxed ZIP Snapshot Backup & Integrity-Verified Restore Engine (Module 39)."""

from __future__ import annotations

import hashlib
import os
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

from modules.module_39_backup_recovery_manager.backend.app.config import BackupConfig
from modules.module_39_backup_recovery_manager.backend.models.database import BackupDB, utc_now_iso


class BackupError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class BackupEngine:
    adapter_name: str = "local_snapshot_backup_engine"
    is_simulated: bool = False

    def __init__(self, config: Optional[BackupConfig] = None, db: Optional[BackupDB] = None) -> None:
        self.config = config or BackupConfig.from_env()
        self.config.ensure_dirs()
        self.sandbox_root = Path(self.config.sandbox_root).expanduser().resolve()
        self.archive_dir = Path(self.config.archive_dir).expanduser().resolve()
        self.db = db or BackupDB(self.config.db_path)
        self._started_at = time.monotonic()

    def _resolve_in_sandbox(self, rel_path: str) -> Path:
        raw = Path(rel_path)
        if raw.is_absolute():
            raise BackupError("PATH_OUTSIDE_SANDBOX", "Absolute paths are not permitted.", 403)
        target = (self.sandbox_root / raw).resolve()
        try:
            target.relative_to(self.sandbox_root)
        except ValueError as exc:
            raise BackupError("PATH_OUTSIDE_SANDBOX", f"Path '{rel_path}' escapes sandbox root.", 403) from exc
        return target

    def create_snapshot(self, name: str, source_rel_path: str = ".", notes: str = "") -> Dict[str, Any]:
        src = self._resolve_in_sandbox(source_rel_path)
        if not src.exists():
            raise BackupError("SOURCE_NOT_FOUND", f"Source path '{source_rel_path}' does not exist in sandbox.", 404)

        snapshot_id = f"snp_{uuid.uuid4().hex[:10]}"
        archive_filename = f"{snapshot_id}.zip"
        archive_path = self.archive_dir / archive_filename

        file_count = 0
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if src.is_file():
                zf.write(src, arcname=src.name)
                file_count = 1
            else:
                for root, dirs, files in os.walk(src):
                    dirs.sort()
                    for fname in sorted(files):
                        fpath = Path(root) / fname
                        arcname = str(fpath.relative_to(src))
                        zf.write(fpath, arcname=arcname)
                        file_count += 1

        digest = _sha256_file(archive_path)
        size = archive_path.stat().st_size

        return self.db.add_snapshot(
            {
                "snapshot_id": snapshot_id,
                "name": name.strip(),
                "source_rel_path": source_rel_path.strip(),
                "archive_filename": archive_filename,
                "file_count": file_count,
                "byte_size": size,
                "sha256": digest,
                "notes": notes.strip(),
                "created_at": utc_now_iso(),
            }
        )

    def verify_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        snap = self.db.get_snapshot(snapshot_id)
        if not snap:
            raise BackupError("SNAPSHOT_NOT_FOUND", f"Snapshot '{snapshot_id}' not found.", 404)
        archive_path = self.archive_dir / snap["archive_filename"]
        if not archive_path.is_file():
            return {
                "snapshot_id": snapshot_id,
                "valid": False,
                "reason": "Archive file missing on disk.",
                "expected_sha256": snap["sha256"],
                "actual_sha256": None,
            }
        actual_sha = _sha256_file(archive_path)
        if actual_sha != snap["sha256"]:
            return {
                "snapshot_id": snapshot_id,
                "valid": False,
                "reason": "SHA-256 digest mismatch.",
                "expected_sha256": snap["sha256"],
                "actual_sha256": actual_sha,
            }
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                bad = zf.testzip()
        except zipfile.BadZipFile:
            bad = "corrupt_zip_header"
        if bad is not None:
            return {
                "snapshot_id": snapshot_id,
                "valid": False,
                "reason": f"Corrupt ZIP entry: {bad}",
                "expected_sha256": snap["sha256"],
                "actual_sha256": actual_sha,
            }
        return {
            "snapshot_id": snapshot_id,
            "valid": True,
            "reason": "SHA-256 and ZIP CRC checks passed.",
            "expected_sha256": snap["sha256"],
            "actual_sha256": actual_sha,
        }

    def restore_snapshot(self, snapshot_id: str, target_rel_path: str) -> Dict[str, Any]:
        check = self.verify_snapshot(snapshot_id)
        if not check["valid"]:
            raise BackupError("SNAPSHOT_CORRUPTED", f"Cannot restore snapshot: {check['reason']}", 409)
        snap = self.db.get_snapshot(snapshot_id)
        assert snap is not None
        dest_dir = self._resolve_in_sandbox(target_rel_path)
        dest_dir.mkdir(parents=True, exist_ok=True)
        archive_path = self.archive_dir / snap["archive_filename"]

        restored = 0
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                out_path = (dest_dir / member.filename).resolve()
                try:
                    out_path.relative_to(dest_dir)
                except ValueError as exc:
                    raise BackupError("ZIP_SLIP_BLOCKED", f"Unsafe archive entry '{member.filename}'.", 422) from exc
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member, "r") as src_fh, out_path.open("wb") as dst_fh:
                    dst_fh.write(src_fh.read())
                restored += 1

        return self.db.add_restore_run(
            {
                "restore_id": f"rst_{uuid.uuid4().hex[:10]}",
                "snapshot_id": snapshot_id,
                "target_rel_path": target_rel_path.strip(),
                "restored_files": restored,
                "status": "completed",
                "created_at": utc_now_iso(),
            }
        )

    def get_status(self) -> Dict[str, Any]:
        snaps = self.db.list_snapshots(limit=500)
        restores = self.db.list_restores(limit=500)
        return {
            "adapter": self.adapter_name,
            "simulated": self.is_simulated,
            "snapshots_count": len(snaps),
            "restores_count": len(restores),
            "total_archive_bytes": sum(s["byte_size"] for s in snaps),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
