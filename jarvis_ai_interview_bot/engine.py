"""Adaptive interview simulation, rubric evaluation, and feedback report engine."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from .config import InterviewBotConfig
from .llm_provider import InterviewLLMClient
from .models import (
    AnswerEvaluation,
    InterviewQuestion,
    InterviewReportResponse,
    RubricBreakdown,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    model_to_dict,
)
from .question_bank import pick_offline_question
from .storage import InterviewBotStore

DIFFICULTY_LADDER = ["Junior", "Mid", "Senior"]


def _adapt_difficulty(current: str, last_score: int) -> str:
    idx = 1
    for i, label in enumerate(DIFFICULTY_LADDER):
        if label.lower() == current.lower():
            idx = i
            break
    if last_score >= 82 and idx < len(DIFFICULTY_LADDER) - 1:
        return DIFFICULTY_LADDER[idx + 1]
    if last_score < 55 and idx > 0:
        return DIFFICULTY_LADDER[idx - 1]
    return DIFFICULTY_LADDER[idx]


def _pick_turn_category(mode: str, turn_number: int) -> str:
    m = mode.lower()
    if m == "technical":
        return "technical"
    if m == "behavioral":
        return "behavioral"
    return "technical" if turn_number % 2 == 1 else "behavioral"


def _score_verdict(score: int) -> str:
    if score >= 85:
        return "Strong Hire"
    if score >= 72:
        return "Hire"
    if score >= 58:
        return "Borderline — Needs Polish"
    return "Needs Preparation"


def _try_parse_json(text: str) -> Optional[Dict[str, object]]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


class InterviewBotEngine:
    """Runs stateful multi-turn technical & behavioral interviews with adaptive scoring."""

    def __init__(
        self,
        config: InterviewBotConfig,
        store: InterviewBotStore,
        llm: InterviewLLMClient,
    ) -> None:
        self.config = config
        self.store = store
        self.llm = llm

    async def start_session(self, req: StartInterviewRequest) -> StartInterviewResponse:
        session_id = self.store.create_session(
            candidate_name=req.candidate_name,
            role=req.role,
            mode=req.mode,
            difficulty=req.difficulty,
            total_questions=req.total_questions,
            focus_topics=req.focus_topics,
        )

        category = _pick_turn_category(req.mode, 1)
        question, provider_used = await self._generate_question(
            role=req.role,
            category=category,
            difficulty=req.difficulty,
            turn_number=1,
            asked_questions=[],
            focus_topics=req.focus_topics,
            last_score=None,
        )

        self.store.add_question_turn(
            session_id=session_id,
            turn_number=1,
            category=question.category,
            difficulty=question.difficulty,
            question=question.question,
            expected_signals=question.expected_signals,
        )

        return StartInterviewResponse(
            session_id=session_id,
            status="in_progress",
            role=req.role,
            mode=req.mode,
            difficulty=req.difficulty,
            total_questions=req.total_questions,
            current_question=question,
            provider_used=provider_used,
        )

    async def submit_answer(
        self,
        session_id: int,
        req: SubmitAnswerRequest,
    ) -> SubmitAnswerResponse:
        session = self.store.get_session(session_id)
        if not session:
            raise KeyError(f"Interview session {session_id} not found.")
        if session["status"] == "completed":
            raise ValueError(f"Interview session {session_id} is already completed.")

        turns = self.store.get_turns(session_id)
        pending = next((t for t in turns if t["answer"] is None), None)
        if not pending:
            raise ValueError("No pending interview question found for this session.")

        evaluation, manual_fallback = await self._evaluate_answer(
            role=session["role"],
            category=pending["category"],
            difficulty=pending["difficulty"],
            turn_number=pending["turn_number"],
            question=pending["question"],
            expected_signals=pending["expected_signals"],
            answer=req.answer,
        )

        self.store.record_answer(
            session_id=session_id,
            turn_number=pending["turn_number"],
            answer=req.answer,
            evaluation=model_to_dict(evaluation),
        )

        answered_count = pending["turn_number"]
        remaining = max(0, int(session["total_questions"]) - answered_count)

        if remaining > 0:
            next_turn = answered_count + 1
            next_cat = _pick_turn_category(session["mode"], next_turn)
            next_diff = _adapt_difficulty(pending["difficulty"], evaluation.rubric.overall_score)
            asked = [t["question"] for t in turns]
            next_q, _ = await self._generate_question(
                role=session["role"],
                category=next_cat,
                difficulty=next_diff,
                turn_number=next_turn,
                asked_questions=asked,
                focus_topics=session["focus_topics"],
                last_score=evaluation.rubric.overall_score,
            )
            self.store.add_question_turn(
                session_id=session_id,
                turn_number=next_turn,
                category=next_q.category,
                difficulty=next_q.difficulty,
                question=next_q.question,
                expected_signals=next_q.expected_signals,
            )
            return SubmitAnswerResponse(
                session_id=session_id,
                status="in_progress",
                evaluation=evaluation,
                next_question=next_q,
                remaining_questions=remaining,
                manual_prompt_fallback=manual_fallback,
            )

        # Final turn answered -> compute and store final report
        report = self.build_report(session_id, finalize=True)
        return SubmitAnswerResponse(
            session_id=session_id,
            status="completed",
            evaluation=evaluation,
            next_question=None,
            remaining_questions=0,
            manual_prompt_fallback=manual_fallback,
        )

    async def _generate_question(
        self,
        role: str,
        category: str,
        difficulty: str,
        turn_number: int,
        asked_questions: List[str],
        focus_topics: List[str],
        last_score: Optional[int],
    ) -> Tuple[InterviewQuestion, str]:
        system_prompt = (
            "You are a senior interviewer inside JARVIS OS. Return ONLY a JSON object with keys: "
            '"question" (string) and "expected_signals" (list of 4-6 concise technical/behavioral keywords).'
        )
        user_prompt = (
            f"Role: {role}\n"
            f"Category: {category}\n"
            f"Target difficulty: {difficulty}\n"
            f"Turn number: {turn_number}\n"
            f"Focus topics: {', '.join(focus_topics) if focus_topics else 'General role fundamentals'}\n"
            f"Previous answer score: {last_score if last_score is not None else 'N/A'}\n"
            f"Already asked questions (do not repeat): {asked_questions}\n"
        )
        res = await self.llm.complete(system_prompt, user_prompt)
        if not res.used_fallback and res.text:
            parsed = _try_parse_json(res.text)
            if parsed and isinstance(parsed.get("question"), str):
                raw_sig = parsed.get("expected_signals")
                signals = [str(s) for s in raw_sig][:6] if isinstance(raw_sig, list) else ["clarity", "depth", "trade-off"]
                return (
                    InterviewQuestion(
                        turn_number=turn_number,
                        category=category,
                        difficulty=difficulty,
                        question=str(parsed["question"]).strip(),
                        expected_signals=signals,
                    ),
                    res.provider_used,
                )

        diff, q_text, signals = pick_offline_question(role, category, difficulty, asked_questions)
        return (
            InterviewQuestion(
                turn_number=turn_number,
                category=category,
                difficulty=diff,
                question=q_text,
                expected_signals=signals,
            ),
            res.provider_used,
        )

    async def _evaluate_answer(
        self,
        role: str,
        category: str,
        difficulty: str,
        turn_number: int,
        question: str,
        expected_signals: List[str],
        answer: str,
    ) -> Tuple[AnswerEvaluation, Optional[str]]:
        system_prompt = (
            "You are a fair, rigorous hiring interviewer. Evaluate the candidate's answer and return ONLY JSON "
            "with keys: accuracy_depth (0-100), structure_clarity (0-100), problem_solving (0-100), "
            "completeness (0-100), strengths (list of 2 strings), improvements (list of 2 strings), coaching_tip (string)."
        )
        user_prompt = (
            f"Role: {role} ({difficulty} {category})\n"
            f"Question: {question}\n"
            f"Expected signals: {expected_signals}\n"
            f"Candidate Answer:\n{answer}\n"
        )

        res = await self.llm.complete(system_prompt, user_prompt)
        if not res.used_fallback and res.text:
            parsed = _try_parse_json(res.text)
            if parsed and all(k in parsed for k in ("accuracy_depth", "structure_clarity", "problem_solving", "completeness")):
                acc = max(0, min(100, int(parsed["accuracy_depth"])))
                struc = max(0, min(100, int(parsed["structure_clarity"])))
                prob = max(0, min(100, int(parsed["problem_solving"])))
                comp = max(0, min(100, int(parsed["completeness"])))
                overall = round(acc * 0.35 + struc * 0.20 + prob * 0.25 + comp * 0.20)
                return (
                    AnswerEvaluation(
                        turn_number=turn_number,
                        question=question,
                        answer=answer,
                        rubric=RubricBreakdown(
                            accuracy_depth=acc,
                            structure_clarity=struc,
                            problem_solving=prob,
                            completeness=comp,
                            overall_score=overall,
                        ),
                        strengths=[str(x) for x in (parsed.get("strengths") or [])][:3],
                        improvements=[str(x) for x in (parsed.get("improvements") or [])][:3],
                        coaching_tip=str(parsed.get("coaching_tip") or "Provide concrete metrics and edge cases."),
                        provider_used=res.provider_used,
                    ),
                    None,
                )

        # Deterministic offline rubric scoring
        return (
            self._offline_evaluate(turn_number, category, question, expected_signals, answer, res.provider_used),
            res.manual_prompt_fallback,
        )

    @staticmethod
    def _offline_evaluate(
        turn_number: int,
        category: str,
        question: str,
        expected_signals: List[str],
        answer: str,
        provider_used: str,
    ) -> AnswerEvaluation:
        low = answer.lower()
        words = answer.split()
        word_count = len(words)

        matched_signals = [sig for sig in expected_signals if sig.lower() in low]
        signal_ratio = (len(matched_signals) / len(expected_signals)) if expected_signals else 0.5

        # Structure markers (bullet points, steps, STAR words, punctuation)
        structure_markers = sum(
            1
            for token in ("first", "second", "finally", "situation", "task", "action", "result", "because", "therefore", "trade-off", "example")
            if token in low
        )
        has_numbers_or_metrics = bool(re.search(r"\b\d+(%|ms|s|gb|mb|x)?\b", low))

        accuracy_depth = min(100, int(35 + signal_ratio * 55 + (10 if word_count >= 55 else 0)))
        structure_clarity = min(100, int(40 + min(4, structure_markers) * 12 + (12 if word_count >= 35 else 0)))
        problem_solving = min(100, int(38 + signal_ratio * 35 + (15 if has_numbers_or_metrics else 0) + (12 if "trade" in low or "edge" in low or "fallback" in low or "test" in low else 0)))
        completeness = min(100, int(30 + min(1.0, word_count / 80.0) * 40 + signal_ratio * 30))

        if word_count < 15:
            accuracy_depth = min(accuracy_depth, 45)
            completeness = min(completeness, 35)

        overall = round(accuracy_depth * 0.35 + structure_clarity * 0.20 + problem_solving * 0.25 + completeness * 0.20)

        strengths: List[str] = []
        improvements: List[str] = []

        if matched_signals:
            strengths.append(f"Covered key concepts directly: {', '.join(matched_signals[:4])}.")
        if structure_markers >= 2:
            strengths.append("Clear, logical structure with explicit transitions.")
        if has_numbers_or_metrics:
            strengths.append("Backed reasoning with concrete numbers or measurable constraints.")
        if not strengths:
            strengths.append("Attempted to address the core question directly.")

        missing = [sig for sig in expected_signals if sig not in matched_signals]
        if missing:
            improvements.append(f"Explicitly discuss missing signals such as: {', '.join(missing[:3])}.")
        if word_count < 40:
            improvements.append("Expand your answer with concrete implementation details and trade-offs (aim for 60–120 words).")
        if category == "behavioral" and not any(k in low for k in ("result", "outcome", "impact")):
            improvements.append("Close your behavioral story with the measurable Result/Impact (STAR method).")
        if not improvements:
            improvements.append("Add one concrete failure mode or scaling boundary to elevate to Senior depth.")

        tip = (
            "Strong answer — next, mention a real production edge case or metric to make it unforgettable."
            if overall >= 80
            else "Use a crisp structure (Context -> Architecture/Action -> Trade-offs -> Measurable Result)."
        )

        return AnswerEvaluation(
            turn_number=turn_number,
            question=question,
            answer=answer,
            rubric=RubricBreakdown(
                accuracy_depth=accuracy_depth,
                structure_clarity=structure_clarity,
                problem_solving=problem_solving,
                completeness=completeness,
                overall_score=overall,
            ),
            strengths=strengths,
            improvements=improvements,
            coaching_tip=tip,
            provider_used=provider_used,
        )

    def build_report(self, session_id: int, finalize: bool = False) -> InterviewReportResponse:
        session = self.store.get_session(session_id)
        if not session:
            raise KeyError(f"Interview session {session_id} not found.")
        turns = self.store.get_turns(session_id)
        evaluated_turns = [AnswerEvaluation(**t["evaluation"]) for t in turns if t["evaluation"]]

        if evaluated_turns:
            n = len(evaluated_turns)
            avg_acc = round(sum(t.rubric.accuracy_depth for t in evaluated_turns) / n)
            avg_str = round(sum(t.rubric.structure_clarity for t in evaluated_turns) / n)
            avg_prob = round(sum(t.rubric.problem_solving for t in evaluated_turns) / n)
            avg_comp = round(sum(t.rubric.completeness for t in evaluated_turns) / n)
            overall = round(sum(t.rubric.overall_score for t in evaluated_turns) / n)
        else:
            avg_acc = avg_str = avg_prob = avg_comp = overall = 0

        verdict = _score_verdict(overall) if evaluated_turns else "In Progress"
        avg_rubric = RubricBreakdown(
            accuracy_depth=avg_acc,
            structure_clarity=avg_str,
            problem_solving=avg_prob,
            completeness=avg_comp,
            overall_score=overall,
        )

        top_strengths: List[str] = []
        priority_improvements: List[str] = []
        for t in evaluated_turns:
            for s in t.strengths:
                if s not in top_strengths:
                    top_strengths.append(s)
            for imp in t.improvements:
                if imp not in priority_improvements:
                    priority_improvements.append(imp)

        md_lines = [
            f"# JARVIS OS — Interview Feedback Report (#{session_id})",
            "",
            f"- **Candidate:** {session['candidate_name']}",
            f"- **Role:** {session['role']} ({session['difficulty']} • {session['mode']})",
            f"- **Overall Score:** {overall}/100",
            f"- **Verdict:** {verdict}",
            "",
            "## Rubric Averages",
            f"- Accuracy & Depth: {avg_acc}/100",
            f"- Structure & Clarity: {avg_str}/100",
            f"- Problem-Solving & Trade-offs: {avg_prob}/100",
            f"- Completeness: {avg_comp}/100",
            "",
            "## Top Strengths",
        ] + [f"- {s}" for s in (top_strengths[:5] or ["No answered turns yet."])] + [
            "",
            "## Priority Improvements",
        ] + [f"- {i}" for i in (priority_improvements[:5] or ["Complete at least one turn."])] + [
            "",
            "## Turn-by-Turn Breakdown",
            "",
        ]

        for t in evaluated_turns:
            md_lines.extend(
                [
                    f"### Q{t.turn_number}: {t.question}",
                    f"- **Score:** {t.rubric.overall_score}/100",
                    f"- **Coaching Tip:** {t.coaching_tip}",
                    "",
                ]
            )

        report_md = "\n".join(md_lines).strip() + "\n"
        if finalize:
            self.store.complete_session(session_id, overall, report_md)
            status = "completed"
        else:
            status = session["status"]

        return InterviewReportResponse(
            session_id=session_id,
            candidate_name=session["candidate_name"],
            role=session["role"],
            mode=session["mode"],
            difficulty=session["difficulty"],
            status=status,
            overall_score=overall,
            verdict=verdict,
            average_rubric=avg_rubric,
            top_strengths=top_strengths[:5],
            priority_improvements=priority_improvements[:5],
            turns=evaluated_turns,
            report_markdown=report_md,
        )
