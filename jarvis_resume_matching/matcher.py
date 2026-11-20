"""128-D semantic resume-JD similarity, qualification scoring, and gap analysis."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Dict, List

from .config import ResumeMatchingConfig
from .extractor import extract_education, extract_skills, extract_years_experience, normalize_skill

STOPWORDS = {"the", "and", "for", "with", "that", "this", "from", "your", "into", "about", "our"}


def _embed(text: str, dim: int = 128) -> List[float]:
    vec = [0.0] * dim
    tokens = [w for w in re.findall(r"[a-z0-9+#.]+", text.lower()) if len(w) >= 2 and w not in STOPWORDS]
    for tok in tokens:
        feats = [(f"w:{tok}", 1.5)]
        if len(tok) >= 4:
            for i in range(len(tok) - 2):
                feats.append((f"c:{tok[i:i+3]}", 0.5))
        for feat, w in feats:
            digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
            i1 = int.from_bytes(digest[:4], "little") % dim
            i2 = int.from_bytes(digest[4:8], "little") % dim
            s1 = 1.0 if (digest[0] & 1) == 0 else -1.0
            s2 = 1.0 if (digest[4] & 1) == 0 else -1.0
            vec[i1] += s1 * w
            vec[i2] += s2 * (w * 0.5)
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 1e-12 else [0.0] * dim


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def evaluate_candidate_match(
    resume_text: str,
    job_description: str,
    required_skills: List[str],
    preferred_skills: List[str],
    min_years_experience: float,
    config: ResumeMatchingConfig,
) -> Dict[str, object]:
    norm_req = sorted({normalize_skill(s) for s in required_skills if s.strip()})
    if not norm_req:
        norm_req = extract_skills(job_description)
    norm_pref = sorted({normalize_skill(s) for s in preferred_skills if s.strip()} - set(norm_req))

    cand_skills = extract_skills(resume_text, extra_candidates=norm_req + norm_pref)
    cand_set = set(cand_skills)

    matched_req = [s for s in norm_req if s in cand_set]
    missing_req = [s for s in norm_req if s not in cand_set]
    matched_pref = [s for s in norm_pref if s in cand_set]
    missing_pref = [s for s in norm_pref if s not in cand_set]

    req_ratio = (len(matched_req) / len(norm_req)) if norm_req else 1.0
    pref_ratio = (len(matched_pref) / len(norm_pref)) if norm_pref else 1.0

    sem_sim = _cosine(
        _embed(resume_text, dim=config.embedding_dim),
        _embed(job_description, dim=config.embedding_dim),
    )

    cand_years = extract_years_experience(resume_text)
    if min_years_experience <= 0:
        exp_ratio = 1.0
    else:
        exp_ratio = min(1.0, cand_years / min_years_experience)

    overall = (
        config.weight_required_skills * req_ratio
        + config.weight_preferred_skills * pref_ratio
        + config.weight_semantic * sem_sim
        + config.weight_experience * exp_ratio
    ) * 100.0
    overall = round(max(0.0, min(100.0, overall)), 2)

    if overall >= 80.0 and len(missing_req) <= 1:
        tier = "strong_match"
    elif overall >= 65.0:
        tier = "good_match"
    elif overall >= 45.0:
        tier = "partial_match"
    else:
        tier = "weak_match"

    gaps: List[str] = []
    if missing_req:
        gaps.append(
            f"Close required skill gaps: {', '.join(missing_req[:6])} (highlight concrete projects or hands-on deliverables)."
        )
    if missing_pref:
        gaps.append(f"Strengthen preferred qualifications: {', '.join(missing_pref[:4])}.")
    if min_years_experience > 0 and cand_years < min_years_experience:
        gaps.append(
            f"Experience delta: resume states {cand_years:g} yrs vs. {min_years_experience:g} yrs requested; emphasize measurable production impact."
        )
    if sem_sim < 0.35:
        gaps.append(
            "Low semantic alignment with the job description; tailor project bullets to mirror domain terminology and outcomes."
        )
    if not gaps:
        gaps.append("Strong end-to-end alignment across required skills, experience, and semantic domain context.")

    return {
        "overall_score": overall,
        "required_skill_score": round(req_ratio * 100.0, 2),
        "preferred_skill_score": round(pref_ratio * 100.0, 2),
        "semantic_similarity": round(sem_sim * 100.0, 2),
        "experience_score": round(exp_ratio * 100.0, 2),
        "recommendation_tier": tier,
        "extracted_candidate_skills": cand_skills,
        "candidate_years_experience": cand_years,
        "candidate_education": extract_education(resume_text),
        "matched_required_skills": matched_req,
        "missing_required_skills": missing_req,
        "matched_preferred_skills": matched_pref,
        "missing_preferred_skills": missing_pref,
        "gap_recommendations": gaps,
    }
