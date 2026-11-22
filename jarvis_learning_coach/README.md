# JARVIS OS — Personalized Learning AI Coach

Adaptive educational coaching with **Socratic tutoring**, **concept mastery diagnostics**, and **personalized exercises** for **Raspberry Pi 5 (8GB)**.

## Features
- **Socratic Tutoring Engine (`pedagogy.py`, `engine.py`)**: Guides learners with probing questions and 3-level progressive hints instead of dumping answers, with optional OpenRouter LLM upgrades when `OPENROUTER_API_KEY` is set.
- **Concept Mastery Diagnostics (`storage.py`)**: Tracks per-learner mastery (`0–100%`), streaks, adaptive difficulty tiers (`foundational`, `intermediate`, `advanced`), strengths, and focus gaps in SQLite WAL.
- **Personalized Exercises & Auto-Grader**: Generates tier-calibrated exercises, evaluates conceptual coverage, gives targeted feedback, and updates mastery scores automatically.

## Quick Start (Standalone)
```bash
pip install -r requirements.txt
python3 -m jarvis_learning_coach.app
# Open http://localhost:8023/learning-coach
```

## Run Tests
```bash
python3 -m unittest discover -s jarvis_learning_coach/tests -v
```
