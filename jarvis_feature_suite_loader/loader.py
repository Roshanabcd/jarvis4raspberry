"""Dynamic registry and safe additive mounter for all 17 JARVIS OS feature modules."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import HTMLResponse

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"

FEATURE_REGISTRY: List[Dict[str, str]] = [
    {
        "id": "ai_coding_assistant",
        "package": "jarvis_ai_coding_assistant",
        "name": "AI Coding Assistant",
        "category": "Developer Tools",
        "tier": "HEAVY",
        "ui_path": "/coding-assistant",
        "health_path": "/api/coding-assistant/health",
        "description": "Code generation, refactoring, static security analysis, and test synthesis.",
    },
    {
        "id": "ai_content_pipeline",
        "package": "jarvis_ai_content_pipeline",
        "name": "AI Content Creation Pipeline",
        "category": "Media & Content",
        "tier": "MEDIUM",
        "ui_path": "/content-pipeline",
        "health_path": "/api/content-pipeline/health",
        "description": "Technical blogs, short-video scripts, hooks, captions, and carousel outlines.",
    },
    {
        "id": "ai_interview_bot",
        "package": "jarvis_ai_interview_bot",
        "name": "AI Interview Bot",
        "category": "Education & Learning",
        "tier": "MEDIUM",
        "ui_path": "/interview-bot",
        "health_path": "/api/interview-bot/health",
        "description": "Technical and behavioral interview simulation with scoring and feedback.",
    },
    {
        "id": "ai_social_automation",
        "package": "jarvis_ai_social_automation",
        "name": "AI Social Media Automation",
        "category": "Business & Support",
        "tier": "MEDIUM",
        "ui_path": "/social-automation",
        "health_path": "/api/social-automation/health",
        "description": "Multi-platform content planning, copy generation, scheduling, and analytics.",
    },
    {
        "id": "ai_study_planner",
        "package": "jarvis_ai_study_planner",
        "name": "AI Study Planner",
        "category": "Education & Learning",
        "tier": "LIGHTWEIGHT",
        "ui_path": "/study-planner",
        "health_path": "/api/study-planner/health",
        "description": "Personalized study schedules, goal breakdown, and spaced-repetition tracking.",
    },
    {
        "id": "autonomous_trading_bot",
        "package": "jarvis_autonomous_trading_bot",
        "name": "Autonomous Trading Bot",
        "category": "Experimental",
        "tier": "HEAVY",
        "ui_path": "/trading-bot",
        "health_path": "/api/trading-bot/health",
        "description": "Safety-locked paper trading, technical indicators, backtesting, and E-STOP.",
    },
    {
        "id": "web_scraping_agent",
        "package": "jarvis_web_scraping_agent",
        "name": "Autonomous Web Scraping Agent",
        "category": "Research & Knowledge",
        "tier": "MEDIUM",
        "ui_path": "/web-scraper",
        "health_path": "/api/web-scraper/health",
        "description": "Policy-compliant HTML extraction, SSRF guards, change monitoring, and JSON export.",
    },
    {
        "id": "customer_support_bot",
        "package": "jarvis_customer_support_bot",
        "name": "ChatGPT-Powered Customer Support Bot",
        "category": "Business & Support",
        "tier": "MEDIUM",
        "ui_path": "/support-bot",
        "health_path": "/api/support-bot/health",
        "description": "Domain KB answering, ticket triage, sentiment classification, and escalation.",
    },
    {
        "id": "recommendation_engine",
        "package": "jarvis_recommendation_engine",
        "name": "Deep Learning Recommendation Engine",
        "category": "Business & Support",
        "tier": "HEAVY",
        "ui_path": "/recommendations",
        "health_path": "/api/recommendations/health",
        "description": "Hybrid 128-D semantic embeddings, collaborative filtering, and SGD latent factors.",
    },
    {
        "id": "document_qa",
        "package": "jarvis_document_qa",
        "name": "Document Question Answering",
        "category": "Research & Knowledge",
        "tier": "MEDIUM",
        "ui_path": "/doc-qa",
        "health_path": "/api/doc-qa/health",
        "description": "Upload, index, search, and perform cited QA over PDF, Markdown, and text docs.",
    },
    {
        "id": "ai_search_engine",
        "package": "jarvis_ai_search_engine",
        "name": "End-to-End AI Search Engine",
        "category": "Research & Knowledge",
        "tier": "HEAVY",
        "ui_path": "/ai-search",
        "health_path": "/api/ai-search/health",
        "description": "Unified semantic + BM25 RRF search over docs, logs, codebases, and web notes.",
    },
    {
        "id": "fraud_detection",
        "package": "jarvis_fraud_detection",
        "name": "Fraud Detection System",
        "category": "Security & Analytics",
        "tier": "HEAVY",
        "ui_path": "/fraud-detection",
        "health_path": "/api/fraud-detection/health",
        "description": "Anomaly detection across transactions, authentication logs, and audit entries.",
    },
    {
        "id": "learning_coach",
        "package": "jarvis_learning_coach",
        "name": "Personalized Learning AI Coach",
        "category": "Education & Learning",
        "tier": "MEDIUM",
        "ui_path": "/learning-coach",
        "health_path": "/api/learning-coach/health",
        "description": "Socratic tutoring, concept mastery diagnostics, and adaptive exercises.",
    },
    {
        "id": "speech_translation",
        "package": "jarvis_speech_translation",
        "name": "Real-Time Speech Translation",
        "category": "Education & Learning",
        "tier": "HEAVY",
        "ui_path": "/speech-translation",
        "health_path": "/api/speech-translation/health",
        "description": "Continuous bilingual speech recognition, WebSocket translation, and voice playback.",
    },
    {
        "id": "resume_matching",
        "package": "jarvis_resume_matching",
        "name": "Smart Resume Matching",
        "category": "Business & Support",
        "tier": "MEDIUM",
        "ui_path": "/resume-matching",
        "health_path": "/api/resume-matching/health",
        "description": "Automated skill extraction, qualification scoring, and semantic gap analysis.",
    },
    {
        "id": "handwriting_ocr",
        "package": "jarvis_handwriting_ocr",
        "name": "Handwritten to Text Converter",
        "category": "Research & Knowledge",
        "tier": "MEDIUM",
        "ui_path": "/handwriting-ocr",
        "health_path": "/api/handwriting-ocr/health",
        "description": "Upload handwritten photos or draw on a live canvas to extract clean digital text.",
    },
    {
        "id": "object_detection",
        "package": "jarvis_object_detection",
        "name": "Real-Time Object Detection",
        "category": "Computer Vision",
        "tier": "HEAVY",
        "ui_path": "/object-detection",
        "health_path": "/api/object-detection/health",
        "description": "Real-time YOLO/offline object detection, centroid tracking, ROI zones, and WebSocket HUD.",
    },
]


def mount_jarvis_feature_suite(
    app: FastAPI,
    enabled_packages: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Safely discover and mount every installed JARVIS feature module onto a FastAPI app."""
    allow_set = set(enabled_packages) if enabled_packages is not None else None
    feature_statuses: List[Dict[str, Any]] = []
    mounted_count = 0

    for spec in FEATURE_REGISTRY:
        pkg = spec["package"]
        entry = dict(spec)
        if allow_set is not None and pkg not in allow_set:
            entry["status"] = "disabled"
            entry["error"] = None
            feature_statuses.append(entry)
            continue

        try:
            mod = importlib.import_module(pkg)
            create_fn = getattr(mod, "create_router")
            app.include_router(create_fn())
            entry["status"] = "available"
            entry["error"] = None
            mounted_count += 1
        except ModuleNotFoundError:
            entry["status"] = "not_installed"
            entry["error"] = f"Package '{pkg}' not found in PYTHONPATH."
        except Exception as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)

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
            "mounted_count": mounted_count,
            "features": feature_statuses,
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
        "mounted_count": mounted_count,
        "features": feature_statuses,
    }
