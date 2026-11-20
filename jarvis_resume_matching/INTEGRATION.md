# Integrating Smart Resume Matching into JARVIS OS

This package is **strictly additive** — it does not modify or overwrite any existing JARVIS OS files.

## 1. Copy the Package
Copy `jarvis_resume_matching/` into your JARVIS OS repository (e.g. `~/.gemini/antigravity/scratch/jarvis-os/jarvis_resume_matching/`).

## 2. Mount the Router in Your JARVIS FastAPI App
```python
from jarvis_resume_matching import ResumeMatchingConfig, create_router

app.include_router(create_router(ResumeMatchingConfig()))
```

## 3. Environment Variables (Optional)
- `JARVIS_RESUME_DB_PATH`: SQLite WAL database path (default: `.jarvis_resume_matching/resume_matching.db`).
- `JARVIS_RESUME_EMBED_DIM`: Dense embedding dimension (default: `128`).
- `JARVIS_RESUME_PORT`: Standalone server port (default: `8025`).

## 4. Endpoints Added
- `GET /resume-matching` — Interactive JARVIS OS Resume Matching dashboard
- `GET /api/resume-matching/health` — Engine status and counts
- `POST /api/resume-matching/jobs` & `GET /api/resume-matching/jobs` — Create and list job descriptions
- `POST /api/resume-matching/match` — Score a resume against a saved job or inline job description
- `GET /api/resume-matching/jobs/{job_id}/leaderboard` — Ranked candidate shortlist for a job

## 5. Dashboard Card Update
Once mounted, update the **Smart Resume Matching** card in your JARVIS OS dashboard from `PLANNED` to `AVAILABLE` and point its **Open** button to `/resume-matching`.
