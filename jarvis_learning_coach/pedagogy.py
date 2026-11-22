"""Socratic pedagogy engine, mastery tiering, and adaptive exercise synthesis/grading."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

CONCEPT_RUBRICS: Dict[str, List[str]] = {
    "sqlite": ["wal", "transaction", "foreign", "index", "concurrency", "lock"],
    "fastapi": ["async", "router", "pydantic", "validation", "dependency", "endpoint"],
    "recursion": ["base", "case", "stack", "termination", "subproblem"],
    "backpropagation": ["gradient", "chain", "loss", "weights", "derivative"],
    "ros2": ["node", "topic", "publisher", "subscriber", "qos", "service"],
    "transformer": ["attention", "query", "key", "value", "positional", "softmax"],
}


def tier_for_mastery(score: float) -> str:
    if score >= 75.0:
        return "advanced"
    if score >= 45.0:
        return "intermediate"
    return "foundational"


def extract_rubric_keywords(subject: str, concept: str) -> List[str]:
    combined = f"{subject} {concept}".lower()
    for key, kws in CONCEPT_RUBRICS.items():
        if key in combined:
            return list(kws)
    tokens = [w for w in re.findall(r"[a-z0-9]+", combined) if len(w) >= 4]
    base = list(dict.fromkeys(tokens))[:4]
    defaults = ["example", "mechanism", "tradeoff", "edge"]
    for d in defaults:
        if len(base) >= 5:
            break
        if d not in base:
            base.append(d)
    return base


def build_opening_socratic_prompt(subject: str, concept: str, tier: str, goal: str) -> str:
    if tier == "advanced":
        return (
            f"Welcome back to {subject} ({concept}). Since you already have strong mastery here, "
            f"let's stress-test it: what edge case or failure mode breaks naive implementations of {concept}, "
            f"and how would you redesign around it? (Goal: {goal})"
        )
    if tier == "intermediate":
        return (
            f"Let's sharpen your understanding of {concept} in {subject}. "
            f"In your own words, what core problem does {concept} solve, and what key mechanism makes it work?"
        )
    return (
        f"Let's explore {concept} in {subject} step by step. "
        f"Before I explain anything, what intuition or everyday analogy comes to mind when you hear '{concept}'?"
    )


def evaluate_socratic_turn(
    learner_message: str,
    subject: str,
    concept: str,
    current_mastery: float,
    request_hint: bool,
    prev_hint_level: int,
) -> Tuple[str, float, str, int]:
    """Return (coach_reply, mastery_delta, understanding_signal, new_hint_level)."""
    msg = learner_message.strip()
    lower = msg.lower()
    rubric = extract_rubric_keywords(subject, concept)
    matched = [kw for kw in rubric if kw in lower]
    word_count = len(re.findall(r"[a-z0-9]+", lower))

    unsure_markers = ("don't know", "dont know", "not sure", "stuck", "confused", "no idea", "hint")
    is_unsure = request_hint or any(m in lower for m in unsure_markers)

    if is_unsure:
        hint_level = min(3, prev_hint_level + 1)
        hint_kw = rubric[min(hint_level - 1, len(rubric) - 1)]
        if hint_level == 1:
            reply = (
                f"No problem — let's break {concept} down. Start by thinking about '{hint_kw}': "
                f"how does '{hint_kw}' influence what happens inside {concept}?"
            )
        elif hint_level == 2:
            reply = (
                f"Here is a stronger clue for {concept}: connect '{rubric[0]}' and '{hint_kw}'. "
                f"If you change one of those, what observable effect would you expect?"
            )
        else:
            reply = (
                f"Let's anchor the core idea: in {subject}, {concept} relies closely on "
                f"{', '.join(rubric[:3])}. Now try explaining in 1-2 sentences how they fit together."
            )
        return reply, -1.5, "needs_scaffold", hint_level

    coverage = len(matched) / max(len(rubric), 1)
    if coverage >= 0.45 and word_count >= 10:
        missing = [k for k in rubric if k not in matched]
        next_probe = missing[0] if missing else "a real-world tradeoff"
        reply = (
            f"Strong reasoning — you nailed {', '.join(matched[:3])}. "
            f"To push your mastery further on {concept}, how does '{next_probe}' interact with what you just described?"
        )
        return reply, 9.5, "strong_comprehension", 0

    if coverage >= 0.2 or word_count >= 8:
        missing = [k for k in rubric if k not in matched]
        nudge = missing[0] if missing else rubric[0]
        reply = (
            f"You're on the right track. You touched on a useful angle, though we haven't examined '{nudge}' yet. "
            f"How would you incorporate '{nudge}' into your explanation of {concept}?"
        )
        return reply, 4.5, "developing_comprehension", max(0, prev_hint_level)

    reply = (
        f"Can you expand on that a bit? Try connecting {concept} to at least one concrete mechanism "
        f"(for example, think about '{rubric[0]}' or '{rubric[min(1, len(rubric)-1)]}')."
    )
    return reply, 1.0, "brief_response", prev_hint_level


def generate_adaptive_exercise(subject: str, concept: str, tier: str) -> Dict[str, object]:
    rubric = extract_rubric_keywords(subject, concept)
    if tier == "advanced":
        prompt = (
            f"[Advanced | {subject}] Design a production-grade approach using {concept}. "
            f"Address key architectural mechanisms ({', '.join(rubric[:3])}), potential bottlenecks, and edge cases."
        )
        hint = f"Make sure your answer explicitly connects {rubric[0]}, {rubric[1]}, and failure handling."
    elif tier == "intermediate":
        prompt = (
            f"[Intermediate | {subject}] Explain how {concept} works under the hood and walk through a concrete example "
            f"showing how it handles '{rubric[0]}' and '{rubric[min(1, len(rubric)-1)]}'."
        )
        hint = f"Think through the step-by-step flow involving {', '.join(rubric[:3])}."
    else:
        prompt = (
            f"[Foundational | {subject}] In 3-5 sentences, explain what {concept} is, why it matters in {subject}, "
            f"and give one simple example."
        )
        hint = f"Include core ideas such as {', '.join(rubric[:2])} in your own words."

    solution = (
        f"A complete answer for {concept} in {subject} explains its purpose and connects key concepts: "
        f"{', '.join(rubric)}."
    )
    return {
        "prompt": prompt,
        "hint": hint,
        "expected_keywords": rubric,
        "model_solution": solution,
    }


def grade_exercise_submission(
    answer: str,
    expected_keywords: List[str],
) -> Tuple[float, bool, List[str], List[str], str]:
    lower = answer.lower()
    words = re.findall(r"[a-z0-9]+", lower)
    covered = [kw for kw in expected_keywords if kw.lower() in lower]
    missing = [kw for kw in expected_keywords if kw.lower() not in lower]

    kw_ratio = len(covered) / max(len(expected_keywords), 1)
    depth_bonus = min(20.0, len(words) * 0.8)
    score = round(min(100.0, kw_ratio * 80.0 + depth_bonus), 1)
    passed = score >= 60.0

    if passed:
        feedback = (
            f"Solid work ({score}/100). You clearly covered {', '.join(covered) or 'the core idea'}."
            + (f" To reach 100%, also address: {', '.join(missing[:3])}." if missing else " Complete conceptual coverage!")
        )
    else:
        feedback = (
            f"Needs another pass ({score}/100). Revisit these missing concepts: {', '.join(missing[:4])}. "
            f"Try writing a concrete step-by-step example."
        )
    return score, passed, covered, missing, feedback
