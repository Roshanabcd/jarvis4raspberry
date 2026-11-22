"""End-to-end tests for JARVIS Document Question Answering."""

from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_document_qa.app import create_app
from jarvis_document_qa.config import DocumentQAConfig


def _build_minimal_pdf(text: str) -> bytes:
    """Create a tiny valid single-page PDF containing a literal Tj text operator."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    parts = [
        b"%PDF-1.4\n",
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n",
        f"4 0 obj << /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream\nendobj\n",
        b"%%EOF\n",
    ]
    return b"".join(parts)


class TestDocumentQA(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test_docqa.db"
        cfg = DocumentQAConfig(db_path=db_path)
        self.client = TestClient(create_app(config=cfg))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_health_and_ui(self) -> None:
        ui = self.client.get("/doc-qa")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Document Question Answering", ui.text)

        health = self.client.get("/api/doc-qa/health")
        self.assertEqual(health.status_code, 200)
        body = health.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["total_documents"], 0)

    def test_markdown_ingest_search_ask_and_delete(self) -> None:
        md_doc = (
            "# Power & Cooling\n\n"
            "JARVIS OS runs on a Raspberry Pi 5 with 8GB RAM and an active PWM cooler. "
            "Thermal throttling begins only if CPU temperature exceeds 80 degrees Celsius.\n\n"
            "# Storage Architecture\n\n"
            "All JARVIS modules store state in SQLite using WAL journal mode and foreign key constraints."
        )
        ingest = self.client.post(
            "/api/doc-qa/documents",
            json={
                "title": "JARVIS Hardware Guide",
                "filename": "hardware_guide.md",
                "content_text": md_doc,
                "tags": ["raspberry-pi", "sqlite"],
            },
        )
        self.assertEqual(ingest.status_code, 200)
        doc_rec = ingest.json()
        self.assertEqual(doc_rec["doc_type"], "markdown")
        self.assertGreaterEqual(doc_rec["chunk_count"], 2)

        # Semantic + lexical search
        search = self.client.post(
            "/api/doc-qa/search",
            json={"query": "SQLite WAL journal mode", "top_k": 2},
        )
        self.assertEqual(search.status_code, 200)
        s_data = search.json()
        self.assertGreaterEqual(s_data["total_matches"], 1)
        self.assertEqual(s_data["results"][0]["section"], "Storage Architecture")

        # Grounded QA
        ask = self.client.post(
            "/api/doc-qa/ask",
            json={"question": "At what temperature does Raspberry Pi 5 thermal throttling begin?", "top_k": 2},
        )
        self.assertEqual(ask.status_code, 200)
        a_data = ask.json()
        self.assertEqual(a_data["mode"], "local_extractive_qa")
        self.assertIn("80 degrees Celsius", a_data["answer"])
        self.assertGreaterEqual(len(a_data["citations"]), 1)

        # Delete document cascades cleanly
        delete_resp = self.client.delete(f"/api/doc-qa/documents/{doc_rec['doc_id']}")
        self.assertEqual(delete_resp.status_code, 200)
        self.assertEqual(self.client.get("/api/doc-qa/health").json()["total_chunks"], 0)

    def test_pdf_base64_ingestion_and_qa(self) -> None:
        pdf_bytes = _build_minimal_pdf("JARVIS Voice Assistant uses a 3 second silence detection engine.")
        b64_payload = base64.b64encode(pdf_bytes).decode("ascii")
        resp = self.client.post(
            "/api/doc-qa/documents",
            json={
                "title": "Voice Engine Spec",
                "filename": "voice_spec.pdf",
                "content_base64": b64_payload,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["doc_type"], "pdf")

        ask = self.client.post(
            "/api/doc-qa/ask",
            json={"question": "How long is the silence detection engine in JARVIS Voice Assistant?"},
        )
        self.assertEqual(ask.status_code, 200)
        self.assertIn("3 second silence detection", ask.json()["answer"])


if __name__ == "__main__":
    unittest.main()
