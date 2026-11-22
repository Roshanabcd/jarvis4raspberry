"""Core Personalized Learning AI Coach service orchestrating tutoring, diagnostics, and exercises."""

from __future__ import annotations

import json
import urllib.request
import uuid
from typing import List, Optional

from .config import LearningCoachConfig
from .models import (
    CoachTurn,
    ConceptMasteryRecord,
    ExerciseEvaluationResponse,
    ExerciseRecord,
    GenerateExerciseRequest,
    HealthResponse,
    LearnerReplyRequest,
    LearnerReplyResponse,
    MasteryDiagnosticResponse,
    SessionResponse,
    StartSessionRequest,
    SubmitExerciseRequest,
)
from .pedagogy import (
    build_opening_socratic_prompt,
    evaluate_socratic_turn,
    generate_adaptive_exercise,
    grade_exercise_submission,
    tier_for_mastery,
)
from .storage import LearningCoachStore


class LearningCoachEngine:
    """Adaptive Socratic tutor, concept mastery tracker, and exercise coach."""

    def __init__(self, config: Optional[LearningCoachConfig] = None) -> None:
        self.config = config or LearningCoachConfig()
        self.store = LearningCoachStore(self.config.db_path)

    def health(self) -> HealthResponse:
        c = self.store.counts()
        return HealthResponse(
            total_sessions=c["total_sessions"],
            total_exercises=c["total_exercises"],
            tracked_concepts=c["tracked_concepts"],
        )

    def start_session(self, req: StartSessionRequest) -> SessionResponse:
        learner = req.learner_id.strip()
        subject = req.subject.strip()
        concept = req.concept.strip()
        mastery = self.store.get_or_init_mastery(learner, subject, concept)
        opening = build_opening_socratic_prompt(
            subject=subject,
            concept=concept,
            tier=mastery["difficulty_tier"],
            goal=req.goal.strip(),
        )
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        sess = self.store.create_session(
            session_id=session_id,
            learner_id=learner,
            subject=subject,
            concept=concept,
            goal=req.goal.strip(),
            opening_prompt=opening,
        )
        return SessionResponse(
            session_id=sess["session_id"],
            learner_id=sess["learner_id"],
            subject=sess["subject"],
            concept=sess["concept"],
            difficulty_tier=mastery["difficulty_tier"],
            mastery_score=mastery["mastery_score"],
            turns=[CoachTurn(**t) for t in sess["turns"]],
        )

    def _socratic_openrouter(self, subject: str, concept: str, turns: List[dict], learner_msg: str) -> Optional[str]:
        if not self.config.openrouter_api_key:
            return None
        history_txt = "\n".join(f"{t['role'].upper()}: {t['message']}" for t in turns[-6:])
        prompt = (
            f"You are a Socratic AI tutor teaching {concept} in {subject}. "
            "Guide the learner with 1-2 concise probing questions or a small hint without dumping the full answer.\n\n"
            f"Conversation:\n{history_txt}\nLEARNER: {learner_msg}\nCOACH:"
        )
        payload = json.dumps(
            {
                "model": self.config.openrouter_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return str(data["choices"][0]["message"]["content"]).strip()
        except Exception:
            return None

    def respond_in_session(self, session_id: str, req: LearnerReplyRequest) -> LearnerReplyResponse:
        sess = self.store.get_session(session_id.strip())
        if sess is None:
            raise KeyError(f"Coaching session '{session_id}' not found.")

        mastery = self.store.get_or_init_mastery(sess["learner_id"], sess["subject"], sess["concept"])
        prev_hint = sess["turns"][-1]["hint_level"] if sess["turns"] else 0

        local_reply, delta, signal, hint_level = evaluate_socratic_turn(
            learner_message=req.message,
            subject=sess["subject"],
            concept=sess["concept"],
            current_mastery=float(mastery["mastery_score"]),
            request_hint=req.request_hint,
            prev_hint_level=int(prev_hint),
        )

        mode = "local_socratic_coach"
        reply = local_reply
        if req.use_llm and self.config.openrouter_api_key:
            llm_reply = self._socratic_openrouter(sess["subject"], sess["concept"], sess["turns"], req.message)
            if llm_reply:
                reply = llm_reply
                mode = "openrouter_socratic_coach"

        new_score = max(0.0, min(100.0, float(mastery["mastery_score"]) + delta))
        new_tier = tier_for_mastery(new_score)
        new_streak = int(mastery["streak"]) + 1 if delta > 0 else 0
        self.store.update_mastery(
            learner_id=sess["learner_id"],
            subject=sess["subject"],
            concept=sess["concept"],
            new_score=new_score,
            tier=new_tier,
            attempts=int(mastery["attempts"]) + 1,
            streak=new_streak,
        )

        self.store.append_turn(session_id=sess["session_id"], role="learner", message=req.message.strip(), hint_level=0)
        self.store.append_turn(session_id=sess["session_id"], role="coach", message=reply, hint_level=hint_level)

        return LearnerReplyResponse(
            session_id=sess["session_id"],
            coach_reply=reply,
            mode=mode,
            hint_level=hint_level,
            mastery_score=round(new_score, 2),
            mastery_delta=round(delta, 2),
            difficulty_tier=new_tier,
            understanding_signal=signal,
        )

    def mastery_diagnostics(self, learner_id: str) -> MasteryDiagnosticResponse:
        rows = self.store.list_mastery(learner_id.strip())
        records = [ConceptMasteryRecord(**r) for r in rows]
        if not records:
            return MasteryDiagnosticResponse(
                learner_id=learner_id.strip(),
                overall_mastery=0.0,
                strengths=[],
                focus_gaps=[],
                recommended_next_concept=None,
                concepts=[],
            )
        overall = round(sum(r.mastery_score for r in records) / len(records), 2)
        strengths = [f"{r.subject}: {r.concept} ({r.mastery_score}%)" for r in records if r.mastery_score >= 70.0]
        gaps = [f"{r.subject}: {r.concept} ({r.mastery_score}%)" for r in records if r.mastery_score < 60.0]
        lowest = min(records, key=lambda r: r.mastery_score)
        return MasteryDiagnosticResponse(
            learner_id=learner_id.strip(),
            overall_mastery=overall,
            strengths=strengths,
            focus_gaps=gaps,
            recommended_next_concept=f"{lowest.subject} -> {lowest.concept} ({lowest.difficulty_tier})",
            concepts=records,
        )

    def generate_exercise(self, req: GenerateExerciseRequest) -> ExerciseRecord:
        learner = req.learner_id.strip()
        subject = req.subject.strip()
        concept = req.concept.strip()
        mastery = self.store.get_or_init_mastery(learner, subject, concept)
        gen = generate_adaptive_exercise(subject=subject, concept=concept, tier=mastery["difficulty_tier"])
        ex_id = f"ex_{uuid.uuid4().hex[:12]}"
        saved = self.store.save_exercise(
            {
                "exercise_id": ex_id,
                "learner_id": learner,
                "subject": subject,
                "concept": concept,
                "difficulty_tier": mastery["difficulty_tier"],
                "prompt": gen["prompt"],
                "hint": gen["hint"],
                "expected_keywords": gen["expected_keywords"],
                "model_solution": gen["model_solution"],
            }
        )
        return ExerciseRecord(
            exercise_id=saved["exercise_id"],
            learner_id=saved["learner_id"],
            subject=saved["subject"],
            concept=saved["concept"],
            difficulty_tier=saved["difficulty_tier"],
            prompt=saved["prompt"],
            hint=saved["hint"],
            expected_keywords=saved["expected_keywords"],
            created_at=saved["created_at"],
        )

    def submit_exercise(self, exercise_id: str, req: SubmitExerciseRequest) -> ExerciseEvaluationResponse:
        ex = self.store.get_exercise(exercise_id.strip())
        if ex is None:
            raise KeyError(f"Exercise '{exercise_id}' not found.")

        score, passed, covered, missing, feedback = grade_exercise_submission(
            answer=req.answer,
            expected_keywords=ex["expected_keywords"],
        )
        mastery = self.store.get_or_init_mastery(ex["learner_id"], ex["subject"], ex["concept"])
        # Exponential moving update blending current mastery with exercise performance
        updated_m = round(max(0.0, min(100.0, 0.65 * float(mastery["mastery_score"]) + 0.35 * score)), 2)
        new_tier = tier_for_mastery(updated_m)
        new_streak = int(mastery["streak"]) + 1 if passed else 0
        self.store.update_mastery(
            learner_id=ex["learner_id"],
            subject=ex["subject"],
            concept=ex["concept"],
            new_score=updated_m,
            tier=new_tier,
            attempts=int(mastery["attempts"]) + 1,
            streak=new_streak,
        )

        return ExerciseEvaluationResponse(
            exercise_id=ex["exercise_id"],
            score=score,
            passed=passed,
            covered_concepts=covered,
            missing_concepts=missing,
            feedback=feedback,
            updated_mastery=updated_m,
            difficulty_tier=new_tier,
        )
