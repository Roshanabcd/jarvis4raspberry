"""Pydantic schemas for JARVIS Module 18 (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def model_to_dict(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj.dict()


class AgentStatus(str, Enum):
    ONLINE = "online"
    BUSY = "busy"
    PAUSED = "paused"
    OFFLINE = "offline"


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    PAUSED = "paused"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentRegisterRequest(BaseModel):
    agent_id: Optional[str] = Field(default=None, description="Optional custom agent ID")
    name: str = Field(..., min_length=2, max_length=80)
    role: str = Field(..., min_length=2, max_length=80)
    capabilities: List[str] = Field(default_factory=list)
    max_concurrency: int = Field(default=2, ge=1, le=16)
    handler_type: str = Field(default="research", description="Reference handler key or custom adapter")
    simulated: bool = Field(default=True, description="True if running in local simulation mode")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdateRequest(BaseModel):
    status: Optional[AgentStatus] = None
    max_concurrency: Optional[int] = Field(default=None, ge=1, le=16)
    capabilities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentRecord(BaseModel):
    agent_id: str
    name: str
    role: str
    capabilities: List[str] = Field(default_factory=list)
    status: AgentStatus = AgentStatus.ONLINE
    max_concurrency: int = 2
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    handler_type: str = "research"
    simulated: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    registered_at: str
    last_heartbeat: str


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=140)
    description: str = Field(default="", max_length=2000)
    workflow_id: str = Field(default="default-workflow", min_length=1, max_length=80)
    required_capability: Optional[str] = Field(default=None, max_length=80)
    assigned_agent_id: Optional[str] = Field(default=None, max_length=80)
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    depends_on: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=2, ge=0, le=10)
    retry_backoff_sec: float = Field(default=0.25, ge=0.01, le=60.0)
    timeout_sec: float = Field(default=15.0, ge=0.1, le=600.0)
    requires_approval: bool = Field(default=False)
    approval_prompt: Optional[str] = Field(default=None, max_length=500)


class TaskRecord(BaseModel):
    task_id: str
    workflow_id: str
    title: str
    description: str
    required_capability: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    depends_on: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries_attempted: int = 0
    max_retries: int = 2
    retry_backoff_sec: float = 0.25
    timeout_sec: float = 15.0
    requires_approval: bool = False
    approval_status: Optional[ApprovalStatus] = None
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    decided_by: str = Field(default="operator", min_length=1, max_length=80)
    comment: str = Field(default="", max_length=500)


class ApprovalRecord(BaseModel):
    approval_id: str
    task_id: str
    workflow_id: str
    prompt: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: Optional[str] = None
    comment: Optional[str] = None
    created_at: str
    decided_at: Optional[str] = None


class AgentMessageCreateRequest(BaseModel):
    sender_agent_id: str = Field(..., min_length=1, max_length=80)
    recipient_agent_id: str = Field(default="broadcast", min_length=1, max_length=80)
    task_id: Optional[str] = Field(default=None, max_length=80)
    workflow_id: Optional[str] = Field(default=None, max_length=80)
    channel: str = Field(default="coordination", max_length=60)
    content: str = Field(..., min_length=1, max_length=4000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMessageRecord(BaseModel):
    message_id: str
    sender_agent_id: str
    recipient_agent_id: str
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    channel: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ExecutionLogRecord(BaseModel):
    log_id: int
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    level: str
    event_type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ResourceLimitsRequest(BaseModel):
    max_concurrency: int = Field(..., ge=1, le=32)


class EngineStatusResponse(BaseModel):
    engine_state: str
    paused: bool
    simulation_mode: bool
    max_concurrency: int
    active_workers: int
    agent_count: int
    task_counts: Dict[str, int]
    pending_approvals: int
    total_messages: int
    uptime_seconds: float


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
