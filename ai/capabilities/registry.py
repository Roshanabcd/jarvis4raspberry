"""
JARVIS Unified Capability Registry.
Catalogs all 45+ built-in applications, feature suite extension modules (#1 to #43),
local developer coding CLIs (Antigravity, Claude, Codex, Copilot, Hermes, Aider, OpenCode, Cline),
and dynamic marketplace plugins into a single queryable catalog.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from ai.capabilities.models import (
    Capability,
    CapabilityAction,
    CapabilityCategory,
    CapabilityParameter,
)

logger = logging.getLogger("JARVIS.Capabilities.Registry")

_CATEGORY_MAP = {
    "ai_agents": CapabilityCategory.AI_AGENTS,
    "developer_tools": CapabilityCategory.DEVELOPER_TOOLS,
    "research_knowledge": CapabilityCategory.RESEARCH_KNOWLEDGE,
    "computer_vision": CapabilityCategory.COMPUTER_VISION,
    "education_learning": CapabilityCategory.EDUCATION_LEARNING,
    "media_content": CapabilityCategory.MEDIA_CONTENT,
    "business_support": CapabilityCategory.BUSINESS_SUPPORT,
    "productivity": CapabilityCategory.PRODUCTIVITY,
    "security_analytics": CapabilityCategory.SECURITY_ANALYTICS,
    "experimental": CapabilityCategory.EXPERIMENTAL,
    "governance": CapabilityCategory.GOVERNANCE,
    "notifications": CapabilityCategory.NOTIFICATIONS,
    "management": CapabilityCategory.MANAGEMENT,
    "pc_automation": CapabilityCategory.PC_AUTOMATION,
}


class CapabilityRegistry:
    """Central registry and discoverer for all JARVIS capabilities."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, Capability] = {}
        self._initialized = False
        self._initialize_core_capabilities()
        self._initialize_developer_clis()
        self._discover_feature_modules()
        self._initialized = True

    def _initialize_core_capabilities(self) -> None:
        """Register canonical built-in JARVIS applications and PC tools."""
        core_defs: List[Capability] = [
            Capability(
                id="youtube-summarizer",
                name="YouTube Video Summarizer",
                category=CapabilityCategory.MEDIA_CONTENT,
                tier="medium",
                description="Extract transcripts, chapters, and generate grounded summaries from YouTube videos.",
                route="/apps/youtube-summarizer",
                target_tab="youtube",
                keywords=["youtube", "video", "yt", "transcript", "summarize video", "youtube summary", "watch"],
                regex_triggers=[
                    r"\b(?:summarize|transcribe|explain|analyze|breakdown)\s+(?:the\s+)?(?:youtube|yt)?\s*(?:video|clip|link)?\s*(https?://(?:www\.)?(?:youtube\.com|youtu\.be)\S+)",
                    r"\b(?:youtube|yt)\.com/\S+",
                    r"\byoutu\.be/\S+",
                    r"\b(?:summarize|transcribe)\s+(?:the\s+)?(?:current|playing|latest|open)\s+(?:video|youtube)\b",
                ],
                actions=[
                    CapabilityAction(
                        action_id="summarize_video",
                        name="Summarize YouTube Video",
                        description="Summarize a YouTube video given its URL or current playing context.",
                        parameters=[
                            CapabilityParameter(name="url", type="string", description="Full YouTube video URL", required=False),
                            CapabilityParameter(name="style", type="string", description="Summary style: brief, detailed, bullets", required=False, default="detailed"),
                        ],
                    ),
                    CapabilityAction(
                        action_id="get_transcript",
                        name="Get Video Transcript",
                        description="Extract raw timestamped transcript for a YouTube video.",
                        parameters=[
                            CapabilityParameter(name="url", type="string", description="YouTube video URL", required=False),
                        ],
                    ),
                ],
            ),
            Capability(
                id="document-qa",
                name="Document Question Answering",
                category=CapabilityCategory.RESEARCH_KNOWLEDGE,
                tier="medium",
                description="Upload, index, hybrid-search, and perform grounded RAG over PDF, DOCX, MD, and CSV files.",
                route="/apps/document-qa",
                target_tab="documents",
                keywords=["document", "doc", "pdf", "docx", "rag", "document qa", "knowledge base", "index file"],
                regex_triggers=[
                    r"\b(?:search|query|ask|find\s+in)\s+(?:documents?|docs?|pdfs?|knowledge\s+base)\s*(?:about|for)?\s*(.+)",
                    r"\bwhat\s+(?:does|do)\s+(?:the\s+)?(?:document|doc|pdf|files?)\s+say\s+about\s+(.+)",
                    r"\bindex\s+(?:file|document|pdf)\s+(\S+)",
                ],
                actions=[
                    CapabilityAction(
                        action_id="query_documents",
                        name="Query Documents",
                        description="Perform semantic + BM25 hybrid search over indexed documents with citations.",
                        parameters=[
                            CapabilityParameter(name="query", type="string", description="Search inquiry or question", required=True),
                            CapabilityParameter(name="top_k", type="int", description="Number of passages to retrieve", required=False, default=5),
                        ],
                    ),
                    CapabilityAction(
                        action_id="index_document",
                        name="Index Document",
                        description="Extract text and index a document into the vector store.",
                        parameters=[
                            CapabilityParameter(name="file_path", type="string", description="Path to PDF/DOCX/MD file", required=True),
                        ],
                    ),
                ],
            ),
            Capability(
                id="research-assistant",
                name="AI Research Assistant",
                category=CapabilityCategory.RESEARCH_KNOWLEDGE,
                tier="heavy",
                description="Literature synthesis, academic search, structured literature review, and BibTeX citations.",
                route="/apps/research-assistant",
                target_tab="research",
                keywords=["research", "literature review", "academic", "paper", "arxiv", "citations", "survey"],
                regex_triggers=[
                    r"\b(?:conduct|do|perform|generate)\s+(?:a\s+)?research\s+(?:on|about)?\s*(.+)",
                    r"\bliterature\s+review\s+(?:on|for)\s+(.+)",
                    r"\bsearch\s+(?:academic\s+papers?|arxiv)\s+for\s+(.+)",
                ],
                actions=[
                    CapabilityAction(
                        action_id="synthesize_research",
                        name="Synthesize Research Topic",
                        description="Generate an academic research briefing with citations and methodology breakdown.",
                        parameters=[
                            CapabilityParameter(name="topic", type="string", description="Research subject or hypothesis", required=True),
                            CapabilityParameter(name="depth", type="string", description="Depth: quick, standard, deep", required=False, default="standard"),
                        ],
                    ),
                ],
            ),
            Capability(
                id="face-recognition",
                name="Real-Time Face Recognition",
                category=CapabilityCategory.COMPUTER_VISION,
                tier="lightweight",
                description="Biometric face identification, enrollment, and verification using YuNet and SFace.",
                route="/vision",
                target_tab="vision",
                keywords=["face", "who is looking", "recognize me", "face recognition", "biometrics", "who is there"],
                regex_triggers=[
                    r"\b(?:who\s+is\s+(?:looking|in\s+front|there)|recognize\s+(?:my\s+face|me|person)|scan\s+face)\b",
                    r"\bface\s+(?:recognition|verification|status|enroll)\b",
                ],
                actions=[
                    CapabilityAction(
                        action_id="identify_face",
                        name="Identify Face",
                        description="Capture camera frame and identify active user from biometrics database.",
                        parameters=[],
                    ),
                    CapabilityAction(
                        action_id="list_enrolled",
                        name="List Enrolled Faces",
                        description="List all enrolled biometric profiles and their assigned roles.",
                        parameters=[],
                    ),
                ],
            ),
            Capability(
                id="system-telemetry",
                name="System Health & Diagnostics",
                category=CapabilityCategory.SECURITY_ANALYTICS,
                tier="lightweight",
                description="Real-time Linux OS telemetry (CPU, RAM, SoC temperature, disk, process list, uptime).",
                route="/system-health",
                target_tab="system",
                keywords=["system status", "health", "cpu usage", "ram", "memory", "temperature", "disk usage", "telemetry"],
                regex_triggers=[
                    r"\b(?:check|show|get|report)\s+(?:system\s+status|health|telemetry|cpu|ram|memory|temp(?:erature)?)\b",
                    r"\bhow\s+(?:healthy|hot|busy)\s+is\s+(?:the\s+)?(?:system|pi|server|cpu)\b",
                    r"\b(uptime|system\s+info|hardware\s+status)\b",
                ],
                actions=[
                    CapabilityAction(
                        action_id="get_status",
                        name="Get System Status",
                        description="Retrieve CPU %, RAM usage, Broadcom SoC temperature, disk utilization.",
                        parameters=[],
                    ),
                ],
            ),
            Capability(
                id="desktop-pc-tools",
                name="Desktop & PC Automation",
                category=CapabilityCategory.PC_AUTOMATION,
                tier="medium",
                description="Launch desktop applications, control windows, manipulate browsers, and execute terminal commands.",
                route="/desktop",
                keywords=["open app", "launch", "start app", "switch window", "terminal", "browser", "click", "mouse"],
                regex_triggers=[
                    r"\b(?:open|launch|start)\s+(?:the\s+)?(chrome|chromium|firefox|vscode|vs\s*code|mousepad|terminal|lxterminal|calculator|galculator)\b",
                    r"\bswitch\s+(?:back\s+)?to\s+(?:window\s+)?(\S+)\b",
                ],
                actions=[
                    CapabilityAction(
                        action_id="open_application",
                        name="Open Application",
                        description="Launch a desktop application or browser by name.",
                        parameters=[
                            CapabilityParameter(name="app_name", type="string", description="Name of application to launch", required=True),
                            CapabilityParameter(name="target", type="string", description="Optional argument or URL to open with the app", required=False),
                        ],
                    ),
                    CapabilityAction(
                        action_id="switch_window",
                        name="Switch Window",
                        description="Focus or activate a specific desktop window.",
                        parameters=[
                            CapabilityParameter(name="window_name", type="string", description="Title or application name of window", required=True),
                        ],
                    ),
                ],
            ),
        ]
        for cap in core_defs:
            self._capabilities[cap.id] = cap

    def _initialize_developer_clis(self) -> None:
        """Register local developer coding CLIs as first-class capabilities."""
        cli_defs = [
            ("antigravity", "Google Antigravity CLI ('agy')", ["antigravity", "agy", "deepmind agent", "antigravity ide"],
             [r"\b(?:run|ask|use|with|execute)\s+(?:antigravity|agy)\b", r"\bagy\s+.*"]),
            ("claude", "Anthropic Claude Code CLI", ["claude", "claude code", "anthropic cli"],
             [r"\b(?:run|ask|use|with|execute)\s+claude\b", r"\bclaude\s+.*"]),
            ("codex", "OpenAI Codex CLI", ["codex", "openai codex", "codex cli"],
             [r"\b(?:run|ask|use|with|execute)\s+codex\b", r"\bcodex\s+.*"]),
            ("copilot", "GitHub Copilot CLI", ["copilot", "github copilot", "gh copilot"],
             [r"\b(?:run|ask|use|with|execute)\s+(?:github\s+)?copilot\b"]),
            ("hermes", "Hermes Agent CLI", ["hermes", "hermes agent"],
             [r"\b(?:run|ask|use|with|execute)\s+hermes\b"]),
            ("aider", "Aider AI Pair Programming CLI", ["aider", "aider chat"],
             [r"\b(?:run|ask|use|with|execute)\s+aider\b"]),
            ("opencode", "OpenCode CLI", ["opencode", "opencode agent"],
             [r"\b(?:run|ask|use|with|execute)\s+opencode\b"]),
            ("cline", "Cline Autonomous Coding CLI", ["cline", "cline agent"],
             [r"\b(?:run|ask|use|with|execute)\s+cline\b"]),
        ]

        for cli_name, display_name, keywords, triggers in cli_defs:
            cap_id = f"developer-cli:{cli_name}"
            cap = Capability(
                id=cap_id,
                name=display_name,
                category=CapabilityCategory.DEVELOPER_TOOLS,
                tier="heavy",
                description=f"Direct command bridge to local AI developer coding CLI '{cli_name}'. Supports repository diagnosis, refactoring, test fixes, and automated debugging.",
                route="/developer",
                keywords=keywords + ["coding cli", "developer agent", "code repair", "bug fix", "refactor"],
                regex_triggers=triggers,
                is_cli=True,
                is_builtin=False,
                minimum_role="USER",
                metadata={"cli_name": cli_name},
                actions=[
                    CapabilityAction(
                        action_id="run_task",
                        name=f"Run Task via {cli_name.title()}",
                        description=f"Execute coding or diagnostic task using local CLI {cli_name}.",
                        parameters=[
                            CapabilityParameter(name="prompt", type="string", description="Coding task instruction", required=True),
                            CapabilityParameter(name="timeout", type="int", description="Execution timeout seconds", required=False, default=45),
                        ],
                    ),
                    CapabilityAction(
                        action_id="diagnose",
                        name=f"Diagnose Repository via {cli_name.title()}",
                        description=f"Run read-only system/repo diagnosis using {cli_name}.",
                        parameters=[
                            CapabilityParameter(name="prompt", type="string", description="Diagnostic focus prompt", required=False, default="Diagnose repository and suggest fixes"),
                        ],
                    ),
                ],
            )
            self._capabilities[cap_id] = cap

    def _discover_feature_modules(self) -> None:
        """Dynamically ingest all modules from jarvis_feature_suite_loader."""
        try:
            from jarvis_feature_suite_loader.loader import FEATURE_REGISTRY
        except Exception as exc:
            logger.warning("Could not import FEATURE_REGISTRY: %s", exc)
            return

        for spec in FEATURE_REGISTRY:
            mod_num = spec.get("module_number")
            mod_id = spec.get("id")
            name = spec.get("name")
            desc = spec.get("description", "")
            raw_cat = spec.get("category", "ai_agents").lower().replace(" ", "_").replace("&", "").replace("-", "_")
            cat = _CATEGORY_MAP.get(raw_cat, CapabilityCategory.AI_AGENTS)
            tier = (spec.get("tier") or "medium").lower()

            cap_id = f"module:{mod_num}:{mod_id}"
            keywords = [
                name.lower(),
                mod_id.replace("_", " "),
                f"module {mod_num}",
                spec.get("ui_path", "").lstrip("/").replace("-", " "),
            ]
            
            # Formulate smart regex triggers based on the module's core nature
            triggers = self._generate_module_triggers(mod_num, mod_id, name)

            actions = self._generate_module_actions(mod_num, mod_id, name)

            cap = Capability(
                id=cap_id,
                name=f"{name} (Module #{mod_num})",
                category=cat,
                tier=tier,
                description=desc,
                route=spec.get("ui_path"),
                keywords=keywords,
                regex_triggers=triggers,
                actions=actions,
                minimum_role="ADMIN" if mod_num in {6, 7, 12, 33, 40} else "USER",
                is_builtin=False,
                metadata={"module_number": mod_num, "package": spec.get("package")},
            )
            self._capabilities[cap_id] = cap

    def _generate_module_triggers(self, mod_num: int, mod_id: str, name: str) -> List[str]:
        """Generate targeted regex intent triggers for each module number."""
        clean_name = name.lower()
        triggers = [
            rf"\b(?:open|launch|run|trigger|start)\s+(?:module\s+)?{mod_num}\b",
            rf"\b{re.escape(clean_name)}\b",
        ]

        specific_triggers = {
            1: [r"\b(?:generate|write|refactor|fix)\s+(?:the\s+)?code\b", r"\bcoding\s+assistant\b"],
            2: [r"\b(?:generate|create|write)\s+(?:a\s+)?(?:blog|content|script|carousel|outline)\b"],
            3: [r"\b(?:start|conduct|simulate)\s+(?:an?\s+)?interview\b", r"\binterview\s+bot\b"],
            4: [r"\b(?:schedule|plan|post)\s+(?:social\s+media|tweet|linkedin)\b"],
            5: [r"\b(?:create|plan)\s+(?:a\s+)?study\s+(?:plan|schedule)\b", r"\bstudy\s+planner\b"],
            6: [r"\b(?:paper\s+trade|backtest|trading\s+bot|check\s+market)\b"],
            7: [r"\b(?:scrape|crawl)\s+(?:website|url|page)?\s*(https?://\S+)", r"\bweb\s+scraping\b"],
            8: [r"\b(?:customer\s+support|support\s+ticket|helpdesk)\b"],
            9: [r"\b(?:recommend|recommendation\s+engine)\b"],
            11: [r"\b(?:dense\s+search|semantic\s+search|ai\s+search\s+engine)\b"],
            12: [r"\b(?:detect|check\s+for)\s+fraud\b", r"\bfraud\s+detection\b"],
            13: [r"\b(?:learning\s+coach|socratic\s+tutor|explain\s+concept\s+to\s+me)\b"],
            14: [r"\b(?:translate\s+speech|speech\s+translation|realtime\s+translate)\b"],
            15: [r"\b(?:match\s+resume|analyze\s+cv|resume\s+matching)\b"],
            16: [r"\b(?:convert\s+handwriting|handwriting\s+ocr|extract\s+handwritten)\b"],
            17: [r"\b(?:detect\s+objects?|real-time\s+object\s+detection|track\s+objects?)\b"],
            18: [r"\b(?:multi-?agent|orchestrat(?:e|or)|task\s+dag|workflow\s+dag)\b"],
            19: [r"\b(?:computer\s+assistant|automate\s+computer|desktop\s+assistant)\b"],
            20: [r"\b(?:conversational\s+ai|realtime\s+dialogue|voice\s+conversation)\b"],
            21: [r"\b(?:browse\s+web|browser\s+agent|intelligent\s+browser)\b"],
            22: [r"\b(?:route\s+model|model\s+router|select\s+best\s+model)\b"],
            23: [r"\b(?:executive\s+assistant|daily\s+briefing|personal\s+assistant)\b"],
            24: [r"\b(?:check\s+email|triage\s+inbox|schedule\s+meeting|calendar\s+schedule|free\s+slots?)\b"],
            25: [r"\b(?:meeting\s+assistant|meeting\s+notes|summarize\s+meeting)\b"],
            26: [r"\b(?:project\s+autopilot|autopilot\s+project|milestone\s+plan)\b"],
            27: [r"\b(?:github\s+prs?|ci/?cd|trigger\s+workflow|check\s+repo\s+pipeline)\b"],
            28: [r"\b(?:analyze\s+data|data\s+analyst|dataset\s+summary|csv\s+analysis)\b"],
            29: [r"\b(?:organize\s+files|advanced\s+file\s+manager|deduplicate\s+files)\b"],
            30: [r"\b(?:smart\s+home|turn\s+(?:on|off)\s+light|adjust\s+thermostat|home\s+devices?)\b"],
            31: [r"\b(?:robot\s+brain|navigate\s+robot|robot\s+mission)\b"],
            32: [r"\b(?:system\s+diagnostics|deep\s+health\s+check|diagnostic\s+report)\b"],
            33: [r"\b(?:cybersecurity|security\s+audit|defensive\s+scan|vulnerability\s+scan)\b"],
            34: [r"\b(?:personal\s+finance|track\s+expenses?|budget\s+report|spending)\b"],
            35: [r"\b(?:visual\s+workflow|workflow\s+builder|pipeline\s+builder)\b"],
            36: [r"\b(?:screen\s+vision|ocr\s+screen|look\s+at\s+display)\b"],
            37: [r"\b(?:cross\s+device|device\s+control|control\s+other\s+device)\b"],
            38: [r"\b(?:marketplace|plugin\s+skills|install\s+skill)\b"],
            39: [r"\b(?:backup\s+manager|create\s+backup|restore\s+backup)\b"],
            40: [r"\b(?:permission\s+approval|approval\s+center|pending\s+requests?)\b"],
            41: [r"\b(?:notifications?|send\s+alert|notification\s+center)\b"],
            42: [r"\b(?:extension\s+manager|manage\s+extensions|unified\s+extensions)\b"],
            43: [r"\b(?:screen\s+guardian|screen\s+repair|auto\s+repair\s+agent)\b"],
        }
        if mod_num in specific_triggers:
            triggers.extend(specific_triggers[mod_num])

        return triggers

    def _generate_module_actions(self, mod_num: int, mod_id: str, name: str) -> List[CapabilityAction]:
        """Provide standard invocation actions for a module."""
        return [
            CapabilityAction(
                action_id="execute",
                name=f"Execute {name}",
                description=f"Invoke operational action for {name}.",
                parameters=[
                    CapabilityParameter(name="payload", type="dict", description="Action parameters dictionary", required=False, default={}),
                    CapabilityParameter(name="instruction", type="string", description="Natural language intent/directive", required=False),
                ],
                requires_admin=mod_num in {6, 7, 12, 33, 40},
            ),
            CapabilityAction(
                action_id="status",
                name=f"Get {name} Status",
                description=f"Query current operational and health status of {name}.",
                parameters=[],
            ),
        ]

    # --- Public Accessors & Dynamic Plugin Registration ---

    def list_capabilities(self, category: Optional[CapabilityCategory] = None) -> List[Capability]:
        """Return all registered capabilities optionally filtered by category."""
        caps = list(self._capabilities.values())
        if category:
            caps = [c for c in caps if c.category == category]
        return caps

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """Retrieve capability by exact ID or alias."""
        if capability_id in self._capabilities:
            return self._capabilities[capability_id]
        
        # Check alias (e.g. 'claude' -> 'developer-cli:claude')
        if f"developer-cli:{capability_id}" in self._capabilities:
            return self._capabilities[f"developer-cli:{capability_id}"]
        
        # Check module number alias (e.g. 'module:24' -> 'module:24:email_calendar_assistant')
        for k, v in self._capabilities.items():
            if k.startswith(f"module:{capability_id}:") or k == capability_id:
                return v

        return None

    def register_capability(self, capability: Capability) -> None:
        """Register a dynamic capability (e.g. from a plugin or runtime extension)."""
        logger.info("Registering capability: %s (%s)", capability.id, capability.name)
        self._capabilities[capability.id] = capability

    def unregister_capability(self, capability_id: str) -> bool:
        """Remove a dynamic capability."""
        if capability_id in self._capabilities:
            del self._capabilities[capability_id]
            logger.info("Unregistered capability: %s", capability_id)
            return True
        return False

    @property
    def total_count(self) -> int:
        return len(self._capabilities)


_REGISTRY_INSTANCE: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """Return the global singleton CapabilityRegistry."""
    global _REGISTRY_INSTANCE
    if _REGISTRY_INSTANCE is None:
        _REGISTRY_INSTANCE = CapabilityRegistry()
    return _REGISTRY_INSTANCE
