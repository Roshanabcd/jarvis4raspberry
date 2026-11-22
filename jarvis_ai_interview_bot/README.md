# JARVIS OS — Feature #3: AI Interview Bot

Strictly additive, Raspberry Pi 5-friendly Education & Learning module for **JARVIS OS**:
- **Technical, Behavioral (STAR), and Mixed Interview Tracks** (Python/Backend, AI/ML, Robotics/Embedded, Full-Stack)
- **Dynamic Adaptive Questioning** (scales difficulty up/down based on live answer scores via OpenRouter `openrouter/free`, Local Ollama, or curated local question bank)
- **4-Axis Rubric Scoring** (Accuracy & Depth, Structure & Clarity, Problem-Solving, Completeness) with per-turn strengths, improvements, and coaching tips
- **Structured Final Feedback Reports** with readiness verdict and downloadable `.md` export
- **SQLite (WAL Mode) Session History** + **JARVIS OS Dark Cyber Web UI** at `/interview-bot`

## Quick Start (Standalone on Raspberry Pi 5)

```bash
cd ~/.gemini/antigravity/scratch/jarvis-os
unzip /path/to/jarvis_ai_interview_bot.zip -d features/
cd features

export OPENROUTER_API_KEY="your-openrouter-key"
uvicorn jarvis_ai_interview_bot.app:app --host 127.0.0.1 --port 8013
```

Open `http://127.0.0.1:8013/interview-bot`.

## Run Tests

```bash
python3 -m unittest discover -s jarvis_ai_interview_bot/tests -v
# or with pytest:
pytest jarvis_ai_interview_bot/tests -v
```
