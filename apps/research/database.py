"""
SQLite database storage layer for JARVIS AI Research Assistant.
Provides WAL-mode ACID storage for tasks, plans, sources, evidence,
contradictions, reports, and user settings.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from apps.research.models import (
    ContradictionRecord,
    EvidenceRecord,
    ExtractionStatus,
    ReportFormat,
    ResearchMode,
    ResearchPlan,
    ResearchQuery,
    ResearchReport,
    ResearchSource,
    ResearchStatus,
    ResearchTask,
    SourceCategory,
    SupportLevel,
)

logger = logging.getLogger("JARVIS-RESEARCH-DB")

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "research_assistant.sqlite3")
)


class ResearchDatabase:
    """Thread-safe SQLite storage for JARVIS AI Research Assistant."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            self._local.conn = conn
        return self._local.conn

    def _init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        conn = self._get_conn()
        with conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS research_tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    question TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    depth TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    max_sources INTEGER NOT NULL,
                    date_range TEXT NOT NULL,
                    preferred_sources_json TEXT NOT NULL,
                    output_language TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percent INTEGER NOT NULL,
                    current_step TEXT NOT NULL,
                    plan_json TEXT,
                    report_id TEXT,
                    error_message TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    start_time REAL,
                    end_time REAL
                );

                CREATE TABLE IF NOT EXISTS research_sources (
                    source_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    authors_json TEXT NOT NULL,
                    publisher_or_domain TEXT,
                    published_date TEXT,
                    retrieved_at REAL NOT NULL,
                    category TEXT NOT NULL,
                    extraction_status TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    doi TEXT,
                    is_abstract_only INTEGER NOT NULL,
                    citation_count INTEGER NOT NULL,
                    raw_metadata_json TEXT,
                    FOREIGN KEY(task_id) REFERENCES research_tasks(task_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS evidence_records (
                    evidence_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    supporting_passage TEXT NOT NULL,
                    support_level TEXT NOT NULL,
                    confidence_notes TEXT,
                    FOREIGN KEY(task_id) REFERENCES research_tasks(task_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS contradictions (
                    contradiction_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    claim_a TEXT NOT NULL,
                    source_a_id TEXT NOT NULL,
                    claim_b TEXT NOT NULL,
                    source_b_id TEXT NOT NULL,
                    analysis TEXT NOT NULL,
                    unresolved INTEGER NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES research_tasks(task_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS research_reports (
                    report_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    research_date TEXT NOT NULL,
                    research_question TEXT NOT NULL,
                    report_format TEXT NOT NULL,
                    sections_json TEXT NOT NULL,
                    markdown_content TEXT NOT NULL,
                    html_content TEXT NOT NULL,
                    references_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES research_tasks(task_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS research_settings (
                    user_id TEXT PRIMARY KEY,
                    default_mode TEXT NOT NULL,
                    default_max_sources INTEGER NOT NULL,
                    auto_approve_plan INTEGER NOT NULL,
                    preferred_providers_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_user ON research_tasks(user_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON research_tasks(status);
                CREATE INDEX IF NOT EXISTS idx_sources_task ON research_sources(task_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_task ON evidence_records(task_id);
                CREATE INDEX IF NOT EXISTS idx_reports_user ON research_reports(user_id);
                """
            )

    # Task Operations
    def save_task(self, task: ResearchTask) -> None:
        conn = self._get_conn()
        plan_json = json.dumps(task.plan.to_dict()) if task.plan else None
        pref_json = json.dumps(task.preferred_sources)

        with conn:
            conn.execute(
                """
                INSERT INTO research_tasks (
                    task_id, user_id, topic, question, mode, depth, scope,
                    max_sources, date_range, preferred_sources_json, output_language,
                    status, progress_percent, current_step, plan_json, report_id,
                    error_message, created_at, updated_at, start_time, end_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    topic=excluded.topic,
                    question=excluded.question,
                    mode=excluded.mode,
                    depth=excluded.depth,
                    scope=excluded.scope,
                    max_sources=excluded.max_sources,
                    date_range=excluded.date_range,
                    preferred_sources_json=excluded.preferred_sources_json,
                    output_language=excluded.output_language,
                    status=excluded.status,
                    progress_percent=excluded.progress_percent,
                    current_step=excluded.current_step,
                    plan_json=excluded.plan_json,
                    report_id=excluded.report_id,
                    error_message=excluded.error_message,
                    updated_at=excluded.updated_at,
                    start_time=excluded.start_time,
                    end_time=excluded.end_time;
                """,
                (
                    task.task_id,
                    task.user_id,
                    task.topic,
                    task.question,
                    task.mode.value if isinstance(task.mode, ResearchMode) else task.mode,
                    task.depth,
                    task.scope,
                    task.max_sources,
                    task.date_range,
                    pref_json,
                    task.output_language,
                    task.status.value if isinstance(task.status, ResearchStatus) else task.status,
                    task.progress_percent,
                    task.current_step,
                    plan_json,
                    task.report_id,
                    task.error_message,
                    task.created_at,
                    task.updated_at,
                    task.start_time,
                    task.end_time,
                ),
            )

    def get_task(self, task_id: str) -> Optional[ResearchTask]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM research_tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            return None

        # Reconstruct ResearchPlan
        plan = None
        if row["plan_json"]:
            try:
                p_data = json.loads(row["plan_json"])
                queries = [ResearchQuery(**q) for q in p_data.get("planned_queries", [])]
                p_data["planned_queries"] = queries
                plan = ResearchPlan(**p_data)
            except Exception as exc:
                logger.warning(f"Error parsing plan_json for task {task_id}: {exc}")

        task = ResearchTask(
            task_id=row["task_id"],
            user_id=row["user_id"],
            topic=row["topic"],
            question=row["question"],
            mode=ResearchMode(row["mode"]),
            depth=row["depth"],
            scope=row["scope"],
            max_sources=row["max_sources"],
            date_range=row["date_range"],
            preferred_sources=json.loads(row["preferred_sources_json"]),
            output_language=row["output_language"],
            status=ResearchStatus(row["status"]),
            progress_percent=row["progress_percent"],
            current_step=row["current_step"],
            plan=plan,
            report_id=row["report_id"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            start_time=row["start_time"],
            end_time=row["end_time"],
        )

        task.sources = self.get_sources_for_task(task_id)
        task.evidence = self.get_evidence_for_task(task_id)
        task.contradictions = self.get_contradictions_for_task(task_id)

        return task

    def list_tasks(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT task_id, user_id, topic, question, mode, status, progress_percent,
                   current_step, report_id, created_at, updated_at
            FROM research_tasks
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?;
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # Source Operations
    def save_sources(self, sources: List[ResearchSource]) -> None:
        if not sources:
            return
        conn = self._get_conn()
        with conn:
            for s in sources:
                conn.execute(
                    """
                    INSERT INTO research_sources (
                        source_id, task_id, url, title, authors_json, publisher_or_domain,
                        published_date, retrieved_at, category, extraction_status, content,
                        summary, doi, is_abstract_only, citation_count, raw_metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_id) DO UPDATE SET
                        title=excluded.title,
                        authors_json=excluded.authors_json,
                        publisher_or_domain=excluded.publisher_or_domain,
                        published_date=excluded.published_date,
                        category=excluded.category,
                        extraction_status=excluded.extraction_status,
                        content=excluded.content,
                        summary=excluded.summary,
                        doi=excluded.doi,
                        is_abstract_only=excluded.is_abstract_only,
                        citation_count=excluded.citation_count,
                        raw_metadata_json=excluded.raw_metadata_json;
                    """,
                    (
                        s.source_id,
                        s.task_id,
                        s.url,
                        s.title,
                        json.dumps(s.authors),
                        s.publisher_or_domain,
                        s.published_date,
                        s.retrieved_at,
                        s.category.value if isinstance(s.category, SourceCategory) else s.category,
                        s.extraction_status.value if isinstance(s.extraction_status, ExtractionStatus) else s.extraction_status,
                        s.content,
                        s.summary,
                        s.doi,
                        1 if s.is_abstract_only else 0,
                        s.citation_count,
                        json.dumps(s.raw_metadata),
                    ),
                )

    def get_sources_for_task(self, task_id: str) -> List[ResearchSource]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM research_sources WHERE task_id = ?", (task_id,)).fetchall()
        sources: List[ResearchSource] = []
        for r in rows:
            sources.append(
                ResearchSource(
                    source_id=r["source_id"],
                    task_id=r["task_id"],
                    url=r["url"],
                    title=r["title"],
                    authors=json.loads(r["authors_json"]),
                    publisher_or_domain=r["publisher_or_domain"],
                    published_date=r["published_date"],
                    retrieved_at=r["retrieved_at"],
                    category=SourceCategory(r["category"]),
                    extraction_status=ExtractionStatus(r["extraction_status"]),
                    content=r["content"],
                    summary=r["summary"],
                    doi=r["doi"],
                    is_abstract_only=bool(r["is_abstract_only"]),
                    citation_count=r["citation_count"],
                    raw_metadata=json.loads(r["raw_metadata_json"] or "{}"),
                )
            )
        return sources

    # Evidence Operations
    def save_evidence(self, records: List[EvidenceRecord]) -> None:
        if not records:
            return
        conn = self._get_conn()
        with conn:
            for r in records:
                conn.execute(
                    """
                    INSERT INTO evidence_records (
                        evidence_id, task_id, source_id, claim, supporting_passage,
                        support_level, confidence_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(evidence_id) DO UPDATE SET
                        claim=excluded.claim,
                        supporting_passage=excluded.supporting_passage,
                        support_level=excluded.support_level,
                        confidence_notes=excluded.confidence_notes;
                    """,
                    (
                        r.evidence_id,
                        r.task_id,
                        r.source_id,
                        r.claim,
                        r.supporting_passage,
                        r.support_level.value if isinstance(r.support_level, SupportLevel) else r.support_level,
                        r.confidence_notes,
                    ),
                )

    def get_evidence_for_task(self, task_id: str) -> List[EvidenceRecord]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM evidence_records WHERE task_id = ?", (task_id,)).fetchall()
        records: List[EvidenceRecord] = []
        for r in rows:
            records.append(
                EvidenceRecord(
                    evidence_id=r["evidence_id"],
                    task_id=r["task_id"],
                    source_id=r["source_id"],
                    claim=r["claim"],
                    supporting_passage=r["supporting_passage"],
                    support_level=SupportLevel(r["support_level"]),
                    confidence_notes=r["confidence_notes"],
                )
            )
        return records

    # Contradictions Operations
    def save_contradictions(self, records: List[ContradictionRecord]) -> None:
        if not records:
            return
        conn = self._get_conn()
        with conn:
            for c in records:
                conn.execute(
                    """
                    INSERT INTO contradictions (
                        contradiction_id, task_id, topic, claim_a, source_a_id,
                        claim_b, source_b_id, analysis, unresolved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(contradiction_id) DO UPDATE SET
                        topic=excluded.topic,
                        claim_a=excluded.claim_a,
                        claim_b=excluded.claim_b,
                        analysis=excluded.analysis,
                        unresolved=excluded.unresolved;
                    """,
                    (
                        c.contradiction_id,
                        c.task_id,
                        c.topic,
                        c.claim_a,
                        c.source_a_id,
                        c.claim_b,
                        c.source_b_id,
                        c.analysis,
                        1 if c.unresolved else 0,
                    ),
                )

    def get_contradictions_for_task(self, task_id: str) -> List[ContradictionRecord]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM contradictions WHERE task_id = ?", (task_id,)).fetchall()
        recs: List[ContradictionRecord] = []
        for r in rows:
            recs.append(
                ContradictionRecord(
                    contradiction_id=r["contradiction_id"],
                    task_id=r["task_id"],
                    topic=r["topic"],
                    claim_a=r["claim_a"],
                    source_a_id=r["source_a_id"],
                    claim_b=r["claim_b"],
                    source_b_id=r["source_b_id"],
                    analysis=r["analysis"],
                    unresolved=bool(r["unresolved"]),
                )
            )
        return recs

    # Report Operations
    def save_report(self, report: ResearchReport) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO research_reports (
                    report_id, task_id, user_id, title, research_date, research_question,
                    report_format, sections_json, markdown_content, html_content,
                    references_json, limitations_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(report_id) DO UPDATE SET
                    title=excluded.title,
                    research_date=excluded.research_date,
                    report_format=excluded.report_format,
                    sections_json=excluded.sections_json,
                    markdown_content=excluded.markdown_content,
                    html_content=excluded.html_content,
                    references_json=excluded.references_json,
                    limitations_json=excluded.limitations_json,
                    updated_at=excluded.updated_at;
                """,
                (
                    report.report_id,
                    report.task_id,
                    report.user_id,
                    report.title,
                    report.research_date,
                    report.research_question,
                    report.report_format.value if isinstance(report.report_format, ReportFormat) else report.report_format,
                    json.dumps(report.sections),
                    report.markdown_content,
                    report.html_content,
                    json.dumps(report.references),
                    json.dumps(report.limitations),
                    report.created_at,
                    report.updated_at,
                ),
            )

    def get_report(self, report_id: str) -> Optional[ResearchReport]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM research_reports WHERE report_id = ?", (report_id,)).fetchone()
        if not row:
            return None
        return ResearchReport(
            report_id=row["report_id"],
            task_id=row["task_id"],
            user_id=row["user_id"],
            title=row["title"],
            research_date=row["research_date"],
            research_question=row["research_question"],
            report_format=ReportFormat(row["report_format"]),
            sections=json.loads(row["sections_json"]),
            markdown_content=row["markdown_content"],
            html_content=row["html_content"],
            references=json.loads(row["references_json"]),
            limitations=json.loads(row["limitations_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_reports(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT report_id, task_id, user_id, title, research_date, report_format, created_at
            FROM research_reports
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?;
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # Settings Operations
    def get_settings(self, user_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM research_settings WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return {
                "user_id": user_id,
                "default_mode": "standard",
                "default_max_sources": 8,
                "auto_approve_plan": False,
                "preferred_providers": ["web", "arxiv", "crossref"],
                "updated_at": time.time(),
            }
        return {
            "user_id": row["user_id"],
            "default_mode": row["default_mode"],
            "default_max_sources": row["default_max_sources"],
            "auto_approve_plan": bool(row["auto_approve_plan"]),
            "preferred_providers": json.loads(row["preferred_providers_json"]),
            "updated_at": row["updated_at"],
        }

    def save_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT INTO research_settings (
                    user_id, default_mode, default_max_sources, auto_approve_plan,
                    preferred_providers_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    default_mode=excluded.default_mode,
                    default_max_sources=excluded.default_max_sources,
                    auto_approve_plan=excluded.auto_approve_plan,
                    preferred_providers_json=excluded.preferred_providers_json,
                    updated_at=excluded.updated_at;
                """,
                (
                    user_id,
                    settings.get("default_mode", "standard"),
                    settings.get("default_max_sources", 8),
                    1 if settings.get("auto_approve_plan") else 0,
                    json.dumps(settings.get("preferred_providers", ["web", "arxiv", "crossref"])),
                    time.time(),
                ),
            )


_global_research_db: Optional[ResearchDatabase] = None


def get_research_db() -> ResearchDatabase:
    """Singleton getter for ResearchDatabase."""
    global _global_research_db
    if _global_research_db is None:
        _global_research_db = ResearchDatabase()
    return _global_research_db
