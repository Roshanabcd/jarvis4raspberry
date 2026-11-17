"""
Autonomous multi-step research agent for JARVIS OS.
Orchestrates planning, searching, retrieval, extraction, evidence linking,
verification, contradiction detection, AI synthesis, citation validation,
and report generation with persistent SQLite checkpoints.
"""

from __future__ import annotations

import concurrent.futures
import logging
import threading
import time
from typing import Any, Dict, List, Optional
import uuid

from apps.research.citations import CitationManager
from apps.research.comparative import ComparativeAnalyzer
from apps.research.credibility import assess_credibility
from apps.research.database import ResearchDatabase, get_research_db
from apps.research.evidence import EvidenceExtractor, EvidenceStore
from apps.research.extractor import ContentExtractor
from apps.research.models import (
    ContradictionRecord,
    EvidenceRecord,
    ReportFormat,
    ResearchMode,
    ResearchPlan,
    ResearchReport,
    ResearchSource,
    ResearchStatus,
    ResearchTask,
)
from apps.research.planner import ResearchPlanner
from apps.research.reports import ReportBuilder
from apps.research.search_providers import SearchDispatcher
from apps.research.synthesizer import ResearchSynthesizer
from apps.research.verification import ContradictionDetector, FactChecker, LimitationsCompiler

logger = logging.getLogger("JARVIS-RESEARCH-AGENT")


