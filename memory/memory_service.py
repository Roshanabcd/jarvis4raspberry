"""
JARVIS OS — Memory Service Layer.

Provides user-facing memory operations on top of ``MemoryDB``:

* Persistent storage and retrieval (categories, tags, importance).
* Configurable semantic retrieval via ``memory/vector/semantic_search.py``.
* Memory correction (update) with audit trail.
* Memory deletion controls — destructive operations require explicit
  confirmation and are audited; nothing is ever removed silently.
* Privacy redaction — secrets/keys are stripped from returned content so
  callers never leak credentials through memory results.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

from memory.long_term.database import db as _default_db
from memory.vector.semantic_search import semantic_search as _default_semantic

logger = logging.getLogger("JARVIS.Memory.Service")

_SECRET_RE = re.compile(
    r"(api[_-]?key|secret|token|password|passwd|credential|private[_-]?key)\s*[:=]\s*\\?['\"]?([^\\'\"\s,}]+)",
    re.IGNORECASE,
)


def _redact(content: str) -> str:
    """Redact potential secrets from memory content before returning it."""
    return _SECRET_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", content)


class MemoryService:
    """User-facing service for persistent, auditable memory operations."""

    def __init__(self, db=None, semantic=None) -> None:
        self.db = db or _default_db
        self.semantic = semantic or _default_semantic
        self._audit: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Status / configuration
    # ------------------------------------------------------------------ #
    def status(self) -> Dict[str, Any]:
        """Return non-sensitive service status and semantic-search config."""
        return {
            "database": self.db.db_path,
            "categories": sorted(self.db.VALID_CATEGORIES),
            "semantic": self.semantic.status(),
        }

    # ------------------------------------------------------------------ #
    # Persistent storage (create)
    # ------------------------------------------------------------------ #
    def store(self, category: str, content: str,
              key: Optional[str] = None,
              tags: Optional[List[str]] = None,
              importance: int = 5) -> Dict[str, Any]:
        """Store a memory. Returns the new record (redacted)."""
        if category not in self.db.VALID_CATEGORIES:
            return {"success": False, "error": f"Invalid category '{category}'"}
        try:
            row_id = self.db.store(
                category=category, content=content, key=key,
                tags=tags, importance=importance,
            )
            self._audit.append({
                "ts": time.time(), "action": "store",
                "category": category, "memory_id": row_id,
            })
            return {
                "success": True, "memory_id": row_id,
                "content": _redact(content),
                "category": category,
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Memory store failed: %s", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Retrieval (keyword + optional semantic)
    # ------------------------------------------------------------------ #
    def search(self, query: str = "", category: Optional[str] = None,
               limit: int = 20, semantic: Optional[bool] = None) -> Dict[str, Any]:
        """Search memories.

        When ``semantic`` is None the configured default is used.  Results are
        redacted so secrets are never returned to callers.
        """
        use_semantic = self.semantic.enabled if semantic is None else bool(semantic)
        if use_semantic:
            results = self.semantic.search(
                query=query, category=category, limit=limit,
            )
        else:
            results = self.db.search(
                query=query, category=category, limit=limit,
            )
            for r in results:
                r.setdefault("semantic", False)

        for r in results:
            r["content"] = _redact(r.get("content", ""))
            # Stable alias so callers can reference records by memory_id
            if "memory_id" not in r and "id" in r:
                r["memory_id"] = r["id"]

        return {
            "success": True,
            "query": query,
            "category": category,
            "semantic_used": use_semantic,
            "count": len(results),
            "results": results,
        }

    def retrieve_context(self, category: str = "CONVERSATION",
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent context entries (redacted)."""
        results = self.db.retrieve_context(category=category, limit=limit)
        for r in results:
            r["content"] = _redact(r.get("content", ""))
            if "memory_id" not in r and "id" in r:
                r["memory_id"] = r["id"]
        return results

    def get_session_messages(self, session_id: str,
                             limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve historical conversation turns for a session (redacted)."""
        messages = self.db.get_session_messages(session_id=session_id, limit=limit)
        for m in messages:
            m["content"] = _redact(m.get("content", ""))

    def correct(self, memory_id: int, content: str,
                importance: Optional[int] = None) -> Dict[str, Any]:
        """Correct an existing memory by id. Audited; returns redacted record."""
        # Verify the memory exists before allowing a correction.
        with self.db._get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        if row is None:
            return {"success": False, "error": f"Memory id={memory_id} not found"}
        ok = self.db.update(memory_id, content, importance=importance)
        if not ok:
            return {"success": False, "error": f"Memory id={memory_id} not updated"}
        self._audit.append({
            "ts": time.time(), "action": "correct",
            "memory_id": memory_id,
        })
        return {"success": True, "memory_id": memory_id,
                "content": _redact(content)}

    # ------------------------------------------------------------------ #
    # Deletion controls — confirmation required, audited
    # ------------------------------------------------------------------ #
    def delete(self, memory_id: int, confirmed: bool = False) -> Dict[str, Any]:
        """Delete a memory by id.

        Deletion requires ``confirmed=True`` and is always audited.  Returns
        the redacted content of what was deleted so the caller has a record,
        without exposing secrets.
        """
        if not confirmed:
            return {
                "success": False,
                "error": "Deletion requires explicit confirmation (confirmed=True)",
                "requires_confirmation": True,
            }
        # Snapshot before deleting for the audit trail (redacted).
        with self.db._get_conn() as conn:
            row = conn.execute(
                "SELECT category, content FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        if row is None:
            return {"success": False, "error": f"Memory id={memory_id} not found"}
        ok = self.db.delete(memory_id)
        if not ok:
            return {"success": False, "error": f"Memory id={memory_id} not deleted"}
        self._audit.append({
            "ts": time.time(), "action": "delete",
            "memory_id": memory_id, "category": row["category"],
        })
        return {
            "success": True, "memory_id": memory_id,
            "content": _redact(row["content"]),
        }

    # ------------------------------------------------------------------ #
    # Audit / inspection
    # ------------------------------------------------------------------ #
    def get_audit(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent service-level audit entries (no secret content)."""
        return list(self._audit[-limit:])

    def summarize(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Return counts and recent entries for inspection (no content)."""
        return self.db.summarize(category=category)


# Module-level singleton bound to the default database.
memory_service = MemoryService()