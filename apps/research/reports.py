"""
Report assembly and multi-format export generator for JARVIS AI Research Assistant.
Builds comprehensive Markdown documents, responsive standalone HTML reports,
and JSON evidence archives.
"""

from __future__ import annotations

import html
import json
import logging
import time
from typing import Any, Dict, List, Optional
import uuid

from apps.research.citations import CitationManager
from apps.research.models import (
    ContradictionRecord,
    EvidenceRecord,
    ReportFormat,
    ResearchPlan,
    ResearchReport,
    ResearchSource,
    ResearchTask,
)

logger = logging.getLogger("JARVIS-RESEARCH-REPORTS")


class ReportBuilder:
    """Assembles final research report from synthesized sections and evidence."""

    @classmethod
    def build_report(
        cls,
        task: ResearchTask,
        plan: ResearchPlan,
        sources: List[ResearchSource],
        evidence: List[EvidenceRecord],
        contradictions: List[ContradictionRecord],
        limitations: List[str],
        sections: List[Dict[str, str]],
        citation_manager: CitationManager,
        report_format: ReportFormat = ReportFormat.EXECUTIVE,
    ) -> ResearchReport:
        """Construct a validated ResearchReport object with Markdown and HTML representations."""
        report_id = f"rep_{uuid.uuid4().hex[:10]}"
        title = f"Autonomous Research Report: {task.topic}"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        # Validate citations across all sections
        validated_sections: List[Dict[str, str]] = []
        for sec in sections:
            clean_body, _, _ = citation_manager.validate_citations_in_text(sec.get("content", ""))
            validated_sections.append({"title": sec.get("title", "Section"), "content": clean_body})

        # Format references
        references_list = citation_manager.format_reference_list()
        ref_dicts = [c.to_dict() for c in citation_manager.citations]

        # 1. Build Markdown
        md_text = cls._build_markdown(
            title=title,
            task=task,
            date_str=now_str,
            sections=validated_sections,
            limitations=limitations,
            references=references_list,
        )

        # 2. Build HTML
        html_text = cls._build_html(
            title=title,
            task=task,
            date_str=now_str,
            sections=validated_sections,
            limitations=limitations,
            references=references_list,
            sources=sources,
        )

        report = ResearchReport(
            report_id=report_id,
            task_id=task.task_id,
            user_id=task.user_id,
            title=title,
            research_date=now_str,
            research_question=task.question,
            report_format=report_format,
            sections=validated_sections,
            markdown_content=md_text,
            html_content=html_text,
            references=ref_dicts,
            limitations=limitations,
        )

        return report

    @staticmethod
    def _build_markdown(
        title: str,
        task: ResearchTask,
        date_str: str,
        sections: List[Dict[str, str]],
        limitations: List[str],
        references: List[str],
    ) -> str:
        """Render complete GitHub-flavored Markdown report."""
        lines = [
            f"# {title}",
            "",
            f"**Research Question:** {task.question}  ",
            f"**Date:** {date_str}  ",
            f"**Mode:** {task.mode.value} | **Scope:** {task.scope} | **Sources Analyzed:** {len(task.sources)}  ",
            "",
            "---",
            "",
            "## Table of Contents",
            "",
        ]

        # TOC
        for i, sec in enumerate(sections, start=1):
            anchor = sec["title"].lower().replace(" ", "-").replace("&", "").replace("/", "")
            lines.append(f"{i}. [{sec['title']}](#{anchor})")
        lines.append(f"{len(sections) + 1}. [Research Limitations & Uncertainties](#research-limitations--uncertainties)")
        lines.append(f"{len(sections) + 2}. [References & Sources](#references--sources)")
        lines.extend(["", "---", ""])

        # Sections
        for sec in sections:
            lines.append(f"## {sec['title']}")
            lines.append("")
            lines.append(sec["content"])
            lines.append("")

        # Limitations
        lines.append("## Research Limitations & Uncertainties")
        lines.append("")
        for lim in limitations:
            lines.append(f"- {lim}")
        lines.append("")

        # References
        lines.append("## References & Sources")
        lines.append("")
        for ref in references:
            lines.append(f"- {ref}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _build_html(
        title: str,
        task: ResearchTask,
        date_str: str,
        sections: List[Dict[str, str]],
        limitations: List[str],
        references: List[str],
        sources: List[ResearchSource],
    ) -> str:
        """Render clean, standalone responsive HTML."""
        safe_title = html.escape(title)
        safe_question = html.escape(task.question)

        sections_html = []
        for sec in sections:
            s_title = html.escape(sec["title"])
            # Format paragraphs and list items simply
            content_html = html.escape(sec["content"]).replace("\n\n", "</p><p>").replace("\n- ", "<br>• ")
            sections_html.append(f'<section class="report-section"><h2>{s_title}</h2><p>{content_html}</p></section>')

        lims_html = "".join(f"<li>{html.escape(lim)}</li>" for lim in limitations)
        refs_html = "".join(f"<li>{html.escape(ref)}</li>" for ref in references)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title}</title>
<style>
  :root {{
    --bg-color: #0d1117;
    --card-bg: #161b22;
    --border-color: #30363d;
    --text-primary: #c9d1d9;
    --text-heading: #58a6ff;
    --accent: #238636;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-primary);
    line-height: 1.6;
    margin: 0;
    padding: 24px;
  }}
  .container {{
    max-width: 900px;
    margin: 0 auto;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 32px;
  }}
  h1 {{ color: var(--text-heading); margin-top: 0; font-size: 26px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; }}
  h2 {{ color: #79c0ff; font-size: 20px; margin-top: 24px; border-bottom: 1px solid #21262d; padding-bottom: 6px; }}
  .meta-box {{
    background: #0d1117;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 24px;
    font-size: 14px;
  }}
  .report-section {{ margin-bottom: 24px; }}
  ul {{ padding-left: 20px; }}
  li {{ margin-bottom: 8px; }}
  .ref-list li {{ font-size: 13px; font-family: monospace; }}
</style>
</head>
<body>
<div class="container">
  <h1>{safe_title}</h1>
  <div class="meta-box">
    <strong>Research Question:</strong> {safe_question}<br>
    <strong>Generated:</strong> {date_str} | <strong>Mode:</strong> {task.mode.value} | <strong>Sources Analyzed:</strong> {len(sources)}
  </div>
  {"".join(sections_html)}
  <section class="report-section">
    <h2>Research Limitations & Uncertainties</h2>
    <ul>{lims_html}</ul>
  </section>
  <section class="report-section">
    <h2>References & Sources</h2>
    <ul class="ref-list">{refs_html}</ul>
  </section>
</div>
</body>
</html>
"""

    @staticmethod
    def build_json_archive(
        task: ResearchTask,
        plan: ResearchPlan,
        sources: List[ResearchSource],
        evidence: List[EvidenceRecord],
        contradictions: List[ContradictionRecord],
        report: ResearchReport,
    ) -> Dict[str, Any]:
        """Produce full JSON evidence archive."""
        return {
            "schema_version": "1.0",
            "task": task.to_dict(),
            "plan": plan.to_dict(),
            "sources": [s.to_dict() for s in sources],
            "evidence": [e.to_dict() for e in evidence],
            "contradictions": [c.to_dict() for c in contradictions],
            "report": report.to_dict(),
            "exported_at": time.time(),
        }