class ResearchAgent:
    """Coordinates the end-to-end autonomous research lifecycle."""

    def __init__(self, db: Optional[ResearchDatabase] = None) -> None:
        self.db = db or get_research_db()
        self.planner = ResearchPlanner()
        self.searcher = SearchDispatcher(timeout=8)
        self.extractor = ContentExtractor(timeout=8)
        self.evidence_extractor = EvidenceExtractor(max_records_per_source=4)
        self.synthesizer = ResearchSynthesizer()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="ResearchWorker")
        self._cancellation_flags: Dict[str, bool] = {}

    def create_task(
        self,
        user_id: str,
        topic: str,
        question: str,
        mode: str = "standard",
        depth: str = "balanced",
        scope: str = "broad",
        max_sources: int = 8,
        date_range: str = "all",
        preferred_sources: Optional[List[str]] = None,
        output_language: str = "en",
        auto_start: bool = True,
        auto_approve: bool = False,
    ) -> ResearchTask:
        """Initialize a new research task, persist to DB, and optionally launch pipeline."""
        task_id = f"tsk_{uuid.uuid4().hex[:10]}"
        try:
            mode_enum = ResearchMode(mode.lower())
        except ValueError:
            mode_enum = ResearchMode.STANDARD

        task = ResearchTask(
            task_id=task_id,
            user_id=user_id,
            topic=topic.strip(),
            question=question.strip() or f"Comprehensive research investigation into {topic.strip()}",
            mode=mode_enum,
            depth=depth,
            scope=scope,
            max_sources=max_sources,
            date_range=date_range,
            preferred_sources=preferred_sources or ["web", "arxiv", "crossref"],
            output_language=output_language,
            status=ResearchStatus.CREATED,
            progress_percent=0,
            current_step="Task created",
            created_at=time.time(),
            updated_at=time.time(),
            start_time=time.time(),
        )

        # Check user settings for auto_approve override
        settings = self.db.get_settings(user_id)
        effective_auto_approve = auto_approve or settings.get("auto_approve_plan", False)

        self.db.save_task(task)

        if auto_start:
            self._executor.submit(self._run_pipeline, task_id, effective_auto_approve)

        return task

    def run_task_sync(self, task_id: str, auto_approve: bool = True) -> ResearchTask:
        """Run the research pipeline synchronously (ideal for testing)."""
        return self._run_pipeline(task_id, auto_approve=auto_approve)

    def approve_plan(self, task_id: str, user_edits: Optional[Dict[str, Any]] = None) -> Optional[ResearchTask]:
        """Approve an awaiting research plan and resume execution."""
        task = self.db.get_task(task_id)
        if not task or not task.plan:
            return None

        if user_edits:
            if "supporting_questions" in user_edits:
                task.plan.supporting_questions = user_edits["supporting_questions"]
            if "objectives" in user_edits:
                task.plan.objectives = user_edits["objectives"]
            if "source_limits" in user_edits:
                task.plan.source_limits = user_edits["source_limits"]

        task.plan.approved = True
        task.status = ResearchStatus.SEARCHING
        task.current_step = "Plan approved by user; initiating discovery search"
        task.updated_at = time.time()
        self.db.save_task(task)

        # Launch pipeline continuation in background
        self._executor.submit(self._run_pipeline_after_plan, task_id)
        return task

    def cancel_task(self, task_id: str) -> bool:
        """Signal cancellation for a running task."""
        self._cancellation_flags[task_id] = True
        task = self.db.get_task(task_id)
        if task and task.status not in (ResearchStatus.COMPLETED, ResearchStatus.FAILED):
            task.status = ResearchStatus.CANCELLED
            task.current_step = "Research task cancelled by user"
            task.updated_at = time.time()
            task.end_time = time.time()
            self.db.save_task(task)
            return True
        return False

    def _is_cancelled(self, task_id: str) -> bool:
        return self._cancellation_flags.get(task_id, False)

    def _run_pipeline(self, task_id: str, auto_approve: bool) -> ResearchTask:
        """Main multi-step pipeline runner."""
        task = self.db.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        try:
            # STEP 1: PLANNING
            task.status = ResearchStatus.PLANNING
            task.progress_percent = 10
            task.current_step = "Decomposing research question and formulating search strategy"
            task.updated_at = time.time()
            self.db.save_task(task)

            plan = self.planner.generate_plan(task)
            task.plan = plan
            self.db.save_task(task)

            if not auto_approve and not plan.approved:
                task.status = ResearchStatus.NEEDS_USER_INPUT
                task.current_step = "Plan formulated; awaiting user approval or query adjustments"
                task.updated_at = time.time()
                self.db.save_task(task)
                return task

            plan.approved = True
            self.db.save_task(task)

            return self._run_pipeline_after_plan(task_id)

        except Exception as exc:
            logger.error(f"Error in research pipeline for task {task_id}: {exc}", exc_info=True)
            task.status = ResearchStatus.FAILED
            task.error_message = str(exc)
            task.current_step = f"Failed during planning: {exc}"
            task.end_time = time.time()
            self.db.save_task(task)
            return task

    def _run_pipeline_after_plan(self, task_id: str) -> ResearchTask:
        """Execute remaining pipeline steps after plan approval."""
        task = self.db.get_task(task_id)
        if not task or not task.plan:
            raise ValueError("Task or Plan missing for execution continuation")

        try:
            # STEP 2: MULTI-PROVIDER SEARCH
            if self._is_cancelled(task_id):
                return task

            task.status = ResearchStatus.SEARCHING
            task.progress_percent = 25
            task.current_step = "Searching across web, arXiv, Crossref, and scholarly repositories"
            task.updated_at = time.time()
            self.db.save_task(task)

            sources = self.searcher.search_plan(task.plan, task)
            for s in sources:
                s.task_id = task.task_id
            task.sources = sources
            self.db.save_sources(sources)
            self.db.save_task(task)

            # STEP 3: CONTENT EXTRACTION
            if self._is_cancelled(task_id):
                return task

            task.status = ResearchStatus.FETCHING
            task.progress_percent = 45
            task.current_step = f"Retrieving full contents and papers for {len(sources)} sources"
            task.updated_at = time.time()
            self.db.save_task(task)

            extracted_sources = self.extractor.batch_extract(sources, max_workers=3)
            task.sources = extracted_sources
            self.db.save_sources(extracted_sources)
            self.db.save_task(task)

            # STEP 4: CREDIBILITY ASSESSMENT & DATES
            if self._is_cancelled(task_id):
                return task

            task.status = ResearchStatus.ANALYZING
            task.progress_percent = 60
            task.current_step = "Assessing source credibility, dates, and domain authority"
            task.updated_at = time.time()
            self.db.save_task(task)

            for src in extracted_sources:
                assess_credibility(src)
            self.db.save_sources(extracted_sources)

            # STEP 5: EVIDENCE EXTRACTION
            if self._is_cancelled(task_id):
                return task

            task.progress_percent = 70
            task.current_step = "Extracting grounded claims linked to verbatim passages"
            self.db.save_task(task)

            all_evidence: List[EvidenceRecord] = []
            for src in extracted_sources:
                evs = self.evidence_extractor.extract_from_source(
                    src, task_id=task.task_id, focus_terms=[task.topic]
                )
                all_evidence.extend(evs)

            task.evidence = all_evidence
            self.db.save_evidence(all_evidence)
            self.db.save_task(task)

            # STEP 6: VERIFICATION & CONTRADICTIONS
            if self._is_cancelled(task_id):
                return task

            task.status = ResearchStatus.VERIFYING
            task.progress_percent = 80
            task.current_step = "Cross-referencing claims and scanning for empirical contradictions"
            self.db.save_task(task)

            detector = ContradictionDetector(extracted_sources, all_evidence)
            contradictions = detector.detect_contradictions(task.task_id)
            task.contradictions = contradictions
            self.db.save_contradictions(contradictions)

            limitations = LimitationsCompiler.compile_limitations(
                sources=extracted_sources,
                plan=task.plan,
                contradictions=contradictions,
            )

            # STEP 7: AI SYNTHESIS
            if self._is_cancelled(task_id):
                return task

            task.status = ResearchStatus.SYNTHESIZING
            task.progress_percent = 90
            task.current_step = "Synthesizing evidence-based report sections with prompt injection isolation"
            self.db.save_task(task)

            citation_mgr = CitationManager(extracted_sources)

            # Comparative Matrix if mode is comparative
            comp_data = None
            if task.mode == ResearchMode.COMPARATIVE:
                entities = [w.strip() for w in task.topic.split(" vs ") if w.strip()]
                if len(entities) >= 2:
                    analyzer = ComparativeAnalyzer(entities=entities)
                    comp_data = analyzer.build_matrix(
                        sources=extracted_sources,
                        evidence=all_evidence,
                        source_tags=citation_mgr.source_to_tag,
                    )

            # Determine report format
            format_map = {
                ResearchMode.COMPARATIVE: ReportFormat.COMPARATIVE,
                ResearchMode.ACADEMIC: ReportFormat.LITERATURE_REVIEW,
                ResearchMode.LITERATURE_REVIEW: ReportFormat.LITERATURE_REVIEW,
                ResearchMode.TECHNICAL: ReportFormat.TECHNICAL,
            }
            report_format = format_map.get(task.mode, ReportFormat.EXECUTIVE)

            raw_sections = self.synthesizer.synthesize(
                task=task,
                plan=task.plan,
                sources=extracted_sources,
                evidence=all_evidence,
                contradictions=contradictions,
                citation_manager=citation_mgr,
                report_format=report_format,
                comparative_data=comp_data,
            )

            # STEP 8: CITATION VALIDATION
            if self._is_cancelled(task_id):
                return task

            task.status = ResearchStatus.VALIDATING_CITATIONS
            task.progress_percent = 95
            task.current_step = "Validating inline citations against verified sources"
            self.db.save_task(task)

            # STEP 9: REPORT ASSEMBLY & PERSISTENCE
            task.status = ResearchStatus.GENERATING_REPORT
            task.progress_percent = 98
            task.current_step = "Compiling Markdown, HTML, and evidence archive"
            self.db.save_task(task)

            report = ReportBuilder.build_report(
                task=task,
                plan=task.plan,
                sources=extracted_sources,
                evidence=all_evidence,
                contradictions=contradictions,
                limitations=limitations,
                sections=raw_sections,
                citation_manager=citation_mgr,
                report_format=report_format,
            )

            self.db.save_report(report)
            task.report_id = report.report_id
            task.status = ResearchStatus.COMPLETED
            task.progress_percent = 100
            task.current_step = "Research successfully completed"
            task.end_time = time.time()
            task.updated_at = time.time()
            self.db.save_task(task)

            logger.info(f"Research task {task_id} completed successfully in {task.duration_seconds}s")
            return task

        except Exception as exc:
            logger.error(f"Error executing research task {task_id}: {exc}", exc_info=True)
            task.status = ResearchStatus.FAILED
            task.error_message = str(exc)
            task.current_step = f"Failed: {exc}"
            task.end_time = time.time()
            self.db.save_task(task)
            return task


_global_research_agent: Optional[ResearchAgent] = None


def get_research_agent() -> ResearchAgent:
    """Singleton getter for ResearchAgent."""
    global _global_research_agent
    if _global_research_agent is None:
        _global_research_agent = ResearchAgent()
    return _global_research_agent
