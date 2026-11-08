"""
JARVIS OS Tools API
Allows listing and executing registered agent tools across Categories A through H.
"""
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tools.registry import tool_registry

logger = logging.getLogger("JARVIS.API.Tools")
tools_router = APIRouter(prefix="/tools", tags=["tools"])


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


@tools_router.get("")
def list_tools(category: Optional[str] = None):
    """List all registered tools, schemas, categories, and risk levels."""
    all_tools = tool_registry.list_tools()
    if category:
        all_tools = [t for t in all_tools if t.get("category", "").lower() == category.lower()]
    return {
        "status": "ok",
        "total": len(all_tools),
        "tools": all_tools,
    }


@tools_router.post("/execute")
def execute_tool(req: ToolExecuteRequest):
    """Execute a registered tool directly with validated parameters."""
    res = tool_registry.execute_tool(
        name=req.tool_name,
        arguments=req.arguments,
        user_confirmed=req.confirmed,
    )
    if not res.get("success", False) and "Tool" in res.get("error", "") and "not found" in res.get("error", ""):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res
