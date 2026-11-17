"""
JARVIS OS - Phase 12: Autonomous AI Research Assistant
"""
from apps.research.agent import ResearchAgent, get_research_agent
from apps.research.citations import CitationManager
from apps.research.comparative import ComparativeAnalyzer
from apps.research.credibility import assess_credibility, classify_category, disambiguate_dates
from apps.research.database import ResearchDatabase, get_research_db
from apps.research.evidence import EvidenceExtractor, EvidenceStore
from apps.research.extractor import ContentExtractor, SSRFSecurityError, validate_url_ssrf
from apps.research.models import (
    CitationRecord,
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
from apps.research.planner import ResearchPlanner
from apps.research.reports import ReportBuilder
from apps.research.search_providers import (
    ArxivProvider,
    CrossrefProvider,
    DuckDuckGoProvider,
    EuropePmcProvider,
    OpenAlexProvider,
    SearchDispatcher,
)
from apps.research.synthesizer import ResearchSynthesizer
from apps.research.verification import ContradictionDetector, FactChecker, LimitationsCompiler

__all__ = [
    "ResearchMode",
    "ResearchStatus",
    "SourceCategory",
    "ExtractionStatus",
    "SupportLevel",
    "ReportFormat",
    "ResearchQuery",
    "ResearchPlan",
    "ResearchSource",
    "EvidenceRecord",
    "ContradictionRecord",
    "CitationRecord",
    "ResearchReport",
    "ResearchTask",
    "ResearchPlanner",
    "SearchDispatcher",
    "DuckDuckGoProvider",
    "ArxivProvider",
    "CrossrefProvider",
    "OpenAlexProvider",
    "EuropePmcProvider",
    "ContentExtractor",
    "SSRFSecurityError",
    "validate_url_ssrf",
    "classify_category",
    "disambiguate_dates",
    "assess_credibility",
    "EvidenceExtractor",
    "EvidenceStore",
    "FactChecker",
    "ContradictionDetector",
    "LimitationsCompiler",
    "CitationManager",
    "ComparativeAnalyzer",
    "ResearchSynthesizer",
    "ReportBuilder",
    "ResearchDatabase",
    "get_research_db",
    "ResearchAgent",
    "get_research_agent",
]
