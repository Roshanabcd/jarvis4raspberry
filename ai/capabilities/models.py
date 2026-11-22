"""Pydantic data models for JARVIS Autonomous Capability System."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CapabilityCategory(str, Enum):
    AI_AGENTS = "ai_agents"
    DEVELOPER_TOOLS = "developer_tools"
    RESEARCH_KNOWLEDGE = "research_knowledge"
    COMPUTER_VISION = "computer_vision"
    EDUCATION_LEARNING = "education_learning"
    MEDIA_CONTENT = "media_content"
    BUSINESS_SUPPORT = "business_support"
    PRODUCTIVITY = "productivity"
    SECURITY_ANALYTICS = "security_analytics"
    EXPERIMENTAL = "experimental"
    GOVERNANCE = "governance"
    NOTIFICATIONS = "notifications"
    MANAGEMENT = "management"
    PC_AUTOMATION = "pc_automation"


class CapabilityParameter(BaseModel):
    name: str
    type: str = "string"  # "string", "int", "float", "bool", "dict", "list"
    description: str = ""
    required: bool = False
    default: Any = None


class CapabilityAction(BaseModel):
    action_id: str
    name: str
    description: str = ""
    parameters: List[CapabilityParameter] = Field(default_factory=list)
    requires_admin: bool = False
    requires_approval: bool = False


class Capability(BaseModel):
    id: str
    name: str
    category: CapabilityCategory
    tier: str = "medium"  # "lightweight", "medium", "heavy"
    description: str
    route: Optional[str] = None
    target_tab: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    regex_triggers: List[str] = Field(default_factory=list)
    actions: List[CapabilityAction] = Field(default_factory=list)
    minimum_role: str = "USER"  # "GUEST", "USER", "ADMIN"
    is_cli: bool = False
    is_plugin: bool = False
    is_builtin: bool = True
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CapabilityIntentMatch(BaseModel):
    capability_id: str
    action_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict)
    matched_pattern: Optional[str] = None
    rationale: str = ""


class CapabilityInvocationRequest(BaseModel):
    capability_id: str
    action_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_id: str = "default_user"
    role: str = "USER"
    session_id: str = "default"
    channel: str = "chat"  # "voice", "chat", "background_task", "api"


class CapabilityResult(BaseModel):
    status: str = "ok"  # "ok", "error", "approval_required", "unauthorized", "unavailable"
    capability_id: str
    action_id: str
    data: Any = None
    markdown_output: str = ""
    spoken_summary: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class PlanStep(BaseModel):
    step_id: str
    title: str
    capability_id: str
    action_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    status: str = "pending"  # "pending", "running", "completed", "failed", "skipped"
    result: Optional[CapabilityResult] = None


class MultiTaskPlan(BaseModel):
    plan_id: str
    original_prompt: str
    steps: List[PlanStep] = Field(default_factory=list)
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    final_summary: str = ""
    spoken_summary: str = ""
    total_execution_time_ms: float = 0.0
