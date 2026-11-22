"""Pydantic v1/v2 compatible schemas for JARVIS Document Question Answering."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "Document Question Answering"
    version: str = "1.0.0"
    embedding_dim: int
    total_documents: int
    total_chunks: int


class DocumentIngestRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    filename: str = Field(default="document.txt", min_length=1, max_length=200)
    content_text: Optional[str] = Field(default=None, max_length=500000)
    content_base64: Optional[str] = Field(default=None, max_length=2000000)
    tags: List[str] = Field(default_factory=list)


class DocumentRecord(BaseModel):
    doc_id: str
    created_at: str
    title: str
    filename: str
    doc_type: str
    char_count: int
    chunk_count: int
    tags: List[str]


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentRecord]


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    doc_id: str


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=30)
    doc_id: Optional[str] = None


class RetrievedChunk(BaseModel):
    doc_id: str
    doc_title: str
    filename: str
    chunk_index: int
    section: str
    content: str
    score: float
    semantic_score: float
    lexical_score: float


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[RetrievedChunk]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1500)
    top_k: int = Field(default=4, ge=1, le=15)
    doc_id: Optional[str] = None
    use_llm: bool = False


class Citation(BaseModel):
    doc_id: str
    doc_title: str
    chunk_index: int
    section: str
    score: float
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    mode: str
    confidence: float
    citations: List[Citation]
