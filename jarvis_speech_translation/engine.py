"""Core Real-Time Speech Translation service managing bilingual sessions, translation, and glossaries."""

from __future__ import annotations

import time
import uuid
from typing import Optional

from .config import SpeechTranslationConfig
from .models import (
    CreateSessionRequest,
    GlossaryEntryRecord,
    GlossaryEntryRequest,
    GlossaryListResponse,
    HealthResponse,
    SUPPORTED_LANGUAGES,
    SessionDetailResponse,
    TranslateRequest,
    TranslateResponse,
    UtteranceRecord,
)
from .storage import SpeechTranslationStore
from .translator import BCP47_MAP, local_tts_available, translate_text


class SpeechTranslationEngine:
    """Orchestrates continuous bilingual translation, glossaries, and transcript storage."""

    def __init__(self, config: Optional[SpeechTranslationConfig] = None) -> None:
        self.config = config or SpeechTranslationConfig()
        self.store = SpeechTranslationStore(self.config.db_path)

    def health(self) -> HealthResponse:
        c = self.store.counts()
        return HealthResponse(
            supported_languages=SUPPORTED_LANGUAGES,
            local_tts_available=local_tts_available(),
            total_sessions=c["total_sessions"],
            total_utterances=c["total_utterances"],
        )

    def create_session(self, req: CreateSessionRequest) -> SessionDetailResponse:
        la = req.lang_a.strip().lower()
        lb = req.lang_b.strip().lower()
        if la not in SUPPORTED_LANGUAGES or lb not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language pair ({la}, {lb}). Supported: {sorted(SUPPORTED_LANGUAGES)}")
        sid = f"st_{uuid.uuid4().hex[:12]}"
        saved = self.store.create_session(session_id=sid, title=req.title.strip(), lang_a=la, lang_b=lb)
        return SessionDetailResponse(**saved)

    def get_session(self, session_id: str) -> SessionDetailResponse:
        sess = self.store.get_session(session_id.strip())
        if sess is None:
            raise KeyError(f"Translation session '{session_id}' not found.")
        sess["utterances"] = [UtteranceRecord(**u) for u in sess["utterances"]]
        return SessionDetailResponse(**sess)

    def translate(self, req: TranslateRequest) -> TranslateResponse:
        t0 = time.perf_counter()
        src = req.source_lang.strip().lower()
        tgt = req.target_lang.strip().lower()
        if tgt not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language '{tgt}'. Supported: {sorted(SUPPORTED_LANGUAGES)}")

        glossary = self.store.list_glossary(source_lang=None if src == "auto" else src, target_lang=tgt)
        resolved_src, translated, provider = translate_text(
            text=req.text,
            source_lang=src,
            target_lang=tgt,
            glossary=glossary,
            config=self.config,
            use_llm=req.use_llm,
        )
        # Apply pair-specific glossary if source was auto-detected
        if src == "auto":
            pair_glossary = self.store.list_glossary(source_lang=resolved_src, target_lang=tgt)
            if pair_glossary:
                from .translator import apply_glossary

                translated = apply_glossary(translated, pair_glossary)

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        utterance_id: Optional[int] = None
        if req.session_id:
            sess = self.store.get_session(req.session_id.strip())
            if sess is None:
                raise KeyError(f"Translation session '{req.session_id}' not found.")
            utterance_id = self.store.append_utterance(
                session_id=sess["session_id"],
                speaker=req.speaker.strip() or "speaker_a",
                source_lang=resolved_src,
                target_lang=tgt,
                source_text=req.text.strip(),
                translated_text=translated,
                provider=provider,
                latency_ms=latency_ms,
            )

        return TranslateResponse(
            source_lang=resolved_src,
            target_lang=tgt,
            source_text=req.text.strip(),
            translated_text=translated,
            provider=provider,
            latency_ms=latency_ms,
            tts_bcp47=BCP47_MAP.get(tgt, "en-US"),
            utterance_id=utterance_id,
        )

    def upsert_glossary(self, req: GlossaryEntryRequest) -> GlossaryEntryRecord:
        saved = self.store.upsert_glossary(
            source_lang=req.source_lang.strip().lower(),
            target_lang=req.target_lang.strip().lower(),
            source_term=req.source_term.strip(),
            target_term=req.target_term.strip(),
        )
        return GlossaryEntryRecord(**saved)

    def list_glossary(self) -> GlossaryListResponse:
        rows = [GlossaryEntryRecord(**r) for r in self.store.list_glossary()]
        return GlossaryListResponse(total=len(rows), entries=rows)
