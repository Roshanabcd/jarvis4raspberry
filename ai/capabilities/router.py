"""
JARVIS Autonomous Capability Router.
Classifies natural language input (from Voice, Chat, or Background Tasks) into
concrete capability intents and extracts parameters without requiring an LLM.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ai.capabilities.models import CapabilityIntentMatch
from ai.capabilities.registry import get_capability_registry

logger = logging.getLogger("JARVIS.Capabilities.Router")

_PREFIX_STRIP_REGEX = re.compile(
    r"^(?:(?:hey|hi|hello|ok|okay)?\s*jarvis[,:\s]*|(?:please|can\s+you|could\s+you|would\s+you|go\s+ahead\s+and)\s+)*",
    re.IGNORECASE,
)

_URL_REGEX = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


class AutonomousCapabilityRouter:
    """Routes voice and text prompts to the optimal capability with zero-overhead classification."""

    def __init__(self) -> None:
        self.registry = get_capability_registry()

    def clean_prompt(self, text: str) -> str:
        """Strip conversational filler words and wake words."""
        cleaned = _PREFIX_STRIP_REGEX.sub("", text.strip()).strip()
        # Clean trailing punctuation
        return cleaned.rstrip("?.!")

    def route(
        self,
        text: str,
        user_role: str = "USER",
        channel: str = "chat",
    ) -> Optional[CapabilityIntentMatch]:
        """Classify user prompt into a specific capability and extract parameters."""
        raw = text.strip()
        cleaned = self.clean_prompt(raw)
        if not cleaned:
            return None

        # 1. Developer CLI Direct Escapes (High Priority)
        cli_match = self._match_developer_clis(cleaned)
        if cli_match:
            return cli_match

        # 2. Canonical Core Apps (YouTube, Document QA, Research, Telemetry, Desktop)
        core_match = self._match_core_apps(cleaned, raw)
        if core_match:
            return core_match

        # 3. Extension Modules (#1 to #43)
        module_match = self._match_modules(cleaned)
        if module_match:
            return module_match

        return None

    def _match_developer_clis(self, text: str) -> Optional[CapabilityIntentMatch]:
        """Check for explicit developer CLI directives."""
        cli_patterns = [
            ("antigravity", r"\b(?:antigravity|agy)\b"),
            ("claude", r"\bclaude(?:\s+code)?\b"),
            ("codex", r"\bcodex\b"),
            ("copilot", r"\b(?:github\s+)?copilot\b"),
            ("hermes", r"\bhermes\b"),
            ("aider", r"\baider\b"),
            ("opencode", r"\bopencode\b"),
            ("cline", r"\bcline\b"),
        ]

        # Trigger verbs indicating command escalation
        verbs_pattern = re.compile(
            r"\b(?:run|ask|use|with|execute|tell|launch|invoke|have)\s+(?:the\s+)?",
            re.IGNORECASE,
        )

        for cli_name, pattern in cli_patterns:
            m_cli = re.search(pattern, text, re.IGNORECASE)
            if not m_cli:
                continue

            # Check if preceded by trigger verb, or starts with CLI name
            is_direct_prefix = text.lower().startswith(cli_name) or text.lower().startswith("agy ")
            is_verb_triggered = bool(verbs_pattern.search(text[:m_cli.start() + len(cli_name)]))

            if is_direct_prefix or is_verb_triggered or "diagnose" in text.lower() or "fix" in text.lower() or "cli" in text.lower():
                # Extract prompt: remove CLI invocation prefix
                prompt_text = re.sub(
                    rf"^(?:(?:run|ask|use|with|execute|tell|launch|invoke|have)\s+)?(?:the\s+)?{pattern}\s+(?:to\s+|for\s+)?",
                    "",
                    text,
                    flags=re.IGNORECASE,
                ).strip()
                if not prompt_text:
                    prompt_text = "Diagnose repository and suggest fixes"

                action_id = "diagnose" if any(w in text.lower() for w in ("diagnose", "inspect", "audit", "status", "check")) else "run_task"
                return CapabilityIntentMatch(
                    capability_id=f"developer-cli:{cli_name}",
                    action_id=action_id,
                    confidence=0.95,
                    extracted_parameters={"prompt": prompt_text, "instruction": prompt_text},
                    matched_pattern=pattern,
                    rationale=f"Matched explicit developer CLI trigger for {cli_name.title()}.",
                )

        return None

    def _match_core_apps(self, text: str, raw_text: str) -> Optional[CapabilityIntentMatch]:
        """Match YouTube summarizer, Document QA, Research, Telemetry, and Desktop automation."""
        # A. YouTube Video Summarizer
        url_match = _URL_REGEX.search(raw_text)
        yt_url = url_match.group(0) if url_match and ("youtube.com" in url_match.group(0) or "youtu.be" in url_match.group(0)) else None

        if yt_url or re.search(r"\b(?:youtube|yt)\b", text, re.I):
            if any(w in text.lower() for w in ("summarize", "transcript", "explain", "breakdown", "watch", "tell me about", "play")):
                return CapabilityIntentMatch(
                    capability_id="youtube-summarizer",
                    action_id="summarize_video",
                    confidence=0.92,
                    extracted_parameters={"url": yt_url} if yt_url else {},
                    matched_pattern="youtube_summarize",
                    rationale="Detected YouTube video summarization intent.",
                )

        # B. Document QA / Knowledge Base RAG
        if re.search(r"\b(?:search|query|ask|find\s+in)\s+(?:documents?|docs?|pdfs?|knowledge\s+base)\b", text, re.I) or \
           re.search(r"\bwhat\s+(?:does|do)\s+(?:the\s+)?(?:documents?|docs?|pdf)\s+say\b", text, re.I):
            clean_q = re.sub(r"^.*?\b(?:about|for|saying|say)\s+", "", text, flags=re.I).strip()
            return CapabilityIntentMatch(
                capability_id="document-qa",
                action_id="query_documents",
                confidence=0.88,
                extracted_parameters={"query": clean_q or text},
                matched_pattern="document_qa_query",
                rationale="Detected Document QA knowledge retrieval intent.",
            )

        # C. Research Assistant
        if re.search(r"\b(?:conduct|do|perform|generate)\s+(?:a\s+)?research\s+(?:on|about)?\b", text, re.I) or \
           re.search(r"\bliterature\s+review\s+(?:on|for)\b", text, re.I):
            topic = re.sub(r"^.*?\b(?:on|about|for)\s+", "", text, flags=re.I).strip()
            return CapabilityIntentMatch(
                capability_id="research-assistant",
                action_id="synthesize_research",
                confidence=0.89,
                extracted_parameters={"topic": topic or text},
                matched_pattern="research_synthesis",
                rationale="Detected deep academic research synthesis intent.",
            )

        # D. Face Recognition
        if re.search(r"\b(?:who\s+is\s+(?:looking|in\s+front|there)|recognize\s+(?:my\s+face|me|person)|scan\s+face)\b", text, re.I) or \
           re.search(r"\bface\s+(?:recognition|verification|status|enroll)\b", text, re.I):
            return CapabilityIntentMatch(
                capability_id="face-recognition",
                action_id="identify_face",
                confidence=0.90,
                extracted_parameters={},
                matched_pattern="face_recognition",
                rationale="Detected biometric face identification inquiry.",
            )

        # E. System Telemetry & Health
        if re.search(r"\b(?:check|show|get|report|display)\s+(?:me\s+)?(?:the\s+)?(?:system|cpu|ram|memory|telemetry|hardware|device|health)\b", text, re.I) or \
           re.search(r"\bhow\s+(?:healthy|hot|busy)\s+is\s+(?:the\s+)?(?:system|pi|server|cpu)\b", text, re.I) or \
           re.search(r"\b(?:system\s+status|health|telemetry|uptime)\b", text, re.I):
            return CapabilityIntentMatch(
                capability_id="system-telemetry",
                action_id="get_status",
                confidence=0.94,
                extracted_parameters={},
                matched_pattern="system_telemetry",
                rationale="Detected hardware and OS telemetry request.",
            )

        # F. Desktop PC Tools (App Launcher & Window Switch)
        m_app = re.search(r"\b(?:open|launch|start)\s+(?:the\s+)?(chrome|chromium|firefox|vscode|vs\s*code|mousepad|terminal|lxterminal|calculator|galculator)\b", text, re.I)
        if m_app:
            target_app = m_app.group(1).lower().strip()
            return CapabilityIntentMatch(
                capability_id="desktop-pc-tools",
                action_id="open_application",
                confidence=0.91,
                extracted_parameters={"app_name": target_app},
                matched_pattern="open_application",
                rationale=f"Detected desktop application launch request for {target_app}.",
            )

        return None

    def _match_modules(self, text: str) -> Optional[CapabilityIntentMatch]:
        """Match against the 43 feature suite extension modules."""
        caps = [c for c in self.registry.list_capabilities() if c.id.startswith("module:")]
        text_lower = text.lower()

        # Check regex triggers first
        for cap in caps:
            for pat in cap.regex_triggers:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    extracted: Dict[str, Any] = {"instruction": text}
                    if m.groups():
                        extracted["target"] = m.group(1)
                    return CapabilityIntentMatch(
                        capability_id=cap.id,
                        action_id="execute",
                        confidence=0.88,
                        extracted_parameters=extracted,
                        matched_pattern=pat,
                        rationale=f"Matched regex pattern for {cap.name}.",
                    )

        # Keyword scoring fallback for module matching
        best_cap: Optional[Any] = None
        best_score = 0.0
        words = set(re.findall(r"\w+", text_lower))

        for cap in caps:
            score = 0.0
            for kw in cap.keywords:
                kw_lower = kw.lower()
                if kw_lower in text_lower:
                    score += 1.5
                else:
                    kw_words = set(re.findall(r"\w+", kw_lower))
                    if kw_words and kw_words.issubset(words):
                        score += 1.0

            if score > best_score:
                best_score = score
                best_cap = cap

        if best_cap and best_score >= 1.5:
            conf = min(0.85, 0.60 + (best_score * 0.08))
            return CapabilityIntentMatch(
                capability_id=best_cap.id,
                action_id="execute",
                confidence=conf,
                extracted_parameters={"instruction": text},
                matched_pattern="keyword_similarity",
                rationale=f"Matched high keyword confidence ({best_score:.1f}) for {best_cap.name}.",
            )

        return None


_ROUTER_INSTANCE: Optional[AutonomousCapabilityRouter] = None


def get_capability_router() -> AutonomousCapabilityRouter:
    """Return the global singleton AutonomousCapabilityRouter."""
    global _ROUTER_INSTANCE
    if _ROUTER_INSTANCE is None:
        _ROUTER_INSTANCE = AutonomousCapabilityRouter()
    return _ROUTER_INSTANCE
