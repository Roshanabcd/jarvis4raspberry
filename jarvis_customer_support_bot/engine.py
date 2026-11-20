"""Core Customer Support Bot engine: domain KB retrieval, LLM/offline replies, triage, and stats."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .config import SupportBotConfig
from .llm_provider import SupportLLMClient
from .models import (
    CustomerInquiryRequest,
    SupportReplyResponse,
    SupportStatsResponse,
)
from .storage import SupportBotStore
from .triage import classify_and_triage

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "have", "what",
    "how", "can", "are", "was", "not", "you", "our", "about", "please", "help",
}


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{3,}", text.lower()) if w not in STOPWORDS}


class SupportBotEngine:
    """Retrieves domain KB articles, triages tickets, and drafts grounded support responses."""

    def __init__(
        self,
        config: SupportBotConfig,
        store: SupportBotStore,
        llm: SupportLLMClient,
    ) -> None:
        self.config = config
        self.store = store
        self.llm = llm

    def _retrieve_kb(self, query: str, top_k: int = 3) -> Tuple[List[Dict[str, Any]], float]:
        articles = self.store.list_kb_articles()
        if not articles:
            return [], 0.0
        q_tokens = _tokenize(query)
        if not q_tokens:
            return [], 0.0

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for art in articles:
            doc_text = f"{art['title']} {art['category']} {' '.join(art['tags'])} {art['content']}"
            d_tokens = _tokenize(doc_text)
            if not d_tokens:
                continue
            overlap = len(q_tokens & d_tokens)
            if overlap == 0:
                continue
            score = overlap / max(1.0, min(len(q_tokens), 8))
            scored.append((min(1.0, score), art))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:top_k]
        if not top:
            return [], 0.0
        return [art for _, art in top], round(top[0][0], 2)

    async def handle_inquiry(self, req: CustomerInquiryRequest) -> SupportReplyResponse:
        query_text = f"{req.subject} {req.message}"
        matched_kb, confidence = self._retrieve_kb(query_text, top_k=3)
        triage = classify_and_triage(req.subject, req.message, kb_confidence=confidence)

        kb_context = "\n\n".join(
            f"### {a['title']} ({a['category']})\n{a['content']}" for a in matched_kb
        ) or "No matching internal knowledge base article found."

        system_prompt = (
            "You are a helpful, accurate, empathetic customer support assistant inside JARVIS OS. "
            "Answer strictly using the provided domain knowledge base context. Never invent refund amounts, "
            "policies, or promises not in the KB. If escalation is flagged, let the customer know their ticket "
            "has been prioritized for the specialist team."
        )
        user_prompt = (
            f"Customer: {req.customer_name}\n"
            f"Subject: {req.subject}\n"
            f"Message: {req.message}\n"
            f"Triage: category={triage.category}, priority={triage.priority}, sentiment={triage.sentiment}, escalate={triage.escalate} ({triage.escalation_team})\n\n"
            f"Domain Knowledge Base:\n{kb_context}\n"
        )

        llm_res = await self.llm.complete(system_prompt, user_prompt)
        if not llm_res.used_fallback and llm_res.text:
            reply_text = llm_res.text
        else:
            reply_text = self._offline_reply(req, matched_kb, triage.escalate, triage.escalation_team)

        status = "escalated" if triage.escalate else "open"
        ticket = self.store.create_ticket(
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            subject=req.subject,
            message=req.message,
            category=triage.category,
            priority=triage.priority,
            sentiment=triage.sentiment,
            sentiment_score=triage.sentiment_score,
            escalated=triage.escalate,
            escalation_team=triage.escalation_team,
            escalation_reason=triage.escalation_reason,
            status=status,
            reply_text=reply_text,
        )

        return SupportReplyResponse(
            ticket_id=int(ticket["id"]),
            status=status,
            provider_used=llm_res.provider_used,
            triage=triage,
            reply_text=reply_text,
            matched_kb_titles=[str(a["title"]) for a in matched_kb],
            confidence=confidence,
        )

    @staticmethod
    def _offline_reply(
        req: CustomerInquiryRequest,
        matched_kb: List[Dict[str, Any]],
        escalate: bool,
        team: str,
    ) -> str:
        greeting = f"Hi {req.customer_name},"
        if matched_kb:
            primary = matched_kb[0]
            body = (
                f"Thanks for reaching out about \"{req.subject}\". "
                f"Based on our guide **{primary['title']}**:\n\n{primary['content']}"
            )
        else:
            body = (
                f"Thanks for contacting us about \"{req.subject}\". "
                "I did not find an exact match in our automated knowledge base, so I have logged your full details for review."
            )
        if escalate:
            closing = f"\n\nBecause of the priority of your request, I have escalated your ticket directly to our **{team}** team for faster follow-up."
        else:
            closing = "\n\nPlease reply if you need anything else and we will be glad to help."
        return f"{greeting}\n\n{body}{closing}"

    def get_stats(self) -> SupportStatsResponse:
        tickets = self.store.list_tickets(limit=500)
        open_c = sum(1 for t in tickets if t["status"] == "open")
        esc_c = sum(1 for t in tickets if t["status"] == "escalated")
        res_c = sum(1 for t in tickets if t["status"] == "resolved")
        by_cat: Dict[str, int] = {}
        by_sent: Dict[str, int] = {}
        for t in tickets:
            cat = str(t["category"])
            sent = str(t["sentiment"])
            by_cat[cat] = by_cat.get(cat, 0) + 1
            by_sent[sent] = by_sent.get(sent, 0) + 1
        return SupportStatsResponse(
            total_tickets=len(tickets),
            open_tickets=open_c,
            escalated_tickets=esc_c,
            resolved_tickets=res_c,
            by_category=by_cat,
            by_sentiment=by_sent,
        )
