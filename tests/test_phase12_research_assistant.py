"""
Comprehensive automated test suite for JARVIS OS Phase 12: Autonomous AI Research Assistant.
Covers models, planning, multi-provider search, content extraction, SSRF security defense,
credibility assessment, evidence linking, contradiction detection, citation validation,
synthesis, report generation, SQLite WAL persistence, agent lifecycle, FastAPI endpoints,
and voice intent routing.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from ai.local_engine import LocalIntelligenceEngine
from apps.api.research_api import get_current_user_identity
from apps.apps_center.permissions import AppRequestIdentity, UserRole
from apps.core.app_factory import create_app, noop_lifespan
from apps.research import (
    ArxivProvider,
    CitationManager,
    CitationRecord,
    ComparativeAnalyzer,
    ContentExtractor,
    ContradictionDetector,
    ContradictionRecord,
    CrossrefProvider,
    DuckDuckGoProvider,
    EuropePmcProvider,
    EvidenceExtractor,
    EvidenceRecord,
    EvidenceStore,
    ExtractionStatus,
    FactChecker,
    LimitationsCompiler,
    OpenAlexProvider,
    ReportBuilder,
    ReportFormat,
    ResearchAgent,
    ResearchDatabase,
    ResearchMode,
    ResearchPlan,
    ResearchPlanner,
    ResearchQuery,
    ResearchReport,
    ResearchSource,
    ResearchStatus,
    ResearchSynthesizer,
    ResearchTask,
    SSRFSecurityError,
    SearchDispatcher,
    SourceCategory,
    SupportLevel,
    assess_credibility,
    classify_category,
    disambiguate_dates,
    validate_url_ssrf,
)


class TestResearchModelsAndEnums(unittest.TestCase):
    """Test group 1: Enums, dataclasses, and serialization schemas."""

    def test_enums(self):
        self.assertEqual(ResearchMode.STANDARD.value, "standard")
        self.assertEqual(ResearchMode.ACADEMIC.value, "academic")
        self.assertEqual(ResearchMode.COMPARATIVE.value, "comparative")
        self.assertEqual(ResearchStatus.COMPLETED.value, "COMPLETED")
        self.assertEqual(SourceCategory.PEER_REVIEWED_PAPER.value, "PEER_REVIEWED_PAPER")
        self.assertEqual(ExtractionStatus.FULL_CONTENT_RETRIEVED.value, "FULL_CONTENT_RETRIEVED")
        self.assertEqual(SupportLevel.DIRECTLY_SUPPORTED.value, "DIRECTLY_SUPPORTED")
        self.assertEqual(ReportFormat.EXECUTIVE.value, "executive")

    def test_task_serialization(self):
        task = ResearchTask(
            task_id="tsk_test_01",
            user_id="user_admin",
            topic="Raspberry Pi 5 Cooling",
            question="What is the thermal efficiency of active coolers?",
            mode=ResearchMode.STANDARD,
        )
        d = task.to_dict()
        self.assertEqual(d["task_id"], "tsk_test_01")
        self.assertEqual(d["mode"], "standard")
        self.assertEqual(d["status"], "CREATED")
        self.assertEqual(d["progress_percent"], 0)

    def test_source_serialization(self):
        src = ResearchSource(
            source_id="src_01",
            task_id="tsk_test_01",
            url="https://arxiv.org/abs/2401.00001",
            title="Thermal Optimization on ARM64",
            authors=["Alice Smith", "Bob Jones"],
            publisher_or_domain="arxiv.org",
            category=SourceCategory.PEER_REVIEWED_PAPER,
            extraction_status=ExtractionStatus.ABSTRACT_ONLY,
            content="This paper evaluates active vs passive cooling on Cortex-A76.",
            doi="10.1234/arxiv.2401.00001",
            is_abstract_only=True,
        )
        d = src.to_dict()
        self.assertEqual(d["source_id"], "src_01")
        self.assertEqual(d["category"], "PEER_REVIEWED_PAPER")
        self.assertTrue(d["is_abstract_only"])
        self.assertIn("Alice Smith", d["authors"])


class TestResearchPlanner(unittest.TestCase):
    """Test group 2: Research planning engine and query formulation."""

    def setUp(self):
        mock_ai = MagicMock()
        mock_ai.chat_completion.return_value = None
        self.planner = ResearchPlanner(ai_service=mock_ai)

    def test_generate_standard_plan(self):
        task = ResearchTask(
            task_id="tsk_plan_01",
            user_id="user_01",
            topic="Solid State Batteries in EV Vehicles",
            question="What is the commercial readiness of solid state batteries in 2026?",
            mode=ResearchMode.STANDARD,
            max_sources=6,
        )
        plan = self.planner.generate_plan(task)
        self.assertEqual(plan.task_id, "tsk_plan_01")
        self.assertGreaterEqual(len(plan.supporting_questions), 2)
        self.assertGreaterEqual(len(plan.objectives), 2)
        self.assertGreaterEqual(len(plan.planned_queries), 3)
        self.assertEqual(plan.source_limits, 6)
        self.assertFalse(plan.approved)

    def test_generate_comparative_plan(self):
        task = ResearchTask(
            task_id="tsk_comp_01",
            user_id="user_01",
            topic="SQLite vs DuckDB",
            question="Compare SQLite and DuckDB for embedded analytics on ARM64",
            mode=ResearchMode.COMPARATIVE,
        )
        plan = self.planner.generate_plan(task)
        self.assertTrue(any("Comparative" in sec or "Matrix" in sec for sec in plan.expected_sections))
        queries = [q.query_text.lower() for q in plan.planned_queries]
        self.assertTrue(any("benchmark" in q or "compare" in q or "duckdb" in q for q in queries))

    def test_plan_updating(self):
        task = ResearchTask(
            task_id="tsk_up_01",
            user_id="user_01",
            topic="Edge AI",
            question="Edge AI models",
            mode=ResearchMode.QUICK,
        )
        plan = self.planner.generate_plan(task)
        updated = self.planner.update_plan(
            plan,
            user_modifications={
                "supporting_questions": ["What is NCNN throughput on Pi 5?"],
                "source_limits": 4,
            },
        )
        self.assertEqual(updated.source_limits, 4)
        self.assertEqual(updated.supporting_questions, ["What is NCNN throughput on Pi 5?"])


class TestSearchProvidersAndDispatcher(unittest.TestCase):
    """Test group 3: Multi-provider search parsing and dispatcher."""

    @patch("requests.Session.get")
    def test_duckduckgo_provider_instant_answer(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "AbstractText": "Raspberry Pi 5 is a single-board computer released in 2023 with a quad-core Cortex-A76.",
            "AbstractURL": "https://en.wikipedia.org/wiki/Raspberry_Pi_5",
            "Heading": "Raspberry Pi 5",
            "RelatedTopics": [],
        }
        mock_get.return_value = mock_resp

        provider = DuckDuckGoProvider(timeout=5)
        results = provider.search("Raspberry Pi 5", max_results=3, task_id="t1")
        self.assertGreaterEqual(len(results), 1)
        src = results[0]
        self.assertIn("Raspberry Pi 5", src.title)
        self.assertEqual(src.url, "https://en.wikipedia.org/wiki/Raspberry_Pi_5")
        self.assertIn("Cortex-A76", src.content)

    @patch("requests.Session.get")
    def test_arxiv_provider_atom_xml(self, mock_get):
        xml_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
          <entry>
            <id>http://arxiv.org/abs/2301.00002v1</id>
            <published>2023-01-02T12:00:00Z</published>
            <title>Benchmarking LLMs on Embedded ARM Systems</title>
            <summary>We benchmark quantized LLaMA models on Raspberry Pi 5.</summary>
            <author><name>Dr. Jane Doe</name></author>
            <arxiv:doi>10.48550/arXiv.2301.00002</arxiv:doi>
            <link title="pdf" href="http://arxiv.org/pdf/2301.00002v1" type="application/pdf"/>
          </entry>
        </feed>"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = xml_feed
        mock_get.return_value = mock_resp

        provider = ArxivProvider(timeout=5)
        results = provider.search("ARM LLM benchmarking", max_results=2, task_id="t1")
        self.assertEqual(len(results), 1)
        src = results[0]
        self.assertEqual(src.title, "Benchmarking LLMs on Embedded ARM Systems")
        self.assertEqual(src.authors, ["Dr. Jane Doe"])
        self.assertEqual(src.published_date, "2023-01-02")
        self.assertEqual(src.doi, "10.48550/arXiv.2301.00002")
        self.assertTrue(src.is_abstract_only)

    @patch("requests.Session.get")
    def test_crossref_provider_json(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {
                "items": [
                    {
                        "title": ["Thermal Analysis of Multicore SoCs"],
                        "DOI": "10.1109/TCAD.2023.123456",
                        "author": [{"given": "John", "family": "Smith"}],
                        "issued": {"date-parts": [[2023, 6, 15]]},
                        "container-title": ["IEEE Transactions on CAD"],
                        "is-referenced-by-count": 42,
                        "URL": "https://doi.org/10.1109/TCAD.2023.123456",
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp

        provider = CrossrefProvider(timeout=5)
        results = provider.search("multicore thermal", max_results=2, task_id="t1")
        self.assertEqual(len(results), 1)
        src = results[0]
        self.assertEqual(src.title, "Thermal Analysis of Multicore SoCs")
        self.assertEqual(src.authors, ["John Smith"])
        self.assertEqual(src.published_date, "2023-06-15")
        self.assertEqual(src.citation_count, 42)

    def test_openalex_abstract_reconstruction(self):
        inv_index = {
            "This": [0],
            "paper": [1],
            "presents": [2],
            "a": [3],
            "novel": [4],
            "architecture.": [5],
        }
        abstract = OpenAlexProvider._reconstruct_abstract(inv_index)
        self.assertEqual(abstract, "This paper presents a novel architecture.")

    def test_search_dispatcher_deduplication(self):
        dispatcher = SearchDispatcher(timeout=5)
        # Mock providers
        s1 = ResearchSource(source_id="s1", task_id="t1", url="https://example.com/paper1", title="Paper One")
        s2 = ResearchSource(source_id="s2", task_id="t1", url="https://example.com/paper1/", title="Paper One")  # duplicate url
        s3 = ResearchSource(source_id="s3", task_id="t1", url="https://example.com/paper2", title="Paper Two")

        mock_prov = MagicMock()
        mock_prov.search.return_value = [s1, s2, s3]
        dispatcher.providers["web"] = mock_prov

        plan = ResearchPlan(
            plan_id="p1",
            task_id="t1",
            main_question="Q",
            planned_queries=[ResearchQuery(query_id="q1", query_text="Q1", target_provider="web")],
            source_limits=5,
        )
        task = ResearchTask(task_id="t1", user_id="u1", topic="T", question="Q", max_sources=5)
        deduped = dispatcher.search_plan(plan, task)
        self.assertEqual(len(deduped), 2)
        urls = [s.url for s in deduped]
        self.assertIn("https://example.com/paper1", urls)
        self.assertIn("https://example.com/paper2", urls)


class TestContentExtractorAndSSRF(unittest.TestCase):
    """Test group 4: SSRF protection and content extraction."""

    def test_ssrf_defense_loopback_and_private(self):
        bad_targets = [
            "http://127.0.0.1:8000/api/tools",
            "http://localhost:8080/secret",
            "http://192.168.1.1/router",
            "http://10.200.0.1/admin",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]:5000/api",
        ]
        for url in bad_targets:
            with self.assertRaises(SSRFSecurityError):
                validate_url_ssrf(url)

    def test_ssrf_defense_valid_public_url(self):
        try:
            validate_url_ssrf("https://arxiv.org/abs/2301.00001")
            validate_url_ssrf("https://api.crossref.org/works")
        except SSRFSecurityError:
            self.fail("Valid public URLs should not trigger SSRFSecurityError")

    @patch("requests.Session.get")
    def test_html_extraction_and_cleaning(self, mock_get):
        html_doc = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Raspberry Pi 5 Performance Guide</title>
          <meta name="author" content="Eben Upton">
          <meta name="publication_date" content="2024-02-10">
        </head>
        <body>
          <nav><a href="/">Home</a></nav>
          <h1>Overview</h1>
          <p>The Raspberry Pi 5 features a quad-core 2.4 GHz Arm Cortex-A76 processor delivering up to 3x performance increase over Raspberry Pi 4.</p>
          <script>alert("malicious");</script>
          <footer>Footer text</footer>
        </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.encoding = "utf-8"
        mock_resp.iter_content.return_value = [html_doc.encode("utf-8")]
        mock_resp.url = "https://example.com/guide"
        mock_get.return_value = mock_resp

        extractor = ContentExtractor(timeout=5)
        src = ResearchSource(
            source_id="src_html",
            task_id="t1",
            url="https://example.com/guide",
            title="",
        )
        updated = extractor.extract_source(src)
        self.assertEqual(updated.title, "Raspberry Pi 5 Performance Guide")
        self.assertIn("Eben Upton", updated.authors)
        self.assertEqual(updated.published_date, "2024-02-10")
        self.assertIn("quad-core 2.4 GHz", updated.content)
        self.assertNotIn("alert", updated.content)
        self.assertEqual(updated.extraction_status, ExtractionStatus.FULL_CONTENT_RETRIEVED)

    @patch("requests.Session.get")
    def test_access_blocked_honest_reporting(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.url = "https://example.com/paywalled"
        mock_get.return_value = mock_resp

        extractor = ContentExtractor(timeout=5)
        src = ResearchSource(
            source_id="src_paywall",
            task_id="t1",
            url="https://example.com/paywalled",
            title="Paywalled Paper",
            content="Original abstract text retrieved from metadata",
        )
        updated = extractor.extract_source(src)
        self.assertEqual(updated.extraction_status, ExtractionStatus.ACCESS_BLOCKED)
        self.assertIn("Original abstract text", updated.content)


class TestCredibilityAndDateDisambiguation(unittest.TestCase):
    """Test group 5: Domain categorization, dates, and credibility scoring."""

    def test_classify_category(self):
        self.assertEqual(classify_category("https://www.cdc.gov/flu"), SourceCategory.GOVERNMENT_SOURCE)
        self.assertEqual(classify_category("https://cs.stanford.edu/paper"), SourceCategory.INSTITUTIONAL_SOURCE)
        self.assertEqual(classify_category("https://docs.python.org/3/library"), SourceCategory.OFFICIAL_DOCUMENTATION)
        self.assertEqual(classify_category("https://arxiv.org/abs/2301"), SourceCategory.PEER_REVIEWED_PAPER)
        self.assertEqual(classify_category("https://www.reddit.com/r/raspberry_pi"), SourceCategory.COMMUNITY_SOURCE)

    def test_disambiguate_dates(self):
        src = ResearchSource(
            source_id="s1",
            task_id="t1",
            url="https://example.org/study",
            title="Study",
            published_date="2024-05-20",
        )
        res = disambiguate_dates(src)
        self.assertEqual(res["publication_year"], 2024)
        self.assertIn(res["recency_tier"], ("current", "recent"))
        self.assertIsNotNone(res["retrieval_date"])

    def test_assess_credibility_peer_reviewed(self):
        src = ResearchSource(
            source_id="s1",
            task_id="t1",
            url="https://nature.com/articles/123",
            title="Quantum Advancements",
            authors=["Dr. A. Scientist"],
            doi="10.1038/s41586-024-0001",
            citation_count=120,
            published_date="2024-01-10",
        )
        assessment = assess_credibility(src)
        self.assertGreaterEqual(assessment["credibility_score"], 0.85)
        self.assertEqual(assessment["category"], "PEER_REVIEWED_PAPER")
        self.assertTrue(any("DOI" in f for f in assessment["flags"]))


class TestEvidenceExtractorAndStore(unittest.TestCase):
    """Test group 6: Grounded evidence extraction and evidence store."""

    def test_evidence_extraction_with_verbatim_passages(self):
        content = (
            "Thermal testing revealed that the active cooler dropped peak temperatures from 84°C to 58°C under continuous load. "
            "Power consumption increased by 0.3 Watts when the pulse-width modulated fan engaged at maximum RPM. "
            "Further analysis showed that acoustic noise was measured at 21 decibels at a distance of 30 centimeters."
        )
        src = ResearchSource(
            source_id="src_cooler",
            task_id="tsk_01",
            url="https://example.com/test",
            title="Pi 5 Thermal Report",
            content=content,
            authors=["Hardware Lab"],
        )
        extractor = EvidenceExtractor(max_records_per_source=3)
        records = extractor.extract_from_source(src, task_id="tsk_01")

        self.assertGreaterEqual(len(records), 2)
        for rec in records:
            # Ensure supporting passage is strictly a substring of original content
            self.assertIn(rec.supporting_passage, content)
            self.assertEqual(rec.support_level, SupportLevel.DIRECTLY_SUPPORTED)
            self.assertIn("Hardware Lab", rec.confidence_notes)

    def test_evidence_store(self):
        store = EvidenceStore(task_id="tsk_01")
        e1 = EvidenceRecord(
            evidence_id="ev_1",
            task_id="tsk_01",
            source_id="src_1",
            claim="Active cooling drops temperature to 58C",
            supporting_passage="...dropped peak temperatures to 58C...",
        )
        e2 = EvidenceRecord(
            evidence_id="ev_2",
            task_id="tsk_01",
            source_id="src_2",
            claim="Passive heatsink reached thermal throttle in 4 minutes",
            supporting_passage="...reached thermal throttle in 4 minutes...",
        )
        store.add_records([e1, e2])

        self.assertEqual(len(store.get_records()), 2)
        self.assertEqual(len(store.get_by_source("src_1")), 1)
        search_res = store.search_evidence("throttle")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].evidence_id, "ev_2")


class TestVerificationAndContradictions(unittest.TestCase):
    """Test group 7: Fact checking, contradictions, and limitations."""

    def test_find_corroborations(self):
        src1 = ResearchSource(source_id="s1", task_id="t1", url="https://lab-a.org", title="Lab A", publisher_or_domain="lab-a.org")
        src2 = ResearchSource(source_id="s2", task_id="t1", url="https://lab-b.edu", title="Lab B", publisher_or_domain="lab-b.edu")

        ev1 = EvidenceRecord(
            evidence_id="e1",
            task_id="t1",
            source_id="s1",
            claim="Active cooler dropped temperatures to fifty-eight degrees celsius under heavy continuous workload",
            supporting_passage="p1",
        )
        ev2 = EvidenceRecord(
            evidence_id="e2",
            task_id="t1",
            source_id="s2",
            claim="Measurements show temperatures dropped to fifty-eight degrees celsius under heavy continuous workload",
            supporting_passage="p2",
        )

        checker = FactChecker([src1, src2], [ev1, ev2])
        corrobs = checker.find_corroborations()
        self.assertGreaterEqual(len(corrobs), 1)
        self.assertEqual(corrobs[0]["independent_sources_count"], 2)

    def test_contradiction_detection(self):
        src1 = ResearchSource(source_id="s1", task_id="t1", url="https://site-a.com", title="Site A", publisher_or_domain="site-a.com")
        src2 = ResearchSource(source_id="s2", task_id="t1", url="https://site-b.com", title="Site B", publisher_or_domain="site-b.com")

        ev1 = EvidenceRecord(
            evidence_id="e1",
            task_id="t1",
            source_id="s1",
            claim="System throughput increased significantly during continuous stress testing",
            supporting_passage="p1",
        )
        ev2 = EvidenceRecord(
            evidence_id="e2",
            task_id="t1",
            source_id="s2",
            claim="System throughput decreased significantly during continuous stress testing",
            supporting_passage="p2",
        )

        detector = ContradictionDetector([src1, src2], [ev1, ev2])
        contras = detector.detect_contradictions("t1")
        self.assertEqual(len(contras), 1)
        self.assertIn("increased", contras[0].analysis)
        self.assertIn("decreased", contras[0].analysis)

    def test_limitations_compiler(self):
        s_abs = ResearchSource(
            source_id="s1",
            task_id="t1",
            url="https://arxiv.org/abs/1",
            title="P1",
            is_abstract_only=True,
            extraction_status=ExtractionStatus.ABSTRACT_ONLY,
        )
        s_block = ResearchSource(
            source_id="s2",
            task_id="t1",
            url="https://paywalled.com/2",
            title="P2",
            extraction_status=ExtractionStatus.ACCESS_BLOCKED,
        )

        limitations = LimitationsCompiler.compile_limitations(
            sources=[s_abs, s_block],
            plan=None,
            contradictions=[],
        )
        self.assertGreaterEqual(len(limitations), 2)
        self.assertTrue(any("abstract" in lim.lower() for lim in limitations))
        self.assertTrue(any("paywall" in lim.lower() or "blocked" in lim.lower() for lim in limitations))


class TestCitationsAndSynthesis(unittest.TestCase):
    """Test group 8: Citations, comparative matrices, and synthesis."""

    def test_citation_manager_and_validator(self):
        sources = [
            ResearchSource(
                source_id="src_1",
                task_id="t1",
                url="https://arxiv.org/abs/2301.01",
                title="ARM Benchmarks",
                authors=["Alice Smith"],
                published_date="2023-05-01",
                doi="10.1234/arm.2301",
            ),
            ResearchSource(
                source_id="src_2",
                task_id="t1",
                url="https://nature.com/articles/02",
                title="Silicon Review",
                authors=["Bob Jones"],
                published_date="2024-01-01",
            ),
        ]
        mgr = CitationManager(sources)
        self.assertEqual(mgr.get_tag_for_source("src_1"), "[1]")
        self.assertEqual(mgr.get_tag_for_source("src_2"), "[2]")

        # Text with valid citation [1] and fake hallucinated citation [99]
        synthesized_text = "ARM processors show high efficiency [1]. Unverified futuristic claim [99]."
        clean_text, valids, fakes = mgr.validate_citations_in_text(synthesized_text)

        self.assertIn("[1]", clean_text)
        self.assertNotIn("[99]", clean_text)
        self.assertIn("[99]", fakes)
        self.assertEqual(len(valids), 1)

    def test_comparative_analyzer(self):
        analyzer = ComparativeAnalyzer(entities=["SQLite", "DuckDB"])
        sources = [ResearchSource(source_id="s1", task_id="t1", url="https://ex.com", title="DB")]
        evidence = [
            EvidenceRecord(
                evidence_id="e1",
                task_id="t1",
                source_id="s1",
                claim="SQLite demonstrates lower memory footprint for embedded writes",
                supporting_passage="...",
            ),
            EvidenceRecord(
                evidence_id="e2",
                task_id="t1",
                source_id="s1",
                claim="DuckDB delivers faster columnar scan performance for analytics",
                supporting_passage="...",
            ),
        ]
        tags = {"s1": "[1]"}
        res = analyzer.build_matrix(sources, evidence, tags)
        self.assertIn("table_markdown", res)
        self.assertIn("SQLite", res["table_markdown"])
        self.assertIn("DuckDB", res["table_markdown"])
        self.assertIn("pros_cons", res)

    def test_deterministic_synthesis_fallback(self):
        synthesizer = ResearchSynthesizer()
        task = ResearchTask(task_id="t1", user_id="u1", topic="Python 3.14", question="What are the key changes in Python 3.14?")
        plan = ResearchPlan(plan_id="p1", task_id="t1", main_question=task.question)
        sources = [
            ResearchSource(
                source_id="s1",
                task_id="t1",
                url="https://docs.python.org/3.14",
                title="What's New In Python 3.14",
                publisher_or_domain="docs.python.org",
            )
        ]
        evidence = [
            EvidenceRecord(
                evidence_id="e1",
                task_id="t1",
                source_id="s1",
                claim="Tail-call evaluation and template strings are proposed",
                supporting_passage="...",
            )
        ]
        mgr = CitationManager(sources)
        sections = synthesizer.synthesize(
            task=task,
            plan=plan,
            sources=sources,
            evidence=evidence,
            contradictions=[],
            citation_manager=mgr,
            report_format=ReportFormat.EXECUTIVE,
        )
        self.assertGreaterEqual(len(sections), 3)
        self.assertIn("Executive Summary", sections[0]["title"])
        self.assertIn("Tail-call", sections[0]["content"])


class TestReportBuilderAndExport(unittest.TestCase):
    """Test group 9: Complete report compilation and formats."""

    def test_build_report_markdown_html_json(self):
        task = ResearchTask(task_id="t1", user_id="u1", topic="Edge Computing", question="What is Edge Computing?")
        plan = ResearchPlan(plan_id="p1", task_id="t1", main_question=task.question)
        sources = [ResearchSource(source_id="s1", task_id="t1", url="https://example.com/edge", title="Edge Computing Guide")]
        evidence = [EvidenceRecord(evidence_id="e1", task_id="t1", source_id="s1", claim="Edge computing lowers latency", supporting_passage="...")]
        mgr = CitationManager(sources)

        report = ReportBuilder.build_report(
            task=task,
            plan=plan,
            sources=sources,
            evidence=evidence,
            contradictions=[],
            limitations=["Limited to open access literature."],
            sections=[{"title": "Overview", "content": "Edge computing reduces network overhead [1]."}],
            citation_manager=mgr,
            report_format=ReportFormat.EXECUTIVE,
        )

        self.assertIn("# Autonomous Research Report: Edge Computing", report.markdown_content)
        self.assertIn("## Table of Contents", report.markdown_content)
        self.assertIn("## References & Sources", report.markdown_content)
        self.assertIn("<!DOCTYPE html>", report.html_content)
        self.assertIn("Edge computing reduces network overhead", report.html_content)

        archive = ReportBuilder.build_json_archive(task, plan, sources, evidence, [], report)
        self.assertEqual(archive["schema_version"], "1.0")
        self.assertEqual(archive["task"]["task_id"], "t1")
        self.assertEqual(len(archive["sources"]), 1)


class TestResearchDatabase(unittest.TestCase):
    """Test group 10: SQLite WAL persistence."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_research.sqlite3")
        self.db = ResearchDatabase(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_task_and_report_persistence(self):
        task = ResearchTask(
            task_id="t_db_01",
            user_id="user_test",
            topic="Robotics Control",
            question="How to control BLDC motors?",
        )
        self.db.save_task(task)

        loaded = self.db.get_task("t_db_01")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.topic, "Robotics Control")

        # Save Source
        src = ResearchSource(source_id="s_db_01", task_id="t_db_01", url="https://ex.com/motor", title="Motor Control")
        self.db.save_sources([src])
        loaded_sources = self.db.get_sources_for_task("t_db_01")
        self.assertEqual(len(loaded_sources), 1)

        # Save Evidence
        ev = EvidenceRecord(evidence_id="e_db_01", task_id="t_db_01", source_id="s_db_01", claim="FOC provides smooth torque", supporting_passage="...")
        self.db.save_evidence([ev])
        loaded_ev = self.db.get_evidence_for_task("t_db_01")
        self.assertEqual(len(loaded_ev), 1)

        # Save Report
        rep = ResearchReport(
            report_id="r_db_01",
            task_id="t_db_01",
            user_id="user_test",
            title="Motor Report",
            research_date="2026-11-17",
            research_question="How to control BLDC motors?",
            report_format=ReportFormat.TECHNICAL,
        )
        self.db.save_report(rep)
        loaded_rep = self.db.get_report("r_db_01")
        self.assertIsNotNone(loaded_rep)
        self.assertEqual(loaded_rep.title, "Motor Report")

        # Settings
        self.db.save_settings("user_test", {"default_mode": "deep", "default_max_sources": 12, "auto_approve_plan": True})
        settings = self.db.get_settings("user_test")
        self.assertEqual(settings["default_mode"], "deep")
        self.assertEqual(settings["default_max_sources"], 12)
        self.assertTrue(settings["auto_approve_plan"])


