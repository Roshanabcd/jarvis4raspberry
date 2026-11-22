# Integrating Personalized Learning AI Coach into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_learning_coach/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_learning_coach/`).

## 2. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_learning_coach import LearningCoachConfig, create_router

app.include_router(create_router(LearningCoachConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_COACH_DB_PATH`: SQLite WAL database path (default: `.jarvis_learning_coach/learning_coach.db`).
- `OPENROUTER_API_KEY` / `JARVIS_COACH_MODEL`: Optional OpenRouter LLM Socratic tutoring when `use_llm=true`.
- `JARVIS_COACH_PORT`: Standalone server port (default: `8023`).

## 4. Endpoints Added
- `GET /learning-coach` — Interactive JARVIS OS Learning Coach dashboard
- `GET /api/learning-coach/health` — Engine status and tracked counts
- `POST /api/learning-coach/sessions` — Start a new Socratic tutoring session
- `POST /api/learning-coach/sessions/{session_id}/respond` — Submit learner reasoning or request a progressive hint
- `GET /api/learning-coach/mastery/{learner_id}` — Concept mastery diagnostic report
- `POST /api/learning-coach/exercises/generate` — Generate a mastery-calibrated exercise
- `POST /api/learning-coach/exercises/{exercise_id}/submit` — Auto-grade submission and update mastery

## 5. Dashboard Card Update
Once mounted, update the **Personalized Learning AI Coach** card in your JARVIS OS dashboard from `PLANNED` to `AVAILABLE` and point its **Open** button to `/learning-coach`.
