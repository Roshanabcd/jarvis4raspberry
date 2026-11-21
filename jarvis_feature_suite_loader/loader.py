"""Dynamic registry and safe additive mounter for all 42 JARVIS OS feature modules."""

from __future__ import annotations

import importlib
import logging
import os
import psutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger("JARVIS.FeatureSuite")

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"

# State for dynamically disabled modules
_DISABLED_MODULES: Set[str] = set()

FEATURE_REGISTRY: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # Original Feature Modules (#1 - #17)
    # -------------------------------------------------------------
    {
        "module_number": 1,
        "id": "ai_coding_assistant",
        "package": "jarvis_ai_coding_assistant",
        "name": "AI Coding Assistant",
        "category": "Developer Tools",
        "tier": "HEAVY",
        "ui_path": "/coding-assistant",
        "health_path": "/api/coding-assistant/health",
        "description": "Code generation, refactoring, static security analysis, and test synthesis.",
        "permissions": ["code:read", "code:write", "shell:execute"],
    },
    {
        "module_number": 2,
        "id": "ai_content_pipeline",
        "package": "jarvis_ai_content_pipeline",
        "name": "AI Content Creation Pipeline",
        "category": "Media & Content",
        "tier": "MEDIUM",
        "ui_path": "/content-pipeline",
        "health_path": "/api/content-pipeline/health",
        "description": "Technical blogs, short-video scripts, hooks, captions, and carousel outlines.",
        "permissions": ["content:generate", "storage:write"],
    },
    {
        "module_number": 3,
        "id": "ai_interview_bot",
        "package": "jarvis_ai_interview_bot",
        "name": "AI Interview Bot",
        "category": "Education & Learning",
        "tier": "MEDIUM",
        "ui_path": "/interview-bot",
        "health_path": "/api/interview-bot/health",
        "description": "Technical and behavioral interview simulation with scoring and feedback.",
        "permissions": ["dialogue:interactive"],
    },
    {
        "module_number": 4,
        "id": "ai_social_automation",
        "package": "jarvis_ai_social_automation",
        "name": "AI Social Media Automation",
        "category": "Business & Support",
        "tier": "MEDIUM",
        "ui_path": "/social-automation",
        "health_path": "/api/social-automation/health",
        "description": "Multi-platform content planning, copy generation, scheduling, and analytics.",
        "permissions": ["social:schedule", "content:write"],
    },
    {
        "module_number": 5,
        "id": "ai_study_planner",
        "package": "jarvis_ai_study_planner",
        "name": "AI Study Planner",
        "category": "Education & Learning",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/study-planner",
        "health_path": "/api/study-planner/health",
        "description": "Personalized study schedules, goal breakdown, and spaced-repetition tracking.",
        "permissions": ["calendar:write", "analytics:read"],
    },
    {
        "module_number": 6,
        "id": "autonomous_trading_bot",
        "package": "jarvis_autonomous_trading_bot",
        "name": "Autonomous Trading Bot",
        "category": "Experimental",
        "tier": "HEAVY",
        "ui_path": "/trading-bot",
        "health_path": "/api/trading-bot/health",
        "description": "Safety-locked paper trading, technical indicators, backtesting, and E-STOP.",
        "permissions": ["market:read", "paper_trade:execute"],
    },
    {
        "module_number": 7,
        "id": "web_scraping_agent",
        "package": "jarvis_web_scraping_agent",
        "name": "Autonomous Web Scraping Agent",
        "category": "Research & Knowledge",
        "tier": "MEDIUM",
        "ui_path": "/web-scraper",
        "health_path": "/api/web-scraper/health",
        "description": "Policy-compliant HTML extraction, SSRF guards, change monitoring, and JSON export.",
        "permissions": ["network:fetch", "storage:write"],
    },
    {
        "module_number": 8,
        "id": "customer_support_bot",
        "package": "jarvis_customer_support_bot",
        "name": "ChatGPT-Powered Customer Support Bot",
        "category": "Business & Support",
        "tier": "MEDIUM",
        "ui_path": "/support-bot",
        "health_path": "/api/support-bot/health",
        "description": "Domain KB answering, ticket triage, sentiment classification, and escalation.",
        "permissions": ["kb:read", "tickets:manage"],
    },
    {
        "module_number": 9,
        "id": "recommendation_engine",
        "package": "jarvis_recommendation_engine",
        "name": "Deep Learning Recommendation Engine",
        "category": "Business & Support",
        "tier": "HEAVY",
        "ui_path": "/recommendations",
        "health_path": "/api/recommendations/health",
        "description": "Hybrid 128-D semantic embeddings, collaborative filtering, and SGD latent factors.",
        "permissions": ["embeddings:compute", "data:read"],
    },
    {
        "module_number": 10,
        "id": "document_qa",
        "package": "jarvis_document_qa",
        "name": "Document Question Answering",
        "category": "Research & Knowledge",
        "tier": "MEDIUM",
        "ui_path": "/doc-qa",
        "health_path": "/api/doc-qa/health",
        "description": "Upload, index, search, and perform cited QA over PDF, Markdown, and text docs.",
        "permissions": ["docs:read", "search:execute"],
    },
    {
        "module_number": 11,
        "id": "ai_search_engine",
        "package": "jarvis_ai_search_engine",
        "name": "End-to-End AI Search Engine",
        "category": "Research & Knowledge",
        "tier": "HEAVY",
        "ui_path": "/ai-search",
        "health_path": "/api/ai-search/health",
        "description": "Unified semantic + BM25 RRF search over docs, logs, codebases, and web notes.",
        "permissions": ["index:search", "index:write"],
    },
    {
        "module_number": 12,
        "id": "fraud_detection",
        "package": "jarvis_fraud_detection",
        "name": "Fraud Detection System",
        "category": "Security & Analytics",
        "tier": "HEAVY",
        "ui_path": "/fraud-detection",
        "health_path": "/api/fraud-detection/health",
        "description": "Anomaly detection across transactions, authentication logs, and audit entries.",
        "permissions": ["audit:read", "security:alert"],
    },
    {
        "module_number": 13,
        "id": "learning_coach",
        "package": "jarvis_learning_coach",
        "name": "Personalized Learning AI Coach",
        "category": "Education & Learning",
        "tier": "MEDIUM",
        "ui_path": "/learning-coach",
        "health_path": "/api/learning-coach/health",
        "description": "Socratic tutoring, concept mastery diagnostics, and adaptive exercises.",
        "permissions": ["tutoring:evaluate", "profile:read"],
    },
    {
        "module_number": 14,
        "id": "speech_translation",
        "package": "jarvis_speech_translation",
        "name": "Real-Time Speech Translation",
        "category": "Education & Learning",
        "tier": "HEAVY",
        "ui_path": "/speech-translation",
        "health_path": "/api/speech-translation/health",
        "description": "Continuous bilingual speech recognition, WebSocket translation, and voice playback.",
        "permissions": ["audio:record", "audio:play"],
    },
    {
        "module_number": 15,
        "id": "resume_matching",
        "package": "jarvis_resume_matching",
        "name": "Smart Resume Matching",
        "category": "Business & Support",
        "tier": "MEDIUM",
        "ui_path": "/resume-matching",
        "health_path": "/api/resume-matching/health",
        "description": "Automated skill extraction, qualification scoring, and semantic gap analysis.",
        "permissions": ["resume:parse", "scores:compute"],
    },
    {
        "module_number": 16,
        "id": "handwriting_ocr",
        "package": "jarvis_handwriting_ocr",
        "name": "Handwritten to Text Converter",
        "category": "Research & Knowledge",
        "tier": "MEDIUM",
        "ui_path": "/handwriting-ocr",
        "health_path": "/api/handwriting-ocr/health",
        "description": "Upload handwritten photos or draw on a live canvas to extract clean digital text.",
        "permissions": ["vision:ocr", "files:read"],
    },
    {
        "module_number": 17,
        "id": "object_detection",
        "package": "jarvis_object_detection",
        "name": "Real-Time Object Detection",
        "category": "Computer Vision",
        "tier": "HEAVY",
        "ui_path": "/object-detection",
        "health_path": "/api/object-detection/health",
        "description": "Real-time YOLO/offline object detection, centroid tracking, ROI zones, and WebSocket HUD.",
        "permissions": ["camera:read", "vision:infer"],
    },

    # -------------------------------------------------------------
    # Extension Modules (#18 - #42)
    # -------------------------------------------------------------
    {
        "module_number": 18,
        "id": "multi_agent_orchestrator",
        "package": "modules.module_18_multi_agent_orchestrator",
        "name": "Multi-Agent Task Orchestrator",
        "category": "Core AI OS",
        "tier": "MEDIUM",
        "ui_path": "/orchestrator",
        "health_path": "/api/v1/orchestrator/health",
        "description": "Unified multi-agent execution engine with DAG scheduling, bounded concurrency, approvals, and persistent state.",
        "permissions": ["orchestrator:write", "agent:execute"],
    },
    {
        "module_number": 19,
        "id": "autonomous_computer_assistant",
        "package": "modules.module_19_autonomous_computer_assistant",
        "name": "Autonomous Computer Assistant",
        "category": "Core AI OS",
        "tier": "MEDIUM",
        "ui_path": "/computer-assistant",
        "health_path": "/api/v1/computer-assistant/health",
        "description": "Sandboxed desktop execution agent with policy authorization and emergency abort.",
        "permissions": ["desktop:control", "shell:execute"],
    },
    {
        "module_number": 20,
        "id": "realtime_conversational_ai",
        "package": "modules.module_20_realtime_conversational_ai",
        "name": "Real-Time Conversational AI",
        "category": "Core AI OS",
        "tier": "HEAVY",
        "ui_path": "/conversational-ai",
        "health_path": "/api/v1/conversational-ai/health",
        "description": "Low-latency streaming conversation with state management and fallback providers.",
        "permissions": ["voice:record", "voice:synthesize"],
    },
    {
        "module_number": 21,
        "id": "intelligent_browser_agent",
        "package": "modules.module_21_intelligent_browser_agent",
        "name": "Intelligent Browser Agent",
        "category": "Core AI OS",
        "tier": "MEDIUM",
        "ui_path": "/browser-agent",
        "health_path": "/api/v1/browser-agent/health",
        "description": "Safe headless browser navigation with DOM extraction and SSRF protection.",
        "permissions": ["browser:navigate", "network:read"],
    },
    {
        "module_number": 22,
        "id": "intelligent_model_router",
        "package": "modules.module_22_intelligent_model_router",
        "name": "Intelligent AI Model Router",
        "category": "Core AI OS",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/model-router",
        "health_path": "/api/v1/model-router/health",
        "description": "Multi-provider model routing, cost tracking, latency budgets, and fallback orchestration.",
        "permissions": ["models:route", "api:admin"],
    },
    {
        "module_number": 23,
        "id": "personal_executive_assistant",
        "package": "modules.module_23_personal_executive_assistant",
        "name": "Personal Executive Assistant",
        "category": "Productivity",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/executive-assistant",
        "health_path": "/api/v1/executive-assistant/health",
        "description": "Executive briefing, task triage, schedule preparation, and priority tracking.",
        "permissions": ["assistant:read", "assistant:write"],
    },
    {
        "module_number": 24,
        "id": "email_calendar_assistant",
        "package": "modules.module_24_email_calendar_assistant",
        "name": "Email & Calendar Assistant",
        "category": "Productivity",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/email-calendar",
        "health_path": "/api/v1/email-calendar/health",
        "description": "Intelligent inbox triaging, draft generation, and conflict-free calendar booking.",
        "permissions": ["calendar:manage", "email:send"],
    },
    {
        "module_number": 25,
        "id": "ai_meeting_assistant",
        "package": "modules.module_25_ai_meeting_assistant",
        "name": "AI Meeting Assistant",
        "category": "Productivity",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/meeting-assistant",
        "health_path": "/api/v1/meeting-assistant/health",
        "description": "Real-time agenda tracking, transcript summarization, and action item extraction.",
        "permissions": ["meeting:record", "notes:write"],
    },
    {
        "module_number": 26,
        "id": "project_autopilot",
        "package": "modules.module_26_project_autopilot",
        "name": "Project Autopilot",
        "category": "Engineering",
        "tier": "MEDIUM",
        "ui_path": "/project-autopilot",
        "health_path": "/api/v1/project-autopilot/health",
        "description": "Autonomous backlog decomposition, milestone tracking, and sprint planning.",
        "permissions": ["project:plan", "tasks:dispatch"],
    },
    {
        "module_number": 27,
        "id": "github_cicd_manager",
        "package": "modules.module_27_github_cicd_manager",
        "name": "GitHub & CI/CD Manager",
        "category": "DevOps",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/github-cicd",
        "health_path": "/api/v1/github-cicd/health",
        "description": "Repository automation, PR reviews, CI failure triage, and branch protection.",
        "permissions": ["git:read", "cicd:trigger"],
    },
    {
        "module_number": 28,
        "id": "ai_data_analyst",
        "package": "modules.module_28_ai_data_analyst",
        "name": "AI Data Analyst",
        "category": "Analytics",
        "tier": "MEDIUM",
        "ui_path": "/ai-data-analyst",
        "health_path": "/api/v1/ai-data-analyst/health",
        "description": "Automated dataset profiling, exploratory analysis, trend forecasting, and charting.",
        "permissions": ["data:query", "reports:generate"],
    },
    {
        "module_number": 29,
        "id": "advanced_file_manager",
        "package": "modules.module_29_advanced_file_manager",
        "name": "Advanced File Manager",
        "category": "Productivity",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/file-manager",
        "health_path": "/api/v1/file-manager/health",
        "description": "Semantic file indexing, deduplication, metadata tagging, and secure operations.",
        "permissions": ["fs:read", "fs:write"],
    },
    {
        "module_number": 30,
        "id": "smart_home_controller",
        "package": "modules.module_30_smart_home_controller",
        "name": "Smart Home Controller",
        "category": "IoT Automation",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/smart-home",
        "health_path": "/api/v1/smart-home/health",
        "description": "Device state coordination, automated scene execution, and local IoT bridge.",
        "permissions": ["iot:read", "iot:control"],
    },
    {
        "module_number": 31,
        "id": "robot_brain",
        "package": "modules.module_31_robot_brain",
        "name": "JARVIS Robot Brain",
        "category": "Robotics",
        "tier": "MEDIUM",
        "ui_path": "/robot-brain",
        "health_path": "/api/v1/robot-brain/health",
        "description": "Simulation-first kinematic planner, waypoint navigator, and hardware emergency stop.",
        "permissions": ["robot:telemetry", "robot:arm"],
    },
    {
        "module_number": 32,
        "id": "system_health_diagnostics",
        "package": "modules.module_32_system_health_diagnostics",
        "name": "System Health & Diagnostics",
        "category": "Observability",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/system-health",
        "health_path": "/api/v1/system-health/health",
        "description": "Host telemetry, resource anomaly alerts, disk health, and process monitoring.",
        "permissions": ["system:metrics:read"],
    },
    {
        "module_number": 33,
        "id": "defensive_cybersecurity_agent",
        "package": "modules.module_33_defensive_cybersecurity_agent",
        "name": "Defensive Cybersecurity Agent",
        "category": "Security",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/cybersecurity",
        "health_path": "/api/v1/cybersecurity/health",
        "description": "Security log parsing, failed authentication detection, and port scan alerts.",
        "permissions": ["security:audit:read", "rules:write"],
    },
    {
        "module_number": 34,
        "id": "personal_finance_manager",
        "package": "modules.module_34_personal_finance_manager",
        "name": "Personal Finance Manager",
        "category": "Finance",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/finance",
        "health_path": "/api/v1/finance/health",
        "description": "Budget tracking, expense categorization, and financial goal projections.",
        "permissions": ["finance:read", "budget:write"],
    },
    {
        "module_number": 35,
        "id": "visual_workflow_builder",
        "package": "modules.module_35_visual_workflow_builder",
        "name": "Visual Workflow Builder",
        "category": "Automation",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/workflows",
        "health_path": "/api/v1/workflows/health",
        "description": "Node-based workflow automation editor, trigger execution, and audit trail.",
        "permissions": ["workflow:create", "workflow:run"],
    },
    {
        "module_number": 36,
        "id": "screen_vision_assistant",
        "package": "modules.module_36_screen_vision_assistant",
        "name": "Screen Vision Assistant",
        "category": "Computer Vision",
        "tier": "HEAVY",
        "ui_path": "/vision",
        "health_path": "/api/v1/vision/health",
        "description": "Visual document understanding, UI element detection, and screenshot OCR.",
        "permissions": ["screen:capture", "vision:infer"],
    },
    {
        "module_number": 37,
        "id": "cross_device_control_center",
        "package": "modules.module_37_cross_device_control_center",
        "name": "Cross-Device Control Center",
        "category": "Device Mesh",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/devices",
        "health_path": "/api/v1/devices/health",
        "description": "Device pairing, clipboard synchronization, and peer-to-peer control mesh.",
        "permissions": ["device:pair", "device:message"],
    },
    {
        "module_number": 38,
        "id": "plugin_skills_marketplace",
        "package": "modules.module_38_plugin_skills_marketplace",
        "name": "Plugin & Skills Marketplace",
        "category": "Extensibility",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/marketplace",
        "health_path": "/api/v1/marketplace/health",
        "description": "Extension discovery, community skill packages, version verification, and installs.",
        "permissions": ["plugins:install", "skills:manage"],
    },
    {
        "module_number": 39,
        "id": "backup_recovery_manager",
        "package": "modules.module_39_backup_recovery_manager",
        "name": "Backup & Recovery Manager",
        "category": "Resilience",
        "tier": "MEDIUM",
        "ui_path": "/backups",
        "health_path": "/api/v1/backups/health",
        "description": "Automated system snapshots, database backup rotation, and integrity verification.",
        "permissions": ["backup:create", "restore:execute"],
    },
    {
        "module_number": 40,
        "id": "permissions_approval_center",
        "package": "modules.module_40_permissions_approval_center",
        "name": "Permissions & Approval Center",
        "category": "Governance",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/approvals",
        "health_path": "/api/v1/approvals/health",
        "description": "Fail-closed policy evaluator, human-in-the-loop approval queue, and audit log.",
        "permissions": ["approval:manage", "policy:write"],
    },
    {
        "module_number": 41,
        "id": "universal_notification_center",
        "package": "modules.module_41_universal_notification_center",
        "name": "Universal Notification Center",
        "category": "Notifications",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/notifications",
        "health_path": "/api/v1/notifications/health",
        "description": "Multi-channel alerts, priority routing, audio notification chimes, and history.",
        "permissions": ["notifications:send", "channels:read"],
    },
    {
        "module_number": 42,
        "id": "unified_extension_manager",
        "package": "modules.module_42_unified_extension_manager",
        "name": "Unified Extension Manager & SDK",
        "category": "Management",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/extensions",
        "health_path": "/api/v1/extensions/health",
        "description": "Archive scanner, compatibility analyzer, dynamic registry, health monitor, and shared SDK.",
        "permissions": ["extensions:manage", "sdk:host"],
    },
]


