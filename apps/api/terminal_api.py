"""
JARVIS Terminal Management REST API
Provides interactive terminal sessions, command execution with directory tracking,
and background job management.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from tools.terminal.terminal_manager import terminal_engine
from tools.desktop.program_runner import program_runner

logger = logging.getLogger("JARVIS-TERMINAL-API")
terminal_router = APIRouter(prefix="/terminal", tags=["terminal"])


class ExecuteCommandRequest(BaseModel):
    command: str
    session_id: str = "default"
    confirm: bool = False
    confirmation_token: Optional[str] = None
    timeout: int = 45


class ChangeDirRequest(BaseModel):
    directory: str
    session_id: str = "default"


@terminal_router.get("/sessions")
def list_sessions() -> List[Dict[str, Any]]:
    """List active persistent terminal sessions."""
    return terminal_engine.list_sessions()


@terminal_router.post("/execute")
def execute_command(req: ExecuteCommandRequest) -> Dict[str, Any]:
    """Execute command in terminal session with real output capture."""
    return terminal_engine.execute_command(
        command=req.command,
        session_id=req.session_id,
        confirm=req.confirm,
        confirmation_token=req.confirmation_token,
        timeout=req.timeout,
    )


@terminal_router.get("/history")
def get_history(session_id: str = "default") -> List[Dict[str, Any]]:
    """Get command history for terminal session."""
    return terminal_engine.get_history(session_id)


@terminal_router.get("/processes")
def list_processes() -> List[Dict[str, Any]]:
    """List tracked background processes."""
    return program_runner.list_jobs()


@terminal_router.post("/processes/{job_id}/stop")
def stop_process(job_id: str) -> Dict[str, Any]:
    """Stop a tracked background process."""
    return program_runner.stop_job(job_id)
