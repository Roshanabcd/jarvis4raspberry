"""Language detection, glossary substitution, and multi-tier translation engine."""

from __future__ import annotations

import json
import re
import shutil
import urllib.request
from typing import Dict, List, Optional, Tuple

from .config import SpeechTranslationConfig

BCP47_MAP: Dict[str, str] = {
    "en": "en-US",
    "ne": "ne-NP",
    "hi": "hi-IN",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "ja": "ja-JP",
}

OFFLINE_PHRASES: Dict[Tuple[str, str], Dict[str, str]] = {
    ("en", "ne"): {
        "hello": "नमस्ते",
        "good morning": "शुभ प्रभात",
        "thank you": "धन्यवाद",
        "how are you": "तपाईंलाई कस्तो छ",
        "welcome": "स्वागत छ",
        "emergency stop": "आपतकालीन रोक",
        "yes": "हो",
        "no": "होइन",
        "please": "कृपया",
        "system ready": "प्रणाली तयार छ",
    },
    ("ne", "en"): {
        "नमस्ते": "Hello",
        "धन्यवाद": "Thank you",
        "तपाईंलाई कस्तो छ": "How are you",
        "स्वागत छ": "Welcome",
        "प्रणाली तयार छ": "System ready",
    },
    ("en", "hi"): {
        "hello": "नमस्ते",
        "good morning": "सुप्रभात",
        "thank you": "धन्यवाद",
        "how are you": "आप कैसे हैं",
        "welcome": "स्वागत है",
        "yes": "हाँ",
        "no": "नहीं",
    },
    ("hi", "en"): {
        "नमस्ते": "Hello",
        "धन्यवाद": "Thank you",
        "आप कैसे हैं": "How are you",
    },
    ("en", "es"): {
        "hello": "Hola",
        "good morning": "Buenos días",
        "thank you": "Gracias",
        "how are you": "¿Cómo estás?",
        "welcome": "Bienvenido",
        "system ready": "Sistema listo",
    },
    ("es", "en"): {
        "hola": "Hello",
        "gracias": "Thank you",
        "buenos días": "Good morning",
    },
    ("en", "fr"): {
        "hello": "Bonjour",
        "thank you": "Merci",
        "good morning": "Bonjour",
        "welcome": "Bienvenue",
    },
    ("en", "de"): {
        "hello": "Hallo",
        "thank you": "Danke",
        "good morning": "Guten Morgen",
        "welcome": "Willkommen",
    },
}


def detect_language(text: str) -> str:
    """Fast script + marker-based language detector."""
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        # Distinguish Nepali vs Hindi via common markers
        if any(m in text for m in ("छ", "तपाईं", "हामी", "होइन", "कस्तो")):
            return "ne"
        return "hi"
    if any("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in text):
        return "ja"
    lower = text.lower()
    if any(w in lower for w in ("hola", "gracias", "buenos", "cómo")):
        return "es"
    if any(w in lower for w in ("bonjour", "merci", "bienvenue")):
        return "fr"
    if any(w in lower for w in ("hallo", "danke", "guten morgen")):
        return "de"
    return "en"


def local_tts_available() -> bool:
    return bool(shutil.which("piper") or shutil.which("espeak-ng") or shutil.which("espeak"))


def apply_glossary(text: str, glossary: List[Dict[str, str]]) -> str:
    result = text
    for entry in glossary:
        src = entry["source_term"]
        tgt = entry["target_term"]
        if src:
            result = re.sub(re.escape(src), tgt, result, flags=re.IGNORECASE)
    return result


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary: List[Dict[str, str]],
    config: SpeechTranslationConfig,
    use_llm: bool = False,
) -> Tuple[str, str, str]:
    """Return (resolved_source_lang, translated_text, provider_name)."""
    resolved_src = detect_language(text) if source_lang == "auto" else source_lang.lower()
    tgt = target_lang.lower()

    if resolved_src == tgt:
        return resolved_src, apply_glossary(text, glossary), "passthrough_same_language"

    # Tier 1: Optional OpenRouter LLM translation
    if use_llm and config.openrouter_api_key:
        gloss_hint = (
            " Use these mandatory glossary translations: "
            + ", ".join(f"{g['source_term']} -> {g['target_term']}" for g in glossary[:10])
            if glossary
            else ""
        )
        prompt = (
            f"Translate the following spoken utterance from {resolved_src} to {tgt}. "
            f"Output ONLY the translated text.{gloss_hint}\n\n{text}"
        )
        payload = json.dumps(
            {
                "model": config.openrouter_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            out = str(data["choices"][0]["message"]["content"]).strip()
            if out:
                return resolved_src, apply_glossary(out, glossary), "openrouter_llm"
        except Exception:
            pass

    # Tier 2: Optional self-hosted LibreTranslate
    if config.libretranslate_url:
        payload = json.dumps(
            {"q": text, "source": resolved_src, "target": tgt, "format": "text"}
        ).encode("utf-8")
        req = urllib.request.Request(
            config.libretranslate_url.rstrip("/") + "/translate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            out = str(data.get("translatedText", "")).strip()
            if out:
                return resolved_src, apply_glossary(out, glossary), "libretranslate"
        except Exception:
            pass

    # Tier 3: Deterministic offline phrasebook + glossary translator
    phrase_map = OFFLINE_PHRASES.get((resolved_src, tgt), {})
    cleaned = text.strip()
    lower = cleaned.lower().rstrip(".!?")
    if lower in phrase_map:
        return resolved_src, apply_glossary(phrase_map[lower], glossary), "offline_phrasebook"

    translated = cleaned
    replaced_any = False
    for src_phrase, tgt_phrase in sorted(phrase_map.items(), key=lambda kv: len(kv[0]), reverse=True):
        new_t, count = re.subn(rf"\b{re.escape(src_phrase)}\b", tgt_phrase, translated, flags=re.IGNORECASE)
        if count > 0:
            translated = new_t
            replaced_any = True

    with_glossary = apply_glossary(translated, glossary)
    if with_glossary != translated:
        replaced_any = True
    translated = with_glossary

    if not replaced_any:
        translated = f"[{tgt}] {cleaned}"

    return resolved_src, translated, "offline_phrasebook"
