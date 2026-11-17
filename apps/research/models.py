"""
Data models, enumerations, and state schemas for JARVIS AI Research Assistant.
"""
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List, Optional
import uuid


class ResearchMode(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    COMPARATIVE = "comparative"
    CURRENT_EVENTS = "current_events"
    LITERATURE_REVIEW = "literature_review"
    CUSTOM = "custom"


class ResearchStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    SEARCHING = "SEARCHING"
    FETCHING = "FETCHING"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    VERIFYING = "VERIFYING"
    SYNTHESIZING = "SYNTHESIZING"
    VALIDATING_CITATIONS = "VALIDATING_CITATIONS"
    GENERATING_REPORT = "GENERATING_REPORT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    NEEDS_USER_INPUT = "NEEDS_USER_INPUT"


class SourceCategory(str, Enum):
    PRIMARY_SOURCE = "PRIMARY_SOURCE"
    OFFICIAL_DOCUMENTATION = "OFFICIAL_DOCUMENTATION"
    PEER_REVIEWED_PAPER = "PEER_REVIEWED_PAPER"
    GOVERNMENT_SOURCE = "GOVERNMENT_SOURCE"
    INSTITUTIONAL_SOURCE = "INSTITUTIONAL_SOURCE"
    REPUTABLE_SECONDARY_SOURCE = "REPUTABLE_SECONDARY_SOURCE"
    NEWS_SOURCE = "NEWS_SOURCE"
    COMMUNITY_SOURCE = "COMMUNITY_SOURCE"
    UNVERIFIED_SOURCE = "UNVERIFIED_SOURCE"


class ExtractionStatus(str, Enum):
    FULL_CONTENT_RETRIEVED = "FULL_CONTENT_RETRIEVED"
    PARTIAL_CONTENT_RETRIEVED = "PARTIAL_CONTENT_RETRIEVED"
    METADATA_ONLY = "METADATA_ONLY"
    ABSTRACT_ONLY = "ABSTRACT_ONLY"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class SupportLevel(str, Enum):
    DIRECTLY_SUPPORTED = "DIRECTLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INFERRED = "INFERRED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ReportFormat(str, Enum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    LITERATURE_REVIEW = "literature_review"
    COMPARATIVE = "comparative"
    PROPOSAL = "proposal"
    MARKET_RESEARCH = "market_research"
    TECHNOLOGY_ASSESSMENT = "technology_assessment"
    CURRENT_DEVELOPMENTS = "current_developments"
    CUSTOM = "custom"


@dataclass
class ResearchQuery:
    query_id: str
    query_text: str
    target_provider: str = "auto"
    sub_question: str = ""
    executed: bool = False
    results_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "target_provider": self.target_provider,
            "sub_question": self.sub_question,
            "executed": self.executed,
            "results_count": self.results_count,
        }


@dataclass
class ResearchPlan:
    plan_id: str
    task_id: str
    main_question: str
    supporting_questions: List[str] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)
    planned_queries: List[ResearchQuery] = field(default_factory=list)
    source_requirements: List[str] = field(default_factory=list)
    date_constraints: str = ""
    expected_sections: List[str] = field(default_factory=list)
    source_limits: int = 10
    approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "main_question": self.main_question,
            "supporting_questions": self.supporting_questions,
            "objectives": self.objectives,
            "planned_queries": [q.to_dict() for q in self.planned_queries],
            "source_requirements": self.source_requirements,
            "date_constraints": self.date_constraints,
            "expected_sections": self.expected_sections,
            "source_limits": self.source_limits,
            "approved": self.approved,
        }


@dataclass
class ResearchSource:
    source_id: str
    task_id: str
    url: str
    title: str
    authors: List[str] = field(default_factory=list)
    publisher_or_domain: str = ""
    published_date: Optional[str] = None
    retrieved_at: float = field(default_factory=time.time)
    category: SourceCategory = SourceCategory.UNVERIFIED_SOURCE
    extraction_status: ExtractionStatus = ExtractionStatus.METADATA_ONLY
    content: str = ""
    summary: str = ""
    doi: Optional[str] = None
    is_abstract_only: bool = False
    citation_count: int = 0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "task_id": self.task_id,
            "url": self.url,
            "title": self.title,
            "authors": self.authors,
            "publisher_or_domain": self.publisher_or_domain,
            "published_date": self.published_date,
            "retrieved_at": self.retrieved_at,
            "retrieved_at_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.retrieved_at)),
            "category": self.category.value if isinstance(self.category, SourceCategory) else self.category,
            "extraction_status": self.extraction_status.value if isinstance(self.extraction_status, ExtractionStatus) else self.extraction_status,
            "content_preview": self.content[:300] + ("..." if len(self.content) > 300 else ""),
            "summary": self.summary,
            "doi": self.doi,
            "is_abstract_only": self.is_abstract_only,
            "citation_count": self.citation_count,
        }


