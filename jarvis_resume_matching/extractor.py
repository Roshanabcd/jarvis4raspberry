"""Automated skill, experience, and education extraction with alias normalization."""

from __future__ import annotations

import re
from typing import Dict, List

SKILL_TAXONOMY: List[str] = [
    "python", "javascript", "typescript", "c++", "rust", "go", "java", "sql",
    "fastapi", "django", "flask", "react", "next.js", "node.js", "html", "css",
    "sqlite", "postgresql", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "linux", "ubuntu", "git", "ci/cd", "aws", "gcp", "azure",
    "pytorch", "tensorflow", "scikit-learn", "opencv", "machine learning", "deep learning",
    "nlp", "rag", "llm", "computer vision", "data analysis", "pandas", "numpy",
    "ros2", "robotics", "raspberry pi", "embedded systems", "arduino", "mqtt", "websocket",
    "rest api", "pydantic", "asyncio", "pytest", "unit testing", "system design",
    "cybersecurity", "anomaly detection", "agile", "leadership", "communication",
]

SKILL_ALIASES: Dict[str, str] = {
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "ros 2": "ros2",
    "rpi": "raspberry pi",
    "rpi5": "raspberry pi",
    "raspberry pi 5": "raspberry pi",
    "sklearn": "scikit-learn",
    "ml": "machine learning",
    "dl": "deep learning",
    "cv": "computer vision",
    "websockets": "websocket",
    "rest apis": "rest api",
    "nodejs": "node.js",
    "nextjs": "next.js",
    "cpp": "c++",
}


def normalize_skill(skill: str) -> str:
    cleaned = " ".join(skill.strip().lower().split())
    return SKILL_ALIASES.get(cleaned, cleaned)


def extract_skills(text: str, extra_candidates: List[str] | None = None) -> List[str]:
    lower = text.lower()
    found: set[str] = set()

    # Check canonical taxonomy and aliases
    for alias, canonical in SKILL_ALIASES.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", lower):
            found.add(canonical)

    candidates = list(SKILL_TAXONOMY)
    if extra_candidates:
        candidates.extend(normalize_skill(s) for s in extra_candidates if s.strip())

    for skill in candidates:
        if not skill:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", lower):
            found.add(skill)

    return sorted(found)


def extract_years_experience(text: str) -> float:
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b", text.lower())
    if not matches:
        return 0.0
    vals = [float(m) for m in matches if float(m) <= 45.0]
    return max(vals) if vals else 0.0


def extract_education(text: str) -> str:
    lower = text.lower()
    if re.search(r"\b(ph\.?d|doctorate)\b", lower):
        return "Doctorate (PhD)"
    if re.search(r"\b(m\.?s\.?|m\.?sc|master'?s|m\.?tech|mba)\b", lower):
        return "Master's Degree"
    if re.search(r"\b(b\.?s\.?|b\.?sc|bachelor'?s|b\.?tech|b\.?e\.?|b\.?eng)\b", lower):
        return "Bachelor's Degree"
    if re.search(r"\b(associate|diploma|bootcamp)\b", lower):
        return "Associate / Diploma"
    return "Not specified"