class TestResearchAgentLifecycle(unittest.TestCase):
    """Test group 11: End-to-end research agent lifecycle and interactive approval."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_agent.sqlite3")
        self.db = ResearchDatabase(self.db_path)
        self.agent = ResearchAgent(self.db)
        mock_ai = MagicMock()
        mock_ai.chat_completion.return_value = None
        self.agent.planner.ai = mock_ai
        self.agent.synthesizer.ai = mock_ai

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("apps.research.search_providers.SearchDispatcher.search_plan")
    @patch("apps.research.extractor.ContentExtractor.batch_extract")
    def test_run_task_sync_full_lifecycle(self, mock_extract, mock_search):
        # Setup mock sources
        src1 = ResearchSource(
            source_id="src_mock_1",
            task_id="t1",
            url="https://arxiv.org/abs/2301",
            title="ARM64 Energy Efficiency",
            content="Experiments confirmed active cooling reduced throttle duration by 85%.",
            publisher_or_domain="arxiv.org",
        )
        mock_search.return_value = [src1]
        mock_extract.return_value = [src1]

        task = self.agent.create_task(
            user_id="u1",
            topic="Pi 5 Energy",
            question="What is the energy efficiency of Pi 5?",
            auto_start=False,
            auto_approve=True,
        )
        completed = self.agent.run_task_sync(task.task_id, auto_approve=True)

        self.assertEqual(completed.status, ResearchStatus.COMPLETED)
        self.assertEqual(completed.progress_percent, 100)
        self.assertIsNotNone(completed.report_id)

        # Verify persisted report
        report = self.db.get_report(completed.report_id)
        self.assertIsNotNone(report)
        self.assertIn("Autonomous Research Report: Pi 5 Energy", report.markdown_content)

    def test_plan_requires_user_approval_flow(self):
        task = self.agent.create_task(
            user_id="u1",
            topic="Robotics Kinematics",
            question="Forward kinematics algorithms",
            auto_start=False,
            auto_approve=False,
        )
        # Run pipeline with auto_approve=False
        res = self.agent._run_pipeline(task.task_id, auto_approve=False)
        self.assertEqual(res.status, ResearchStatus.NEEDS_USER_INPUT)
        self.assertIsNotNone(res.plan)
        self.assertFalse(res.plan.approved)


class TestResearchFastAPIRouter(unittest.TestCase):
    """Test group 12: REST API endpoints and guest role protection."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app(
            router_specs=[("apps.api.research_api", "research_router", "/api", ("research",))],
            lifespan_context=noop_lifespan,
        )
        cls.client = TestClient(cls.app)

    def test_health_endpoint(self):
        resp = self.client.get("/api/research/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["service"], "ai-research-assistant")
        self.assertIn("arxiv", data["providers_available"])

    def test_guest_forbidden_to_create_task(self):
        guest_identity = AppRequestIdentity(user_id="guest_1", display_name="Guest", role=UserRole.GUEST)
        self.app.dependency_overrides[get_current_user_identity] = lambda: guest_identity
        try:
            resp = self.client.post("/api/research/tasks", json={"topic": "Forbidden Research"})
            self.assertEqual(resp.status_code, 403)
            self.assertIn("Guest", resp.json()["detail"])
        finally:
            self.app.dependency_overrides.clear()

    def test_create_and_get_task(self):
        user_identity = AppRequestIdentity(user_id="user_alice", display_name="Alice", role=UserRole.USER)
        self.app.dependency_overrides[get_current_user_identity] = lambda: user_identity
        try:
            # Create task
            c_resp = self.client.post(
                "/api/research/tasks",
                json={
                    "topic": "Microcontroller I2C Speeds",
                    "question": "What are fast-mode plus limits?",
                    "mode": "technical",
                    "max_sources": 4,
                    "auto_approve": False,
                    "auto_start": False,
                },
            )
            self.assertEqual(c_resp.status_code, 201)
            t_data = c_resp.json()["task"]
            task_id = t_data["task_id"]

            # Get task
            g_resp = self.client.get(f"/api/research/tasks/{task_id}")
            self.assertEqual(g_resp.status_code, 200)
            self.assertEqual(g_resp.json()["task"]["topic"], "Microcontroller I2C Speeds")

            # List tasks
            l_resp = self.client.get("/api/research/tasks")
            self.assertEqual(l_resp.status_code, 200)
            self.assertGreaterEqual(l_resp.json()["count"], 1)
        finally:
            self.app.dependency_overrides.clear()

    def test_settings_api(self):
        user_identity = AppRequestIdentity(user_id="user_bob", display_name="Bob", role=UserRole.USER)
        self.app.dependency_overrides[get_current_user_identity] = lambda: user_identity
        try:
            # Update settings
            u_resp = self.client.post(
                "/api/research/settings",
                json={"default_mode": "academic", "default_max_sources": 15, "auto_approve_plan": True},
            )
            self.assertEqual(u_resp.status_code, 200)

            # Get settings
            g_resp = self.client.get("/api/research/settings")
            self.assertEqual(g_resp.status_code, 200)
            s_data = g_resp.json()["settings"]
            self.assertEqual(s_data["default_mode"], "academic")
            self.assertEqual(s_data["default_max_sources"], 15)
            self.assertTrue(s_data["auto_approve_plan"])
        finally:
            self.app.dependency_overrides.clear()


class TestVoiceIntegration(unittest.TestCase):
    """Test group 13: Voice assistant intent routing and responses."""

    def setUp(self):
        self.engine = LocalIntelligenceEngine()

    def test_voice_intents_classification(self):
        cases = [
            ("JARVIS, open the research assistant", "research_open"),
            ("research quantum computing benchmarks", "research_investigate"),
            ("compare SQLite vs DuckDB", "research_compare"),
            ("check research status", "research_status"),
            ("read research summary", "research_read_summary"),
            ("list the research sources", "research_sources"),
        ]
        for phrase, exp_intent in cases:
            intent, ctx = self.engine.classify_intent(phrase)
            self.assertEqual(intent, exp_intent, f"Failed for phrase: '{phrase}'")

    def test_voice_response_execution(self):
        res = self.engine.respond("open research assistant")
        self.assertEqual(res.get("action"), "open_tab")
        self.assertEqual(res.get("target_tab"), "research")

        res_status = self.engine.respond("what is the research status")
        self.assertIn("tools_used", res_status)
        self.assertIn("research_status", res_status["tools_used"])


if __name__ == "__main__":
    pytest.main(["-v", __file__])
