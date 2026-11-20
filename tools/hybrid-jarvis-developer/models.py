from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

class TaskState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"
    REVIEWING = "reviewing"
    READY_FOR_MERGE = "ready_for_merge"
    MERGED = "merged"

@dataclass(frozen=True)
class Capability:
    name: str
    description: str

@dataclass
class Agent:
    agent_id: str
    capabilities: Tuple[Capability, ...]
    adapter: Any

@dataclass
class CheckpointEntry:
    task_id: str
    step: int
    status: str
    diff: str = ""
    summary: str = ""
    created_at: float = field(default_factory=time.time)
    id: Optional[int] = None

@dataclass
class Task:
    prompt: str
    capabilities: Tuple[str, ...] = ()
    dependencies: Tuple[str, ...] = ()
    timeout: float = 30.0
    max_retries: int = 0
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    owned_paths: Tuple[str, ...] = ()
    checkpoint: Optional[str] = None
    worktree: Optional[str] = None
    branch: Optional[str] = None
    agent_id: Optional[str] = None
    review: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    failover_history: Tuple[str, ...] = ()
