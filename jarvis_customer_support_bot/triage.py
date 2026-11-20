"""Deterministic sentiment classification, ticket triage, and escalation routing."""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

from .models import TriageResult

POSITIVE_WORDS: Set[str] = {
    "thanks", "thank", "great", "awesome", "love", "helpful", "resolved", "works", "excellent", "appreciate",
}
NEGATIVE_WORDS: Set[str] = {
    "broken", "failed", "error", "bug", "crash", "slow", "refund", "cancel", "angry",
    "frustrated", "unacceptable", "terrible", "worst", "charged", "double", "missing", "down",
}
URGENT_TRIGGERS: Set[str] = {
    "urgent", "emergency", "outage", "breach", "hacked", "unauthorized", "fraud",
    "chargeback", "lawsuit", "legal", "immediately", "asap", "production down",
}

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "security_abuse": ["breach", "hacked", "unauthorized", "fraud", "phishing", "compromised", "2fa"],
    "billing": ["invoice", "refund", "billing", "charged", "payment", "subscription", "credit card", "chargeback"],
    "account_access": ["login", "password", "locked", "reset", "account", "sign in", "sso"],
    "technical": ["error", "bug", "crash", "api", "timeout", "500", "broken", "outage", "install", "raspberry"],
    "shipping_order": ["order", "delivery", "shipping", "tracking", "package", "damaged", "arrived"],
}

TEAM_ROUTING: Dict[str, str] = {
    "security_abuse": "security-oncall",
    "billing": "billing-specialists",
    "account_access": "identity-support",
    "technical": "tier2-engineering",
    "shipping_order": "fulfillment-ops",
    "general": "support-general",
}


def classify_and_triage(subject: str, message: str, kb_confidence: float) -> TriageResult:
    full = f"{subject} {message}".lower()
    tokens = re.findall(r"[a-z0-9]+", full)

    pos_hits = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg_hits = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    urgent_hits = sum(1 for phrase in URGENT_TRIGGERS if phrase in full)
    exclamations = message.count("!")

    raw_score = (pos_hits * 0.25) - (neg_hits * 0.25) - (urgent_hits * 0.35) - (0.15 if exclamations >= 3 else 0.0)
    score = round(max(-1.0, min(1.0, raw_score)), 2)

    if urgent_hits >= 1 or score <= -0.65:
        sentiment = "URGENT_FRUSTRATED"
    elif score <= -0.2:
        sentiment = "NEGATIVE"
    elif score >= 0.25:
        sentiment = "POSITIVE"
    else:
        sentiment = "NEUTRAL"

    # Category classification
    best_cat = "general"
    best_hits = 0
    for cat, kws in CATEGORY_KEYWORDS.items():
        hits = sum(1 for kw in kws if kw in full)
        if hits > best_hits:
            best_hits = hits
            best_cat = cat

    # Priority & escalation logic
    if best_cat == "security_abuse" or urgent_hits >= 1:
        priority = "P1_CRITICAL"
    elif sentiment == "NEGATIVE" and best_cat in ("billing", "technical"):
        priority = "P2_HIGH"
    elif best_cat != "general":
        priority = "P3_NORMAL"
    else:
        priority = "P4_LOW"

    escalate = False
    reasons: List[str] = []
    if priority in ("P1_CRITICAL", "P2_HIGH"):
        escalate = True
        reasons.append(f"Priority classified as {priority}")
    if sentiment == "URGENT_FRUSTRATED":
        escalate = True
        reasons.append("Customer sentiment indicates urgent frustration")
    if kb_confidence < 0.25 and best_cat != "general":
        escalate = True
        reasons.append("Low domain knowledge-base match confidence")

    team = TEAM_ROUTING.get(best_cat, "support-general") if escalate else "ai-tier1-support"
    reason_str = "; ".join(reasons) if reasons else "Handled by Tier-1 AI support."

    return TriageResult(
        category=best_cat,
        priority=priority,
        sentiment=sentiment,
        sentiment_score=score,
        escalate=escalate,
        escalation_team=team,
        escalation_reason=reason_str,
    )
