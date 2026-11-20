"""FastAPI APIRouter for strictly additive integration of AI Study Planner into JARVIS OS."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import StudyPlannerConfig
from .engine import StudyPlannerEngine
from .llm_provider import StudyLLMClient
from .models import (
    CreateFlashcardRequest,
    CreateStudyPlanRequest,
    FlashcardListResponse,
    FlashcardRecord,
    HealthResponse,
    MilestoneItem,
    PlanListResponse,
    PlanSummary,
    ReviewFlashcardRequest,
    StudyBlock,
    StudyPlanDetail,
    StudyProgressResponse,
    UpdateMilestoneRequest,
)
from .storage import StudyPlannerStore

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def create_router(
    config: Optional[StudyPlannerConfig] = None,
    prefix: str = "/api/study-planner",
    ui_route: str = "/study-planner",
) -> APIRouter:
    """Create a self-contained FastAPI router for JARVIS OS."""
    cfg = config or StudyPlannerConfig()
    store = StudyPlannerStore(cfg.db_path)
    llm = StudyLLMClient(cfg)
    engine = StudyPlannerEngine(cfg, store, llm)

    router = APIRouter(tags=["AI Study Planner"])

    @router.get(ui_route, response_class=HTMLResponse, include_in_schema=False)
    async def serve_ui() -> HTMLResponse:
        if not STATIC_INDEX.exists():
            raise HTTPException(status_code=404, detail="UI bundle not found.")
        return HTMLResponse(content=STATIC_INDEX.read_text(encoding="utf-8"))

    @router.get(f"{prefix}/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        counts = store.progress_counts()
        return HealthResponse(
            status="ok",
            provider=cfg.active_provider_label(),
            total_plans=counts["total_plans"],
            due_reviews=counts["due_cards_today"],
        )

    @router.post(f"{prefix}/plans", response_model=StudyPlanDetail)
    async def create_plan(req: CreateStudyPlanRequest) -> StudyPlanDetail:
        return await engine.create_plan(req)

    @router.get(f"{prefix}/plans", response_model=PlanListResponse)
    async def list_plans(limit: int = Query(default=50, ge=1, le=200)) -> PlanListResponse:
        rows = store.list_plans(limit=limit)
        return PlanListResponse(total=len(rows), plans=[PlanSummary(**r) for r in rows])

    @router.get(f"{prefix}/plans/{{plan_id}}", response_model=StudyPlanDetail)
    async def get_plan(plan_id: int) -> StudyPlanDetail:
        data = store.get_plan(plan_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Study plan {plan_id} not found.")
        return StudyPlanDetail(
            **{
                **data,
                "milestones": [MilestoneItem(**m) for m in data["milestones"]],
                "schedule": [StudyBlock(**s) for s in data["schedule"]],
            }
        )

    @router.get(f"{prefix}/plans/{{plan_id}}/export", response_class=PlainTextResponse)
    async def export_plan(plan_id: int) -> PlainTextResponse:
        data = store.get_plan(plan_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Study plan {plan_id} not found.")
        return PlainTextResponse(
            content=str(data["plan_markdown"]),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="jarvis_study_plan_{plan_id}.md"'},
        )

    @router.patch(f"{prefix}/milestones/{{milestone_id}}", response_model=MilestoneItem)
    async def update_milestone(milestone_id: int, req: UpdateMilestoneRequest) -> MilestoneItem:
        updated = store.update_milestone_status(milestone_id, req.status)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found.")
        return MilestoneItem(**updated)

    @router.post(f"{prefix}/flashcards", response_model=FlashcardRecord)
    async def create_flashcard(req: CreateFlashcardRequest) -> FlashcardRecord:
        return engine.create_flashcard(req)

    @router.get(f"{prefix}/flashcards", response_model=FlashcardListResponse)
    async def list_flashcards(due_only: bool = Query(default=False)) -> FlashcardListResponse:
        rows = store.list_flashcards(due_only=due_only)
        return FlashcardListResponse(total=len(rows), cards=[FlashcardRecord(**r) for r in rows])

    @router.post(f"{prefix}/flashcards/{{card_id}}/review", response_model=FlashcardRecord)
    async def review_flashcard(card_id: int, req: ReviewFlashcardRequest) -> FlashcardRecord:
        try:
            return engine.review_flashcard(card_id, req)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(f"{prefix}/progress", response_model=StudyProgressResponse)
    async def progress() -> StudyProgressResponse:
        return engine.get_progress()

    return router
