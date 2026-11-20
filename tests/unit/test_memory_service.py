"""
Tests for the JARVIS Memory Service layer (Workstream A — Memory).

Covers: persistence, keyword + semantic retrieval, privacy redaction,
memory correction, confirmation-gated deletion, and auditing.
All tests use a throwaway SQLite database so real user data is never touched.
"""
import os
import tempfile

import pytest

from memory.long_term.database import MemoryDB
from memory.memory_service import MemoryService, _redact
from memory.vector.semantic_search import SemanticMemorySearch


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def mem_db():
    """A MemoryDB backed by a temporary SQLite file."""
    with tempfile.TemporaryDirectory() as td:
        yield MemoryDB(db_path=os.path.join(td, "test_memory.db"))


@pytest.fixture
def mem_service(mem_db):
    """A MemoryService backed by the temporary database (semantic disabled)."""
    semantic = SemanticMemorySearch(db=mem_db, enabled=False)
    return MemoryService(db=mem_db, semantic=semantic)


# --------------------------------------------------------------------------- #
# Privacy redaction
# --------------------------------------------------------------------------- #
def test_redact_strips_secrets():
    """Secrets must never leak through memory results."""
    assert "[REDACTED]" in _redact("api_key=sk-1234567890")
    assert "sk-1234567890" not in _redact("api_key=sk-1234567890")
    assert "[REDACTED]" in _redact("password=supersecret")
    assert "supersecret" not in _redact("password=supersecret")
    # Non-secret content passes through unchanged
    assert _redact("My preferred editor is vim.") == "My preferred editor is vim."


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def test_store_and_search_persistence(mem_service):
    """Stored memories survive and are retrievable by keyword."""
    r = mem_service.store("USER", "I prefer dark mode", key="ui_theme",
                          tags=["preference"], importance=7)
    assert r["success"] is True
    mid = r["memory_id"]

    res = mem_service.search("dark mode", category="USER", limit=5)
    assert res["count"] >= 1
    assert any(x["memory_id"] == mid for x in res["results"])

    # Retrieving context returns stored items
    ctx = mem_service.retrieve_context(category="USER", limit=10)
    assert any(x["memory_id"] == mid for x in ctx)


def test_invalid_category_rejected(mem_service):
    """Invalid categories are rejected without writing."""
    r = mem_service.store("NOT_A_CATEGORY", "some content")
    assert r["success"] is False


# --------------------------------------------------------------------------- #
# Privacy on retrieval
# --------------------------------------------------------------------------- #
def test_search_redacts_secrets(mem_service):
    """Search results must have secrets redacted."""
    mem_service.store("USER", "my token=abcdef123456", key="tok", importance=5)
    res = mem_service.search("token", category="USER", limit=5)
    for x in res["results"]:
        assert "abcdef123456" not in x["content"]


# --------------------------------------------------------------------------- #
# Correction
# --------------------------------------------------------------------------- #
def test_correct_updates_memory(mem_service):
    """Correction updates content and is audited."""
    r = mem_service.store("USER", "original value", key="k1", importance=5)
    mid = r["memory_id"]

    c = mem_service.correct(mid, "corrected value", importance=9)
    assert c["success"] is True
    assert c["content"] == "corrected value"

    audit = mem_service.get_audit()
    assert any(a["action"] == "correct" and a["memory_id"] == mid for a in audit)


def test_correct_nonexistent(mem_service):
    """Correcting a missing memory reports failure."""
    c = mem_service.correct(999999, "whatever")
    assert c["success"] is False


# --------------------------------------------------------------------------- #
# Deletion controls
# --------------------------------------------------------------------------- #
def test_delete_requires_confirmation(mem_service):
    """Deletion without confirmation is rejected."""
    r = mem_service.store("USER", "to be deleted", key="delme", importance=5)
    mid = r["memory_id"]

    d = mem_service.delete(mid, confirmed=False)
    assert d["success"] is False
    assert d.get("requires_confirmation") is True

    # Memory still exists
    res = mem_service.search("to be deleted", category="USER", limit=5)
    assert res["count"] >= 1


def test_delete_with_confirmation_removes(mem_service):
    """Confirmed deletion removes the memory and audits it."""
    r = mem_service.store("USER", "temporary data", key="delme2", importance=5)
    mid = r["memory_id"]

    d = mem_service.delete(mid, confirmed=True)
    assert d["success"] is True
    assert d["content"] == "temporary data"

    res = mem_service.search("temporary", category="USER", limit=5)
    assert res["count"] == 0

    audit = mem_service.get_audit()
    assert any(a["action"] == "delete" and a["memory_id"] == mid for a in audit)


def test_delete_nonexistent(mem_service):
    """Deleting a missing memory reports failure."""
    d = mem_service.delete(999999, confirmed=True)
    assert d["success"] is False


# --------------------------------------------------------------------------- #
# Semantic retrieval
# --------------------------------------------------------------------------- #
def test_semantic_search_reranks(mem_db):
    """Semantic search returns results flagged as semantic when enabled."""
    semantic = SemanticMemorySearch(db=mem_db, enabled=True, similarity_threshold=0.0)
    svc = MemoryService(db=mem_db, semantic=semantic)

    svc.store("KNOWLEDGE", "The capital of France is Paris", key="geo1", importance=5)
    svc.store("KNOWLEDGE", "Python is a programming language", key="geo2", importance=5)

    res = svc.search("capital city", category="KNOWLEDGE", limit=5, semantic=True)
    assert res["semantic_used"] is True
    assert res["count"] >= 1
    # Every result must carry a similarity score when semantic
    for x in res["results"]:
        assert x.get("semantic") is True
        assert "similarity" in x


def test_semantic_disabled_falls_back(mem_db):
    """With semantic disabled, results carry semantic=False."""
    semantic = SemanticMemorySearch(db=mem_db, enabled=False)
    svc = MemoryService(db=mem_db, semantic=semantic)
    svc.store("KNOWLEDGE", "hello world example", key="hw", importance=5)

    res = svc.search("hello", category="KNOWLEDGE", limit=5, semantic=False)
    assert res["semantic_used"] is False
    for x in res["results"]:
        assert x.get("semantic") is False