"""
Autonomous Research Planning Engine.
Decomposes user research queries into sub-questions, targeted queries,
source requirements, and structured execution plans.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional
import uuid

from apps.apps_center.ai_service import SharedAIService
from .models import (
    ResearchMode,
    ResearchPlan,
    ResearchQuery,
    ResearchTask,
)

logger = logging.getLogger("JARVIS.Research.Planner")


class ResearchPlanner:
    """
    Generates and manages structured research plans.
    """

    def __init__(self, ai_service: Optional[SharedAIService] = None):
        self.ai = ai_service or SharedAIService()

    def create_plan(
        self,
        task: ResearchTask,
        provider: Optional[str] = None,
    ) -> ResearchPlan:
        """
        Produce a structured research plan tailored to the task question,
        mode, depth, and constraints.
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # Attempt AI-based plan decomposition
        prompt = (
            f"You are an expert autonomous research planner. Create a structured research plan for the following topic:\n\n"
            f"TOPIC/QUESTION: {task.question}\n"
            f"RESEARCH MODE: {task.mode.value}\n"
            f"DESIRED DEPTH: {task.depth}\n"
            f"DATE RANGE: {task.date_range}\n"
            f"MAX SOURCES: {task.max_sources}\n\n"
            "Return a valid JSON object matching this schema:\n"
            "{\n"
            '  "main_question": string,\n'
            '  "supporting_questions": [string, ...],\n'
            '  "objectives": [string, ...],\n'
            '  "search_queries": [\n'
            '     {"query": string, "provider": "web"|"arxiv"|"crossref"|"openalex"|"europepmc", "sub_question": string}\n'
            '  ],\n'
            '  "source_requirements": [string, ...],\n'
            '  "expected_sections": [string, ...]\n'
            "}\n"
            "Do NOT assume the findings or answers. Propose exploratory queries to discover facts."
        )

        try:
            res = self.ai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are JARVIS Research Planner. Propose objective, unbiased research queries. Return JSON only.",
                provider=provider,
                temperature=0.2,
                max_tokens=1000,
            )
            if res.get("success") and res.get("text"):
                text = res["text"].strip()
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    queries = []
                    for i, q in enumerate(data.get("search_queries", [])):
                        queries.append(
                            ResearchQuery(
                                query_id=f"q_{plan_id}_{i+1}",
                                query_text=q.get("query", task.question),
                                target_provider=q.get("provider", "web"),
                                sub_question=q.get("sub_question", ""),
                            )
                        )

                    return ResearchPlan(
                        plan_id=plan_id,
                        task_id=task.task_id,
                        main_question=data.get("main_question", task.question),
                        supporting_questions=data.get("supporting_questions", []),
                        objectives=data.get("objectives", []),
                        planned_queries=queries,
                        source_requirements=data.get("source_requirements", ["reputable_web", "academic"]),
                        date_constraints=task.date_range,
                        expected_sections=data.get("expected_sections", ["Overview", "Findings", "Analysis", "References"]),
                        source_limits=task.max_sources,
                        approved=task.mode != ResearchMode.DEEP,
                    )
        except Exception as e:
            logger.warning("AI research planning failed, falling back to deterministic planner: %s", e)

        # Deterministic fallback planner
        return self._create_deterministic_plan(task, plan_id)

    generate_plan = create_plan

    def _create_deterministic_plan(self, task: ResearchTask, plan_id: str) -> ResearchPlan:
        clean_q = task.question.strip()
        # Clean question tokens
        keywords = [w for w in re.findall(r"\b[A-Za-z0-9\-]{3,}\b", clean_q) if w.lower() not in {"what", "when", "where", "which", "how", "does", "compare", "research", "find", "about", "the"}]
        kw_phrase = " ".join(keywords[:5]) if keywords else clean_q

        supporting_questions = []
        objectives = []
        expected_sections = []
        raw_queries: List[Dict[str, str]] = []

        if task.mode == ResearchMode.COMPARATIVE or "compare" in clean_q.lower() or " vs " in clean_q.lower():
            objectives = [
                f"Analyze core specifications and capabilities of target subjects in '{kw_phrase}'.",
                "Evaluate empirical benchmark results and performance under real-world conditions.",
                "Identify trade-offs, advantages, limitations, and practical recommendations.",
            ]
            supporting_questions = [
                f"What are the architectural specifications and baseline metrics for {kw_phrase}?",
                f"What published benchmarks or comparative studies exist comparing {kw_phrase}?",
                f"What are the verified trade-offs, power/efficiency costs, and software ecosystems for {kw_phrase}?",
            ]
            expected_sections = [
                "Executive Summary",
                "Comparative Overview & Feature Matrix",
                "Architectural & Technical Analysis",
                "Performance Benchmarks & Metrics",
                "Trade-Offs & Limitations",
                "Recommendations",
                "References",
            ]
            raw_queries = [
                {"query": f"{kw_phrase} comparison benchmarks", "provider": "web", "sub_q": supporting_questions[0]},
                {"query": f"{kw_phrase} technical specifications architecture", "provider": "web", "sub_q": supporting_questions[0]},
                {"query": f"{kw_phrase} evaluation performance", "provider": "arxiv", "sub_q": supporting_questions[1]},
                {"query": f"{kw_phrase} trade-offs limitations", "provider": "web", "sub_q": supporting_questions[2]},
            ]

        elif task.mode in (ResearchMode.ACADEMIC, ResearchMode.LITERATURE_REVIEW):
            objectives = [
                f"Survey seminal and recent academic publications on '{kw_phrase}'.",
                "Catalog key methodologies, datasets, algorithms, and evaluation metrics.",
                "Synthesize current open research questions, challenges, and future trajectories.",
            ]
            supporting_questions = [
                f"What are the foundational theories and recent state-of-the-art architectures in {kw_phrase}?",
                f"What empirical datasets and experimental methodologies are standard for {kw_phrase}?",
                f"What are the primary unresolved limitations and open challenges in {kw_phrase}?",
            ]
            expected_sections = [
                "Abstract & Executive Summary",
                "Taxonomy & Theoretical Foundations",
                "Methodological Survey",
                "Empirical Results & Benchmarks",
                "Open Challenges & Research Gaps",
                "References",
            ]
            raw_queries = [
                {"query": f"{kw_phrase} review state of the art", "provider": "arxiv", "sub_q": supporting_questions[0]},
                {"query": f"{kw_phrase} architecture methodology", "provider": "crossref", "sub_q": supporting_questions[1]},
                {"query": f"{kw_phrase} dataset benchmark evaluation", "provider": "openalex", "sub_q": supporting_questions[1]},
                {"query": f"{kw_phrase} challenges limitations survey", "provider": "arxiv", "sub_q": supporting_questions[2]},
            ]

        elif task.mode == ResearchMode.CURRENT_EVENTS:
            objectives = [
                f"Identify recent news, releases, and developments in '{kw_phrase}'.",
                "Verify factual event dates, involved organizations, and official announcements.",
                "Assess immediate industry and community impact.",
            ]
            supporting_questions = [
                f"What recent events or major updates occurred regarding {kw_phrase}?",
                f"What do official primary sources state regarding {kw_phrase}?",
                f"What verified outcomes or subsequent developments have been confirmed?",
            ]
            expected_sections = [
                "Summary of Recent Developments",
                "Chronological Timeline",
                "Verified Key Events & Statements",
                "Impact Analysis",
                "References",
            ]
            raw_queries = [
                {"query": f"{kw_phrase} latest news updates", "provider": "web", "sub_q": supporting_questions[0]},
                {"query": f"{kw_phrase} official announcement release", "provider": "web", "sub_q": supporting_questions[1]},
                {"query": f"{kw_phrase} recent developments", "provider": "web", "sub_q": supporting_questions[2]},
            ]

        else:
            # Standard, Quick, Technical, Custom
            objectives = [
                f"Provide clear, evidence-based understanding of '{kw_phrase}'.",
                "Gather verified factual data from authoritative documentation and research.",
                "Synthesize conclusions, limitations, and actionable insights.",
            ]
            supporting_questions = [
                f"What are the core concepts and definitions of {kw_phrase}?",
                f"What are the verified mechanisms, implementations, or architectures in {kw_phrase}?",
                f"What are the real-world implications, limitations, and practical applications?",
            ]
            expected_sections = [
                "Executive Summary",
                "Core Concepts & Definitions",
                "Technical Implementation & Architecture",
                "Key Evidence & Findings",
                "Limitations & Uncertainties",
                "Conclusions",
                "References",
            ]
            raw_queries = [
                {"query": f"{kw_phrase} overview introduction", "provider": "web", "sub_q": supporting_questions[0]},
                {"query": f"{kw_phrase} technical documentation architecture", "provider": "web", "sub_q": supporting_questions[1]},
                {"query": f"{kw_phrase} research paper", "provider": "arxiv", "sub_q": supporting_questions[1]},
                {"query": f"{kw_phrase} practical applications limitations", "provider": "web", "sub_q": supporting_questions[2]},
            ]

        # Enforce max sources / query bounds
        max_q = min(len(raw_queries), max(2, task.max_sources // 2))
        queries = []
        for i, rq in enumerate(raw_queries[:max_q]):
            queries.append(
                ResearchQuery(
                    query_id=f"q_{plan_id}_{i+1}",
                    query_text=rq["query"],
                    target_provider=rq["provider"],
                    sub_question=rq["sub_q"],
                )
            )

        return ResearchPlan(
            plan_id=plan_id,
            task_id=task.task_id,
            main_question=clean_q,
            supporting_questions=supporting_questions,
            objectives=objectives,
            planned_queries=queries,
            source_requirements=["official_documentation", "peer_reviewed_paper", "primary_web"],
            date_constraints=task.date_range,
            expected_sections=expected_sections,
            source_limits=task.max_sources,
            approved=False,
        )

    def update_plan(
        self,
        plan: ResearchPlan,
        updates: Optional[Dict[str, Any]] = None,
        user_modifications: Optional[Dict[str, Any]] = None,
    ) -> ResearchPlan:
        """Allow user revision of research plan before or during execution."""
        eff_updates = updates if updates is not None else (user_modifications or {})
        if "main_question" in eff_updates:
            plan.main_question = str(eff_updates["main_question"]).strip()
        if "supporting_questions" in eff_updates and isinstance(eff_updates["supporting_questions"], list):
            plan.supporting_questions = [str(q).strip() for q in eff_updates["supporting_questions"]]
        if "objectives" in eff_updates and isinstance(eff_updates["objectives"], list):
            plan.objectives = [str(o).strip() for o in eff_updates["objectives"]]
        if "expected_sections" in eff_updates and isinstance(eff_updates["expected_sections"], list):
            plan.expected_sections = [str(s).strip() for s in eff_updates["expected_sections"]]
        if "source_limits" in eff_updates:
            plan.source_limits = max(1, min(50, int(eff_updates["source_limits"])))
        if "approved" in eff_updates:
            plan.approved = bool(eff_updates["approved"])
        if "planned_queries" in eff_updates and isinstance(eff_updates["planned_queries"], list):
            new_queries = []
            for i, q in enumerate(eff_updates["planned_queries"]):
                if isinstance(q, dict):
                    new_queries.append(
                        ResearchQuery(
                            query_id=q.get("query_id", f"q_{plan.plan_id}_{i+1}"),
                            query_text=q.get("query_text", ""),
                            target_provider=q.get("target_provider", "web"),
                            sub_question=q.get("sub_question", ""),
                        )
                    )
            if new_queries:
                plan.planned_queries = new_queries
        return plan

    def approve_plan(self, plan: ResearchPlan) -> ResearchPlan:
        plan.approved = True
        return plan
