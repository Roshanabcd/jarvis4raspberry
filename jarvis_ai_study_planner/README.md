# JARVIS OS — Feature #5: AI Study Planner

Strictly additive, lightweight Education & Learning module for **JARVIS OS** on Raspberry Pi 5:
- **Learning Goal Breakdown & Syllabus Milestones** (via OpenRouter `openrouter/free`, Local Ollama, or deterministic offline planner)
- **Personalized Daily Study Schedule** (balanced across deep study, applied practice, and every-4th-day spaced review)
- **SM-2 Spaced-Repetition Flashcard Engine** (auto-seeded from milestones + custom cards, with quality 0–5 recall grading and ease-factor interval scheduling)
- **SQLite (WAL Mode) Persistence** + **Markdown Export** + **JARVIS OS Dark Cyber Web UI** at `/study-planner`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_ai_study_planner.zip -d features/
cd features

export OPENROUTER_API_KEY="your-openrouter-key"
uvicorn jarvis_ai_study_planner.app:app --host 127.0.0.1 --port 8015
```

Open `http://127.0.0.1:8015/study-planner`.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_ai_study_planner/tests -v
# or with pytest:
pytest jarvis_ai_study_planner/tests -v
```
