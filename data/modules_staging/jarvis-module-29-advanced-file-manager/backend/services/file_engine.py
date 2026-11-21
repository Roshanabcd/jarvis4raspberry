"""Advanced File Manager Engine (Module 29).

Provides real sandboxed local filesystem operations:
- Path-traversal-safe directory browsing, file read/write, mkdir, move/rename
- Soft-delete trash (_trash/) with 1-click restore
- SHA-256 duplicate content scanner with reclaimable bytes calculation
- Smart auto-organizer with dry-run preview & live execution
- Filename + text content search & persistent metadata tags
- Full audit log trail in SQLite WAL
"""

from __future__ import annotations

import hashlib
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.adapters.classifier_adapter import FileClassifierAdapter, LocalRuleFileClassifierAdapter
from backend.app.config import FileManagerConfig
from backend.models.database import FileManagerDB


class FileManagerError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class FileManagerEngine:
    def __init__(
        self,
        config: Optional[FileManagerConfig] = None,
        db: Optional[FileManagerDB] = None,
        classifier: Optional[FileClassifierAdapter] = None,
    ) -> None:
        self.config = config or FileManagerConfig.from_env()
        self.config.ensure_dirs()
        self.root = Path(self.config.root_dir).resolve()
        self.db = db or FileManagerDB(self.config.db_path)
        self.classifier = classifier or LocalRuleFileClassifierAdapter()
        self._started_at = time.monotonic()

    def _resolve_safe(self, rel_path: str) -> Path:
        clean = rel_path.strip().lstrip("/")
        if clean in ("", "."):
            return self.root
        candidate = (self.root / clean).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise FileManagerError("PATH_TRAVERSAL_BLOCKED", f"Path '{rel_path}' escapes sandbox root.", 403)
        return candidate

    def _rel(self, p: Path) -> str:
        return p.resolve().relative_to(self.root).as_posix()

    def _audit(self, action: str, target_path: str, details: str) -> None:
        self.db.add_audit(f"aud_{uuid.uuid4().hex[:10]}", action, target_path, details)

    def list_files(self, rel_dir: str = "") -> Dict[str, Any]:
        target = self._resolve_safe(rel_dir)
        if not target.exists() or not target.is_dir():
            raise FileManagerError("DIR_NOT_FOUND", f"Directory '{rel_dir}' not found.", 404)
        tags_map = self.db.get_all_tags()
        entries: List[Dict[str, Any]] = []
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name == "_trash":
                continue
            rp = self._rel(item)
            stat = item.stat()
            entries.append(
                {
                    "name": item.name,
                    "rel_path": rp,
                    "is_dir": item.is_dir(),
                    "size_bytes": 0 if item.is_dir() else stat.st_size,
                    "category": "folder" if item.is_dir() else self.classifier.classify(item.name),
                    "tags": tags_map.get(rp, []),
                }
            )
        return {"dir": rel_dir or "/", "entries": entries, "count": len(entries)}

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        target = self._resolve_safe(rel_path)
        if target == self.root or "_trash" in target.relative_to(self.root).parts:
            raise FileManagerError("INVALID_TARGET", "Cannot write directly to root or _trash.", 400)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        rp = self._rel(target)
        self._audit("write_file", rp, f"Wrote {len(content.encode('utf-8'))} bytes")
        return {"rel_path": rp, "size_bytes": target.stat().st_size, "category": self.classifier.classify(target.name)}

    def read_file(self, rel_path: str) -> Dict[str, Any]:
        target = self._resolve_safe(rel_path)
        if not target.exists() or not target.is_file():
            raise FileManagerError("FILE_NOT_FOUND", f"File '{rel_path}' not found.", 404)
        text = target.read_text(encoding="utf-8", errors="replace")
        return {"rel_path": self._rel(target), "size_bytes": target.stat().st_size, "content": text}

    def create_dir(self, rel_path: str) -> Dict[str, Any]:
        target = self._resolve_safe(rel_path)
        target.mkdir(parents=True, exist_ok=True)
        rp = self._rel(target)
        self._audit("create_dir", rp, "Created directory")
        return {"rel_path": rp, "is_dir": True}

    def move_path(self, src_path: str, dst_path: str) -> Dict[str, Any]:
        src = self._resolve_safe(src_path)
        dst = self._resolve_safe(dst_path)
        if not src.exists():
            raise FileManagerError("FILE_NOT_FOUND", f"Source '{src_path}' not found.", 404)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        rp_src = src_path.strip().lstrip("/")
        rp_dst = self._rel(dst)
        self._audit("move", rp_dst, f"Moved from {rp_src}")
        return {"src_path": rp_src, "dst_path": rp_dst}

    def soft_delete(self, rel_path: str) -> Dict[str, Any]:
        src = self._resolve_safe(rel_path)
        if not src.exists() or not src.is_file():
            raise FileManagerError("FILE_NOT_FOUND", f"File '{rel_path}' not found.", 404)
        trash_id = f"tr_{uuid.uuid4().hex[:10]}"
        trash_dest = self.root / "_trash" / f"{trash_id}_{src.name}"
        shutil.move(str(src), str(trash_dest))
        rec = self.db.add_trash_item(trash_id, rel_path.strip().lstrip("/"), self._rel(trash_dest))
        self._audit("soft_delete", rec["original_rel_path"], f"Moved to trash ({trash_id})")
        return rec

    def restore_trash(self, trash_id: str) -> Dict[str, Any]:
        rec = self.db.get_trash_item(trash_id)
        if not rec:
            raise FileManagerError("TRASH_NOT_FOUND", f"Trash item '{trash_id}' not found.", 404)
        src = self._resolve_safe(rec["trash_rel_path"])
        dst = self._resolve_safe(rec["original_rel_path"])
        if not src.exists():
            raise FileManagerError("TRASH_FILE_MISSING", "Trash file no longer exists on disk.", 404)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        self.db.delete_trash_record(trash_id)
        self._audit("restore", rec["original_rel_path"], f"Restored from trash ({trash_id})")
        return {"restored_path": rec["original_rel_path"], "trash_id": trash_id}

    def find_duplicates(self) -> Dict[str, Any]:
        hashes: Dict[str, List[Dict[str, Any]]] = {}
        for p in self.root.rglob("*"):
            if not p.is_file() or "_trash" in p.relative_to(self.root).parts:
                continue
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            hashes.setdefault(h, []).append({"rel_path": self._rel(p), "size_bytes": p.stat().st_size})
        groups = []
        reclaimable = 0
        for digest, files in hashes.items():
            if len(files) > 1:
                groups.append({"sha256": digest, "files": files, "count": len(files)})
                reclaimable += files[0]["size_bytes"] * (len(files) - 1)
        return {"duplicate_groups": groups, "groups_count": len(groups), "reclaimable_bytes": reclaimable}

    def organize_root(self, dry_run: bool = True) -> Dict[str, Any]:
        plan: List[Dict[str, str]] = []
        for p in sorted(self.root.iterdir(), key=lambda x: x.name.lower()):
            if not p.is_file():
                continue
            cat = self.classifier.classify(p.name)
            dst = f"{cat}/{p.name}"
            plan.append({"src": p.name, "dst": dst, "category": cat})
            if not dry_run:
                self.move_path(p.name, dst)
        return {"dry_run": dry_run, "planned_moves": plan, "count": len(plan)}

    def search_files(self, query: str) -> Dict[str, Any]:
        q = query.strip().lower()
        hits: List[Dict[str, Any]] = []
        for p in self.root.rglob("*"):
            if not p.is_file() or "_trash" in p.relative_to(self.root).parts:
                continue
            rp = self._rel(p)
            matched_on = []
            if q in p.name.lower():
                matched_on.append("filename")
            try:
                if p.stat().st_size <= 200_000 and q in p.read_text(encoding="utf-8", errors="ignore").lower():
                    matched_on.append("content")
            except OSError:
                pass
            if matched_on:
                hits.append({"rel_path": rp, "size_bytes": p.stat().st_size, "matched_on": matched_on})
        return {"query": query, "results": hits, "count": len(hits)}

    def get_status(self) -> Dict[str, Any]:
        all_files = [p for p in self.root.rglob("*") if p.is_file() and "_trash" not in p.relative_to(self.root).parts]
        return {
            "adapter": self.classifier.adapter_name,
            "simulated": self.classifier.is_simulated,
            "files_count": len(all_files),
            "total_bytes": sum(p.stat().st_size for p in all_files),
            "trash_count": len(self.db.list_trash()),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }
