"""Typed request and response schemas (Pydantic v1 & v2 compatible)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Serialize a Pydantic model cleanly across Pydantic v1 and v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


class HealthResponse(BaseModel):
    status: str = "ok"
    feature: str = "AI Coding Assistant"
    version: str = "1.0.0"
    provider: str
    workspace_root: str
    writes_enabled: bool
    history_records: int


class WorkspaceFileEntry(BaseModel):
    path: str
    size_bytes: int
    language: str


class WorkspaceFileListResponse(BaseModel):
    workspace_root: str
    total_files: int
    files: List[WorkspaceFileEntry]


class WorkspaceFileContentResponse(BaseModel):
    path: str
    language: str
    size_bytes: int
    line_count: int
    content: str


class GenerateCodeRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=8000)
    language: str = Field(default="python", max_length=40)
    context_files: List[str] = Field(default_factory=list)
    include_docstrings: bool = True
    include_type_hints: bool = True
    target_hardware: str = Field(default="Raspberry Pi 5 (8GB)", max_length=80)


class GenerateCodeResponse(BaseModel):
    session_id: int
    provider_used: str
    language: str
    code: str
    explanation: str
    manual_prompt_fallback: Optional[str] = None
    static_warnings_count: int = 0


class RefactorRequest(BaseModel):
    code: Optional[str] = None
    file_path: Optional[str] = None
    language: str = Field(default="python", max_length=40)
    goal: str = Field(
        default="Improve readability, safety, typing, and maintainability",
        min_length=3,
        max_length=2000,
    )


class RefactorResponse(BaseModel):
    session_id: int
    provider_used: str
    language: str
    file_path: Optional[str] = None
    original_code: str
    refactored_code: str
    unified_diff: str
    changes_summary: List[str]
    manual_prompt_fallback: Optional[str] = None


class StaticFinding(BaseModel):
    rule_id: str
    category: str  # "security" | "quality" | "syntax"
    severity: str  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO"
    line: int
    column: int = 0
    message: str
    snippet: str = ""
    remediation: str = ""


class FunctionMetric(BaseModel):
    name: str
    line: int
    length_lines: int
    cyclomatic_complexity: int
    is_async: bool = False


class AnalyzeRequest(BaseModel):
    code: Optional[str] = None
    file_path: Optional[str] = None
    language: str = Field(default="python", max_length=40)


class AnalyzeResponse(BaseModel):
    session_id: int
    file_path: Optional[str] = None
    language: str
    score: int  # 0..100
    grade: str  # A..F
    line_count: int
    summary: Dict[str, int]
    findings: List[StaticFinding]
    metrics: List[FunctionMetric]


class TestSynthesisRequest(BaseModel):
    code: Optional[str] = None
    file_path: Optional[str] = None
    module_import_path: Optional[str] = None
    framework: str = Field(default="pytest", max_length=20)
    include_edge_cases: bool = True


class TestSynthesisResponse(BaseModel):
    session_id: int
    provider_used: str
    framework: str
    file_path: Optional[str] = None
    discovered_symbols: List[str]
    test_code: str
    notes: List[str]
    manual_prompt_fallback: Optional[str] = None


class ApplyPatchRequest(BaseModel):
    file_path: str = Field(..., min_length=1, max_length=500)
    new_content: str
    dry_run: bool = True
    create_backup: bool = True


class ApplyPatchResponse(BaseModel):
    file_path: str
    dry_run: bool
    applied: bool
    created_new_file: bool
    backup_path: Optional[str] = None
    unified_diff: str
    bytes_written: int


class HistoryRecord(BaseModel):
    id: int
    created_at: str
    action: str
    provider: str
    file_path: Optional[str] = None
    summary: str
    score: Optional[int] = None


class HistoryResponse(BaseModel):
    total: int
    records: List[HistoryRecord]
