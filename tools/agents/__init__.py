"""JARVIS OS Phase 5 Multi-Agent Orchestrator Package."""
from tools.agents.models import (
    AgentId,
    AgentStatus,
    AgentCapabilities,
    AgentMetadata,
    ProblemContext,
    PermissionProfile,
    PermissionStatus,
    PermissionRequest,
    TaskPhase,
    AgentTask,
)
from tools.agents.registry import agent_registry, AgentRegistry
from tools.agents.permission_manager import permission_manager, AgentPermissionManager
from tools.agents.context_packager import context_packager, ProblemContextPackager
from tools.agents.git_safety import git_safety, GitSafetyManager
from tools.agents.stuck_watchdog import stuck_watchdog, StuckTaskWatchdog
from tools.agents.orchestrator import multi_agent_orchestrator, MultiAgentOrchestrator
from tools.agents.self_healing import self_healing_engine, SelfHealingEngine

__all__ = [
    "AgentId",
    "AgentStatus",
    "AgentCapabilities",
    "AgentMetadata",
    "ProblemContext",
    "PermissionProfile",
    "PermissionStatus",
    "PermissionRequest",
    "TaskPhase",
    "AgentTask",
    "agent_registry",
    "AgentRegistry",
    "permission_manager",
    "AgentPermissionManager",
    "context_packager",
    "ProblemContextPackager",
    "git_safety",
    "GitSafetyManager",
    "stuck_watchdog",
    "StuckTaskWatchdog",
    "multi_agent_orchestrator",
    "MultiAgentOrchestrator",
    "self_healing_engine",
    "SelfHealingEngine",
]