def mount_jarvis_feature_suite(
    app: FastAPI,
    enabled_packages: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Safely discover and mount every installed JARVIS feature module onto a FastAPI app."""
    allow_set = set(enabled_packages) if enabled_packages is not None else None
    feature_statuses: List[Dict[str, Any]] = []
    
    counts = {
        "discovered": len(FEATURE_REGISTRY),
        "installed": 0,
        "configured": 0,
        "enabled": 0,
        "operational": 0,
        "degraded": 0,
        "blocked": 0,
        "failed": 0,
        "mounted": 0,
    }

    for spec in FEATURE_REGISTRY:
        pkg = spec["package"]
        mod_id = spec["id"]
        entry = dict(spec)
        entry["discovered"] = True
        
        # Check enabled state
        is_enabled = (mod_id not in _DISABLED_MODULES) and (allow_set is None or pkg in allow_set)
        entry["enabled"] = is_enabled

        if not is_enabled:
            entry["status"] = "disabled"
            entry["operational_status"] = "disabled"
            entry["installed"] = True
            entry["configured"] = True
            entry["error"] = None
            feature_statuses.append(entry)
            continue

        counts["enabled"] += 1

        try:
            mod = importlib.import_module(pkg)
            entry["installed"] = True
            counts["installed"] += 1
            entry["configured"] = True
            counts["configured"] += 1

            if hasattr(mod, "mount_module"):
                mod.mount_module(app, include_root_ui=False)
                entry["status"] = "available"
                entry["operational_status"] = "operational"
                entry["error"] = None
                counts["mounted"] += 1
                counts["operational"] += 1
            elif hasattr(mod, "create_router"):
                app.include_router(mod.create_router())
                entry["status"] = "available"
                entry["operational_status"] = "operational"
                entry["error"] = None
                counts["mounted"] += 1
                counts["operational"] += 1
            else:
                entry["status"] = "error"
                entry["operational_status"] = "failed"
                entry["error"] = f"Module {pkg} has neither mount_module nor create_router."
                counts["failed"] += 1

        except ModuleNotFoundError as e:
            entry["installed"] = False
            entry["configured"] = False
            entry["status"] = "not_installed"
            entry["operational_status"] = "blocked"
            entry["error"] = f"Package '{pkg}' not found in PYTHONPATH: {e}"
            counts["blocked"] += 1
        except Exception as exc:
            entry["installed"] = True
            entry["configured"] = False
            entry["status"] = "error"
            entry["operational_status"] = "failed"
            entry["error"] = str(exc)
            counts["failed"] += 1

        feature_statuses.append(entry)

    suite_router = APIRouter(tags=["JARVIS Feature Suite"])

    @suite_router.get("/suite", response_class=HTMLResponse, include_in_schema=False)
    def suite_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=500, detail="Suite Launchpad UI missing.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @suite_router.get("/api/suite/health")
    def suite_health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "total_registered": len(feature_statuses),
            "mounted_count": counts["mounted"],
            "discovered_count": counts["discovered"],
            "installed_count": counts["installed"],
            "configured_count": counts["configured"],
            "enabled_count": counts["enabled"],
            "operational_count": counts["operational"],
            "degraded_count": counts["degraded"],
            "blocked_count": counts["blocked"],
            "failed_count": counts["failed"],
            "features": feature_statuses,
        }

    @suite_router.post("/api/suite/modules/{module_id}/toggle")
    def toggle_module(module_id: str) -> Dict[str, Any]:
        found = False
        for spec in FEATURE_REGISTRY:
            if spec["id"] == module_id or str(spec.get("module_number")) == module_id:
                mod_id = spec["id"]
                found = True
                if mod_id in _DISABLED_MODULES:
                    _DISABLED_MODULES.remove(mod_id)
                    action = "enabled"
                else:
                    _DISABLED_MODULES.add(mod_id)
                    action = "disabled"
                return {"status": "ok", "module_id": mod_id, "state": action}
        if not found:
            raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
        return {"status": "ok"}

    @suite_router.get("/api/suite/diagnostics")
    def suite_diagnostics() -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        return {
            "status": "ok",
            "total_modules": len(FEATURE_REGISTRY),
            "mounted_count": counts["mounted"],
            "operational_count": counts["operational"],
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_used_mb": round(vm.used / (1024 * 1024), 1),
            "ram_total_mb": round(vm.total / (1024 * 1024), 1),
            "ram_percent": vm.percent,
            "pid": os.getpid(),
        }

    app.include_router(suite_router)

    # Ensure any catch-all root mounts (e.g. static dashboard mounted at "" or "/")
    # remain at the end of app.routes so they do not shadow newly mounted API or UI routes.
    from starlette.routing import Mount
    catch_alls = [r for r in app.routes if isinstance(r, Mount) and getattr(r, "path", None) in ("", "/")]
    if catch_alls:
        non_catch_alls = [r for r in app.routes if not (isinstance(r, Mount) and getattr(r, "path", None) in ("", "/"))]
        app.routes[:] = non_catch_alls + catch_alls

    return {
        "total_registered": len(feature_statuses),
        "mounted_count": counts["mounted"],
        "operational_count": counts["operational"],
        "features": feature_statuses,
    }
