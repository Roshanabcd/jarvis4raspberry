"""
JARVIS Document AI - Core Data Models and Types.
"""
from __future__ import annotations

from enum import Enum
import time
from typing import Any, Dict, List, Optional
import uuid

from pydantic import AliasChoices, BaseModel, Field


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "md"
    CSV = "csv"
    UNKNOWN = "unknown"


class SummaryType(str, Enum):
    EXECUTIVE = "executive"
    KEY_TAKEAWAYS = "key_takeaways"
    COMPREHENSIVE = "comprehensive"
    STRUCTURED_OUTLINE = "structured_outline"


class DocumentMetadata(BaseModel):
    doc_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:12]}")
    filename: str
    file_type: DocumentType
    file_size_bytes: int = 0
    user_id: str = "default_user"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    page_count: Optional[int] = 1
    word_count: int = 0
    checksum: str = ""
    collection: str = "default"
    is_indexed: bool = False
    storage_path: str = ""
    title: Optional[str] = None
    author: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:12]}")
    doc_id: str
    user_id: str = "default_user"
    chunk_index: int = 0
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    text: str
    char_start: int = 0
    char_end: int = 0
    word_count: int = 0

    @property
    def citation_label(self) -> str:
        if self.page_number is not None:
            return f"Page {self.page_number}"
        if self.section_heading:
            return f"Section '{self.section_heading}'"
        return f"Passage {self.chunk_index + 1}"


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float
    match_type: str = "hybrid"  # "hybrid", "keyword", "semantic"


class Citation(BaseModel):
    doc_id: str
    filename: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    quote: str
    chunk_id: str
    relevance_score: float = 0.0

    @property
    def formatted(self) -> str:
        loc = f"Page {self.page_number}" if self.page_number else (f"Section '{self.section_heading}'" if self.section_heading else "Text")
        return f"[{self.filename}, {loc}]"


class DocumentAnswer(BaseModel):
    question: str
    answer: str
    grounded: bool = True
    confidence: float = 0.0
    citations: List[Citation] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    model: str = "local_grounded"
    latency_ms: float = 0.0
    doc_ids: List[str] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    summary_type: SummaryType
    summary_text: str
    key_topics: List[str] = Field(default_factory=list)
    grounded: bool = True
    word_count: int = 0
    latency_ms: float = 0.0


class DocumentCollection(BaseModel):
    collection_id: str = Field(default_factory=lambda: f"col_{uuid.uuid4().hex[:8]}")
    user_id: str = "default_user"
    name: str
    description: str = ""
    doc_count: int = 0
    created_at: float = Field(default_factory=time.time)


# API Request / Response Schemas
class AskDocumentRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1500, validation_alias=AliasChoices("question", "query"))
    doc_ids: Optional[List[str]] = None
    doc_id: Optional[str] = None
    document_id: Optional[str] = None
    collection: Optional[str] = None
    top_k: int = Field(5, ge=1, le=20)
    provider: Optional[str] = None


class SummarizeDocumentRequest(BaseModel):
    doc_id: str = Field(..., validation_alias=AliasChoices("doc_id", "document_id"))
    summary_type: SummaryType = SummaryType.EXECUTIVE
    provider: Optional[str] = None


class SearchDocumentRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    doc_ids: Optional[List[str]] = None
    collection: Optional[str] = None
    top_k: int = Field(10, ge=1, le=50)


class CreateCollectionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field("", max_length=500)
