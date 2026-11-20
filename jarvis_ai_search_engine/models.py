"""Pydantic v1/v2 compatible schemas for JARVIS End-to-End AI Search Engine."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

VALID_SOURCE_TYPES = {"document", "terminal_log", "codebase", "web_knowledge"}


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "End-to-End AI Search Engine"
    version: str = "1.0.0"
    embedding_dim: int
    total_sources: int
    total_chunks: int
    by_source_type: Dict[str, int]


class IndexSourceRequest(BaseModel):
    source_type: str = Field(default="document", max_length=40)
    title: str = Field(..., min_length=1, max_length=240)
    source_uri: str = Field(default="local://inline", max_length=500)
    content: str = Field(..., min_length=5, max_length=500000)
    tags: List[str] = Field(default_factory=list)


class IndexDirectoryRequest(BaseModel):
    directory: str = Field(..., min_length=1, max_length=500)
    max_files: int = Field(default=60, ge=1, le=500)
    tags: List[str] = Field(default_factory=list)


class SourceRecord(BaseModel):
    item_id: str
    created_at: str
    source_type: str
    title: str
    source_uri: str
    tags: List[str]
    chunk_count: int
    char_count: int


class SourceListResponse(BaseModel):
    total: int
    by_source_type: Dict[str, int]
    sources: List[SourceRecord]


class IndexDirectoryResponse(BaseModel):
    directory: str
    indexed_files: int
    skipped_files: int
    sources: List[SourceRecord]


class DeleteSourceResponse(BaseModel):
    deleted: bool
    item_id: str


class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    source_types: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    top_k: int = Field(default=8, ge=1, le=40)
    synthesize_answer: bool = True
    synthesize_with_llm: bool = False


class SearchHit(BaseModel):
    item_id: str
    source_type: str
    title: str
    source_uri: str
    chunk_index: int
    location: str
    snippet: str
    content: str
    rrf_score: float
    semantic_score: float
    lexical_score: float
    tags: List[str]


class SearchQueryResponse(BaseModel):
    query: str
    latency_ms: float
    total_hits: int
    synthesis_mode: str
    synthesized_answer: str
    hits: List[SearchHit]


class SearchHistoryEntry(BaseModel):
    id: int
    created_at: str
    query: str
    source_filter: str
    result_count: int
    latency_ms: float


class SearchHistoryResponse(BaseModel):
    total: int
    history: List[SearchHistoryEntry]
