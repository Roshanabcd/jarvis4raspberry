"""End-to-end tests for JARVIS Real-Time Speech Translation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_speech_translation.app import create_app
from jarvis_speech_translation.config import SpeechTranslationConfig


class TestSpeechTranslation(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_translate.db"
        cfg = SpeechTranslationConfig(db_path=db_path)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/speech-translation")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Real-Time Speech Translation", ui.text)

        health = self.client.get("/api/speech-translation/health")
        self.assertEqual(health.status_code, 200)
        self.assertIn("ne", health.json()["supported_languages"])

    def test_rest_translation_auto_detect_and_glossary(self) -> None:
        # Add custom glossary override
        g = self.client.post(
            "/api/speech-translation/glossary",
            json={"source_lang": "en", "target_lang": "ne", "source_term": "JARVIS", "target_term": "जार्विस"},
        )
        self.assertEqual(g.status_code, 200)

        # English -> Nepali with phrasebook + glossary
        t1 = self.client.post(
            "/api/speech-translation/translate",
            json={"text": "Hello JARVIS", "source_lang": "auto", "target_lang": "ne"},
        )
        self.assertEqual(t1.status_code, 200)
        d1 = t1.json()
        self.assertEqual(d1["source_lang"], "en")
        self.assertEqual(d1["tts_bcp47"], "ne-NP")
        self.assertIn("नमस्ते", d1["translated_text"])
        self.assertIn("जार्विस", d1["translated_text"])

        # Nepali -> English auto-detection
        t2 = self.client.post(
            "/api/speech-translation/translate",
            json={"text": "तपाईंलाई कस्तो छ", "source_lang": "auto", "target_lang": "en"},
        )
        self.assertEqual(t2.status_code, 200)
        self.assertEqual(t2.json()["source_lang"], "ne")
        self.assertEqual(t2.json()["translated_text"], "How are you")

    def test_websocket_streaming_and_session_transcript(self) -> None:
        sess = self.client.post(
            "/api/speech-translation/sessions",
            json={"title": "Pi5 Bilingual Test", "lang_a": "en", "lang_b": "es"},
        )
        self.assertEqual(sess.status_code, 200)
        sid = sess.json()["session_id"]

        with self.client.websocket_connect(f"/api/speech-translation/ws/{sid}") as ws:
            hello_evt = ws.receive_json()
            self.assertEqual(hello_evt["event"], "connected")

            ws.send_json({"text": "Good morning", "source_lang": "en", "target_lang": "es"})
            reply = ws.receive_json()
            self.assertEqual(reply["translated_text"], "Buenos días")
            self.assertEqual(reply["tts_bcp47"], "es-ES")
            self.assertIsNotNone(reply["utterance_id"])

        detail = self.client.get(f"/api/speech-translation/sessions/{sid}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.json()["utterances"]), 1)


if __name__ == "__main__":
    unittest.main()
