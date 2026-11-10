"""
JARVIS OS — Apps Center Data Models & Manifest Schema.
Provides strict validation for application registration, categories, permissions,
resource profiles, and task execution states.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class AppStatus(str, Enum):
    AVAILABLE = "available"
    IN_DEVELOPMENT = "in_development"
    PLANNED = "planned"
    DISABLED = "disabled"
    ERROR = "error"


class AppCategory(str, Enum):
    PRODUCTIVITY = "productivity"
    EDUCATION_LEARNING = "education_learning"
    DEVELOPER_TOOLS = "developer_tools"
    AI_AGENTS = "ai_agents"
    BUSINESS_SUPPORT = "business_support"
    RESEARCH_KNOWLEDGE = "research_knowledge"
    COMPUTER_VISION = "computer_vision"
    MEDIA_CONTENT = "media_content"
    SECURITY_ANALYTICS = "security_analytics"
    EXPERIMENTAL = "experimental"


CATEGORY_LABELS: Dict[AppCategory, str] = {
    AppCategory.PRODUCTIVITY: "Productivity",
    AppCategory.EDUCATION_LEARNING: "Education & Learning",
    AppCategory.DEVELOPER_TOOLS: "Developer Tools",
    AppCategory.AI_AGENTS: "AI Agents",
    AppCategory.BUSINESS_SUPPORT: "Business & Customer Support",
    AppCategory.RESEARCH_KNOWLEDGE: "Research & Knowledge",
    AppCategory.COMPUTER_VISION: "Computer Vision",
    AppCategory.MEDIA_CONTENT: "Media & Content Creation",
    AppCategory.SECURITY_ANALYTICS: "Security & Analytics",
    AppCategory.EXPERIMENTAL: "Experimental Applications",
}


class ResourceProfile(str, Enum):
    LIGHTWEIGHT = "lightweight"
    MEDIUM = "medium"
    HEAVY = "heavy"
    CLOUD_ONLY = "cloud_only"


class InferenceType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class LifecycleState(str, Enum):
    ACTIVE = "active"
    IN_DEVELOPMENT = "in_development"
    PLANNED = "planned"
    DISABLED = "disabled"
    ERROR = "error"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Allowlist of canonical 20 application IDs
CANONICAL_APP_IDS = {
    "voice-assistant",
    "face-recognition",
    "document-qa",
    "ai-interview",
    "study-planner",
    "learning-coach",
    "speech-translation",
    "youtube-summarizer",
    "research-assistant",
    "web-scraper",
    "coding-assistant",
    "multi-agent-automation",
    "ai-search-engine",
    "customer-support",
    "recommendation-engine",
    "fraud-detection",
    "resume-matching",
    "social-media-saas",
    "content-creation",
    "trading-bot",
}


class ApplicationManifest(BaseModel):
    """
    Standard application manifest schema.
    Strictly validated. No arbitrary dynamic code execution is permitted.
    """
    id: str = Field(..., description="Unique application identifier in kebab-case")
    name: str = Field(..., description="Human-readable application display name")
    version: str = Field("0.1.0", description="Semantic version string")
    description: str = Field(..., description="Application functional description")
    category: AppCategory = Field(..., description="Application category")
    icon: str = Field("📦", description="Application emoji or SVG icon identifier")
    status: AppStatus = Field(AppStatus.PLANNED, description="Truthful operational status")
    route: str = Field(..., description="Internal URL route or webview endpoint")
    target_tab: Optional[str] = Field(None, description="Dashboard tab identifier for embedded apps")
    minimum_role: str = Field("USER", description="Minimum RBAC role required: ADMIN, USER, GUEST")
    permissions: List[str] = Field(default_factory=list, description="Declared permission tokens")
    capabilities: List[str] = Field(default_factory=list, description="Exposed AI capabilities")
    resource_profile: ResourceProfile = Field(ResourceProfile.MEDIUM, description="Pi 5 resource demand tier")
    inference_type: InferenceType = Field(InferenceType.LOCAL, description="Target AI execution location")
    is_builtin: bool = Field(False, description="Whether application is core built-in JARVIS subsystem")
    lifecycle_state: LifecycleState = Field(LifecycleState.PLANNED, description="Module lifecycle state")
    roadmap: Optional[str] = Field(None, description="Development roadmap or milestone description")
    settings_schema: Optional[Dict[str, Any]] = Field(None, description="Schema for app-specific settings")

    @field_validator("id")
    @classmethod
    def validate_app_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Application ID cannot be empty")
        v = v.strip().lower()
        import re
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(f"Invalid application ID '{v}'. Must be lowercase alphanumeric with hyphens.")
        return v

    @field_validator("minimum_role")
    @classmethod
    def validate_minimum_role(cls, v: str) -> str:
        roles = {"ADMIN", "USER", "GUEST"}
        v_upper = v.upper()
        if v_upper not in roles:
            raise ValueError(f"Invalid minimum_role '{v}'. Allowed roles: {roles}")
        return v_upper


class AppTaskRecord(BaseModel):
    task_id: str
    app_id: str
    user_id: str
    task_type: str
    status: TaskStatus
    progress_pct: int = 0
    message: Optional[str] = None
    input_payload: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class ResourceTelemetry(BaseModel):
    cpu_percent: float
    cpu_count: int
    ram_total_mb: float
    ram_available_mb: float
    ram_used_percent: float
    disk_total_gb: float
    disk_available_gb: float
    disk_used_percent: float
    temperature_c: Optional[float] = None
    active_inference_jobs: int = 0
    max_concurrent_heavy_jobs: int = 1
    system_load_status: str = "nominal"  # "nominal", "warning", "critical"
