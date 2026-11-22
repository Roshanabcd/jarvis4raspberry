"""
Data Models for JARVIS OS Phase 5 Multi-Agent Orchestrator.
Defines agent metadata, capabilities, task lifecycles, problem context packages,
permission requests, and watchdog conditions.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(str, Enum):
    READY = "READY"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    NOT_INSTALLED = "NOT_INSTALLED"
    BUSY = "BUSY"
    ERROR = "ERROR"


class AgentId(str, Enum):
    ANTIGRAVITY = "antigravity"
    CODEX = "codex"
    COPILOT = "copilot"
    CLAUDE = "claude"
    OPENCODE = "opencode"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    CUSTOM = "custom"


class PermissionProfile(str, Enum):
    SAFE_AUTO = "SAFE_AUTO"
    SUPERVISED_AUTO = "SUPERVISED_AUTO"
    MANUAL = "MANUAL"


class PermissionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    AUTO_APPROVED = "AUTO_APPROVED"
    HARD_DENIED = "HARD_DENIED"


class TaskPhase(str, Enum):
    DETECTED = "DETECTED"
    DIAGNOSING = "DIAGNOSING"
    PROPOSED_FIX = "PROPOSED_FIX"
    PATCH_RECEIVED = "PATCH_RECEIVED"
    PATCH_APPLIED = "PATCH_APPLIED"
    TESTING = "TESTING"
    TESTS_PASSED = "TESTS_PASSED"
    RUNTIME_VERIFIED = "RUNTIME_VERIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class AgentCapabilities:
    supports_noninteractive: bool = False
    supports_file_editing: bool = False
    supports_shell: bool = False
    supports_structured_output: bool = False
    supports_review: bool = False
    supports_sandbox: bool = False
    models: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentMetadata:
    id: str
    display_name: str
    installed: bool = False
    authenticated: bool = False
    version: Optional[str] = None
    cli_path: Optional[str] = None
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    permission_mode: str = "detected-mode"
    last_health_check: float = field(default_factory=time.time)
    status: AgentStatus = AgentStatus.NOT_INSTALLED
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class ProblemContext:
    problem_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_request: str = ""
    problem_description: str = ""
    failure_type: str = "EXECUTION_ERROR"
    error_message: str = ""
    traceback: str = ""
    failing_code: str = ""
    failed_command: Optional[str] = None
    exit_code: Optional[int] = None
    working_dir: str = "/home/roshan/.gemini/antigravity/scratch/jarvis-os"
    affected_component: Optional[str] = None
    relevant_files: List[str] = field(default_factory=list)
    file_contents: Dict[str, str] = field(default_factory=dict)
    recent_git_diff: str = ""
    test_results: str = ""
    reproduction_instructions: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    sanitized_env: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PermissionRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    operation: str = ""
    target_path: Optional[str] = None
    command: Optional[str] = None
    working_dir: str = "/home/roshan"
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str = ""
    status: PermissionStatus = PermissionStatus.PENDING
    decision_reason: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    decided_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class AgentTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    problem_context: Optional[ProblemContext] = None
    assigned_agent: Optional[str] = None
    fallback_agents: List[str] = field(default_factory=list)
    attempt_count: int = 0
    max_attempts: int = 3
    phase: TaskPhase = TaskPhase.DETECTED
    process_pid: Optional[int] = None
    applied_patch: Optional[str] = None
    modified_files: List[str] = field(default_factory=list)
    test_output: Optional[str] = None
    tests_passed: bool = False
    runtime_verified: bool = False
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        if self.problem_context:
            d["problem_context"] = self.problem_context.to_dict()
        return d

    @property
    def attempts(self) -> int:
        return self.attempt_count

    @attempts.setter
    def attempts(self, val: int) -> None:
        self.attempt_count = val

    @property
    def error_history(self) -> List[str]:
        return self.logs
