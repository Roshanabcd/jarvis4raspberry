"""Curated multi-track technical and behavioral question bank for offline & hybrid interviews."""

from __future__ import annotations

from typing import Dict, List, Tuple

# Each entry: (difficulty, question_text, expected_signals)
TECHNICAL_BANK: Dict[str, List[Tuple[str, str, List[str]]]] = {
    "python": [
        (
            "Junior",
            "Explain the difference between synchronous functions and `async`/`await` in Python FastAPI services. When can an `async def` endpoint accidentally block the event loop?",
            ["event loop", "blocking", "io", "thread", "await", "concurrency"],
        ),
        (
            "Mid",
            "How would you design a SQLite-backed service on a single-board computer (like Raspberry Pi 5) to handle concurrent reads and writes reliably without database lock errors?",
            ["wal", "transaction", "timeout", "lock", "index", "foreign key"],
        ),
        (
            "Mid",
            "Walk through how you prevent path traversal, command injection, and secret leakage when building a local developer API.",
            ["resolve", "relative", "subprocess", "shell=false", "environment", "validation"],
        ),
        (
            "Senior",
            "Design a resilient multi-provider AI orchestration layer that fails over cleanly between cloud APIs, local Ollama models, and deterministic offline fallbacks under strict latency budgets.",
            ["timeout", "retry", "circuit", "fallback", "observability", "latency"],
        ),
        (
            "Senior",
            "How do you structure automated tests for an asynchronous FastAPI application with external HTTP dependencies so tests stay fast, deterministic, and isolated?",
            ["mock", "dependency", "tempfile", "testclient", "isolation", "edge case"],
        ),
    ],
    "ai": [
        (
            "Junior",
            "Explain precision, recall, and F1 score, and give a real example where optimizing for recall matters more than precision.",
            ["false negative", "false positive", "threshold", "trade-off", "imbalanced"],
        ),
        (
            "Mid",
            "How does Retrieval-Augmented Generation (RAG) reduce hallucinations, and what chunking or retrieval failures still cause wrong answers?",
            ["embedding", "chunk", "context", "rerank", "grounding", "citation"],
        ),
        (
            "Senior",
            "You need to run real-time computer vision and speech pipelines on an 8GB Raspberry Pi 5. How do you budget RAM, CPU threads, and model quantization?",
            ["quantization", "int8", "memory", "latency", "queue", "batch"],
        ),
    ],
    "robotics": [
        (
            "Junior",
            "Explain how PWM controls servo or DC motor speed, and why an emergency-stop (E-STOP) path should never rely solely on a high-level web UI.",
            ["duty cycle", "frequency", "hardware", "fail-safe", "watchdog", "interrupt"],
        ),
        (
            "Mid",
            "How do you structure a hardware abstraction layer (HAL) with simulation mode so you can test motor and sensor logic safely before running on physical hardware?",
            ["interface", "mock", "simulation", "safety", "bounds", "telemetry"],
        ),
        (
            "Senior",
            "Design a fault-tolerant communication protocol between a Raspberry Pi 5 host and an ESP32-S3 microcontroller for real-time motor telemetry and command actuation.",
            ["heartbeat", "checksum", "timeout", "reconnect", "state machine", "backpressure"],
        ),
    ],
}

BEHAVIORAL_BANK: List[Tuple[str, str, List[str]]] = [
    (
        "Junior",
        "Tell me about a tough bug you debugged recently. Use the STAR method (Situation, Task, Action, Result) to explain how you isolated the root cause.",
        ["situation", "task", "action", "result", "root cause", "learned"],
    ),
    (
        "Mid",
        "Describe a time you had to make an architectural trade-off under a tight deadline. What options did you weigh, and what would you do differently now?",
        ["trade-off", "option", "decision", "impact", "metric", "retrospective"],
    ),
    (
        "Mid",
        "Tell me about a project where requirements changed mid-way or a tool/API failed unexpectedly. How did you adapt without breaking existing work?",
        ["pivot", "fallback", "communication", "risk", "result", "testing"],
    ),
    (
        "Senior",
        "Share an example of when you proactively identified a reliability, security, or performance risk before it became an outage, and how you drove the fix.",
        ["risk", "proactive", "ownership", "metric", "prevention", "result"],
    ),
    (
        "Senior",
        "Describe a time you mentored someone or resolved a technical disagreement on design standards. How did you reach alignment?",
        ["alignment", "evidence", "listen", "compromise", "outcome", "team"],
    ),
]


def select_track(role: str) -> str:
    low = role.lower()
    if any(k in low for k in ("robot", "embedded", "hardware", "esp32", "iot")):
        return "robotics"
    if any(k in low for k in ("ai", "ml", "machine learning", "data", "nlp", "vision")):
        return "ai"
    return "python"


def pick_offline_question(
    role: str,
    category: str,
    difficulty: str,
    asked_questions: List[str],
) -> Tuple[str, str, List[str]]:
    """Select an unasked question matching category and closest difficulty."""
    pool = BEHAVIORAL_BANK if category == "behavioral" else TECHNICAL_BANK[select_track(role)]
    asked_set = set(asked_questions)

    # Prefer exact difficulty match first
    for diff, q, signals in pool:
        if diff.lower() == difficulty.lower() and q not in asked_set:
            return diff, q, signals

    # Otherwise any unasked question in pool
    for diff, q, signals in pool:
        if q not in asked_set:
            return diff, q, signals

    # Fallback across all technical tracks if pool exhausted
    for track_pool in TECHNICAL_BANK.values():
        for diff, q, signals in track_pool:
            if q not in asked_set:
                return diff, q, signals

    return (
        difficulty,
        f"Walk through the most challenging {category} system you have built for a {role} role and explain your key design decisions.",
        ["architecture", "trade-off", "testing", "result", "performance"],
    )
