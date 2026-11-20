"""Core Document Question Answering engine (ingestion, hybrid search, extractive + optional LLM QA)."""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from .chunker import chunk_document
from .config import DocumentQAConfig
from .models import (
    AskRequest,
    AskResponse,
    Citation,
    DeleteDocumentResponse,
    DocumentIngestRequest,
    DocumentListResponse,
    DocumentRecord,
    HealthResponse,
    RetrievedChunk,
    SearchRequest,
    SearchResponse,
)
from .parser import extract_document_text
from .retriever import compute_embedding, cosine_similarity, rank_chunks, tokenize
from .storage import DocumentStore


class DocumentQAEngine:
    """Manages document ingestion, chunk embeddings, hybrid search, and grounded QA."""

    def __init__(self, config: Optional[DocumentQAConfig] = None) -> None:
        self.config = config or DocumentQAConfig()
        self.store = DocumentStore(self.config.db_path)

    def health(self) -> HealthResponse:
        counts = self.store.counts()
        return HealthResponse(
            embedding_dim=self.config.embedding_dim,
            total_documents=counts["total_documents"],
            total_chunks=counts["total_chunks"],
        )

    def ingest_document(self, req: DocumentIngestRequest) -> DocumentRecord:
        doc_type, text = extract_document_text(
            filename=req.filename,
            content_text=req.content_text,
            content_base64=req.content_base64,
        )
        raw_chunks = chunk_document(
            text=text,
            doc_type=doc_type,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        if not raw_chunks:
            raise ValueError("Document produced zero indexable chunks.")

        title = (req.title or Path(req.filename).stem or "Untitled Document").strip()
        tags = [t.strip() for t in req.tags if t.strip()]
        doc_id = hashlib.sha256(f"{req.filename}:{title}:{text[:256]}".encode("utf-8")).hexdigest()[:16]

        embedded_chunks: List[Dict[str, object]] = []
        for ch in raw_chunks:
            embed_input = f"{title} {ch['section']} {ch['content']}"
            embedded_chunks.append(
                {
                    "chunk_index": ch["chunk_index"],
                    "section": ch["section"],
                    "content": ch["content"],
                    "embedding": compute_embedding(embed_input, dim=self.config.embedding_dim),
                }
            )

        saved = self.store.save_document_with_chunks(
            doc_id=doc_id,
            title=title,
            filename=req.filename.strip(),
            doc_type=doc_type,
            char_count=len(text),
            tags=tags,
            chunks=embedded_chunks,
        )
        return DocumentRecord(**saved)

    def list_documents(self) -> DocumentListResponse:
        docs = [DocumentRecord(**d) for d in self.store.list_documents()]
        return DocumentListResponse(total=len(docs), documents=docs)

    def delete_document(self, doc_id: str) -> DeleteDocumentResponse:
        deleted = self.store.delete_document(doc_id.strip())
        if not deleted:
            raise KeyError(f"Document '{doc_id}' not found.")
        return DeleteDocumentResponse(deleted=True, doc_id=doc_id.strip())

    def search(self, req: SearchRequest) -> SearchResponse:
        chunks = self.store.list_chunks(doc_id=req.doc_id)
        ranked = rank_chunks(
            query=req.query,
            chunks=chunks,
            dim=self.config.embedding_dim,
            weight_semantic=self.config.weight_semantic,
            weight_lexical=self.config.weight_lexical,
            top_k=req.top_k,
        )
        return SearchResponse(
            query=req.query,
            total_matches=len(ranked),
            results=[RetrievedChunk(**r) for r in ranked],
        )

    def _synthesize_extractive(self, question: str, matches: List[Dict[str, object]]) -> str:
        """Select the highest-scoring grounded sentences across retrieved chunks."""
        q_tokens = set(tokenize(question))
        q_vec = compute_embedding(question, dim=self.config.embedding_dim)
        scored_sentences: List[tuple[float, str, str, int]] = []

        for m in matches:
            text = str(m["content"])
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) >= 15]
            if not sentences:
                sentences = [text.strip()]
            for sent in sentences:
                s_tokens = set(tokenize(sent))
                overlap = (len(q_tokens & s_tokens) / max(len(q_tokens), 1)) if q_tokens else 0.0
                sem = max(0.0, cosine_similarity(q_vec, compute_embedding(sent, dim=self.config.embedding_dim)))
                s_score = 0.55 * overlap + 0.35 * sem + 0.10 * float(m["score"])
                scored_sentences.append((s_score, sent, str(m["doc_title"]), int(m["chunk_index"])))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        chosen: List[str] = []
        seen_norm = set()
        for _, sent, title, idx in scored_sentences:
            norm = sent.lower()
            if norm in seen_norm:
                continue
            seen_norm.add(norm)
            chosen.append(f"{sent} [{title} #{idx}]")
            if len(chosen) >= 3:
                break
        return " ".join(chosen)

    def _synthesize_openrouter(self, question: str, matches: List[Dict[str, object]]) -> Optional[str]:
        if not self.config.openrouter_api_key:
            return None
        context_blocks = [
            f"[{m['doc_title']} #{m['chunk_index']} | {m['section']}]\n{m['content']}"
            for m in matches
        ]
        prompt = (
            "Answer the user's question using ONLY the provided document excerpts. "
            "Cite sources inline as [Title #chunk_index]. If the excerpts do not contain the answer, say so.\n\n"
            f"Excerpts:\n" + "\n\n".join(context_blocks) + f"\n\nQuestion: {question}"
        )
        payload = json.dumps(
            {
                "model": self.config.openrouter_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return str(data["choices"][0]["message"]["content"]).strip()
        except Exception:
            return None

    def ask(self, req: AskRequest) -> AskResponse:
        chunks = self.store.list_chunks(doc_id=req.doc_id)
        if not chunks:
            return AskResponse(
                question=req.question,
                answer="No indexed documents found. Upload or ingest a PDF, Markdown, or text document first.",
                mode="empty_index",
                confidence=0.0,
                citations=[],
            )

        matches = rank_chunks(
            query=req.question,
            chunks=chunks,
            dim=self.config.embedding_dim,
            weight_semantic=self.config.weight_semantic,
            weight_lexical=self.config.weight_lexical,
            top_k=req.top_k,
        )
        top_score = float(matches[0]["score"]) if matches else 0.0
        if not matches or top_score < 0.08:
            return AskResponse(
                question=req.question,
                answer="No sufficiently relevant passages were found in the indexed documents to answer this question.",
                mode="no_relevant_context",
                confidence=round(top_score, 4),
                citations=[],
            )

        mode = "local_extractive_qa"
        answer: Optional[str] = None
        if req.use_llm and self.config.openrouter_api_key:
            answer = self._synthesize_openrouter(req.question, matches)
            if answer:
                mode = "openrouter_rag_qa"
        if not answer:
            answer = self._synthesize_extractive(req.question, matches)

        citations = [
            Citation(
                doc_id=str(m["doc_id"]),
                doc_title=str(m["doc_title"]),
                chunk_index=int(m["chunk_index"]),
                section=str(m["section"]),
                score=float(m["score"]),
                excerpt=str(m["content"])[:260],
            )
            for m in matches
        ]
        return AskResponse(
            question=req.question,
            answer=answer,
            mode=mode,
            confidence=round(min(1.0, top_score), 4),
            citations=citations,
        )