@dataclass
class EvidenceRecord:
    evidence_id: str
    task_id: str
    source_id: str
    claim: str
    supporting_passage: str
    support_level: SupportLevel = SupportLevel.DIRECTLY_SUPPORTED
    confidence_notes: str = ""
    conflicting_evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "task_id": self.task_id,
            "source_id": self.source_id,
            "claim": self.claim,
            "supporting_passage": self.supporting_passage,
            "support_level": self.support_level.value if isinstance(self.support_level, SupportLevel) else self.support_level,
            "confidence_notes": self.confidence_notes,
            "conflicting_evidence_ids": self.conflicting_evidence_ids,
        }


@dataclass
class ContradictionRecord:
    contradiction_id: str
    task_id: str
    topic: str
    claim_a: str
    source_a_id: str
    claim_b: str
    source_b_id: str
    analysis: str
    unresolved: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id,
            "task_id": self.task_id,
            "topic": self.topic,
            "claim_a": self.claim_a,
            "source_a_id": self.source_a_id,
            "claim_b": self.claim_b,
            "source_b_id": self.source_b_id,
            "analysis": self.analysis,
            "unresolved": self.unresolved,
        }


@dataclass
class CitationRecord:
    citation_id: str
    source_id: str
    inline_tag: str  # e.g., "[1]" or "[Smith2026]"
    url: str
    title: str
    authors: List[str] = field(default_factory=list)
    year: Optional[str] = None
    publisher: str = ""
    doi: Optional[str] = None
    is_abstract_only: bool = False
    verified: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "source_id": self.source_id,
            "inline_tag": self.inline_tag,
            "url": self.url,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "publisher": self.publisher,
            "doi": self.doi,
            "is_abstract_only": self.is_abstract_only,
            "verified": self.verified,
        }


@dataclass
class ResearchReport:
    report_id: str
    task_id: str
    user_id: str
    title: str
    research_date: str
    research_question: str
    report_format: ReportFormat
    sections: List[Dict[str, str]] = field(default_factory=list)  # [{"title": ..., "content": ...}]
    markdown_content: str = ""
    html_content: str = ""
    references: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "title": self.title,
            "research_date": self.research_date,
            "research_question": self.research_question,
            "report_format": self.report_format.value if isinstance(self.report_format, ReportFormat) else self.report_format,
            "sections": self.sections,
            "markdown_content": self.markdown_content,
            "html_content": self.html_content,
            "references": self.references,
            "limitations": self.limitations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ResearchTask:
    task_id: str
    user_id: str
    topic: str
    question: str
    mode: ResearchMode = ResearchMode.STANDARD
    depth: str = "balanced"  # quick, balanced, deep
    scope: str = "broad"
    max_sources: int = 8
    date_range: str = "all"
    preferred_sources: List[str] = field(default_factory=lambda: ["web", "academic"])
    output_language: str = "en"
    status: ResearchStatus = ResearchStatus.CREATED
    progress_percent: int = 0
    current_step: str = "Initializing research task"
    plan: Optional[ResearchPlan] = None
    queries: List[ResearchQuery] = field(default_factory=list)
    sources: List[ResearchSource] = field(default_factory=list)
    evidence: List[EvidenceRecord] = field(default_factory=list)
    contradictions: List[ContradictionRecord] = field(default_factory=list)
    report_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration_seconds(self) -> float:
        return round((self.end_time or time.time()) - (self.start_time or self.created_at), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "topic": self.topic,
            "question": self.question,
            "mode": self.mode.value if isinstance(self.mode, ResearchMode) else self.mode,
            "depth": self.depth,
            "scope": self.scope,
            "max_sources": self.max_sources,
            "date_range": self.date_range,
            "preferred_sources": self.preferred_sources,
            "output_language": self.output_language,
            "status": self.status.value if isinstance(self.status, ResearchStatus) else self.status,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "plan": self.plan.to_dict() if self.plan else None,
            "queries_count": len(self.queries),
            "sources_count": len(self.sources),
            "evidence_count": len(self.evidence),
            "contradictions_count": len(self.contradictions),
            "report_id": self.report_id,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duration_seconds": self.duration_seconds,
        }
