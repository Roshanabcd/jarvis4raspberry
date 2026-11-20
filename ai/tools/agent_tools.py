"""Expose registered capabilities to models without trusting model authorization."""
import concurrent.futures
import inspect
import json
import re
from typing import Any, Dict, List, Optional

_TYPES = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
}


def available_tools(
    role: str = "admin",
    query: Optional[str] = None,
    max_tools: Optional[int] = None,
    provider_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return role-filtered tool schemas.
    When querying smaller local models (e.g. Ollama), tools can be relevance-ranked
    to prevent swamping the small model's context window.
    """
    from tools.registry import tool_registry
    from tools.identity.permission_manager import permission_manager

    candidates = []
    for entry in tool_registry.list_tools():
        if not permission_manager.check_tool_permission(entry["name"], user_role=role)[0]:
            continue
        candidates.append(entry)

    # Local models (e.g. Ollama) have limited context; avoid swamping with 90+ tool schemas
    is_local_provider = bool(provider_name and ("ollama" in provider_name.lower() or "local" in provider_name.lower()))
    effective_max = max_tools or (16 if (is_local_provider and query) else None)

    if effective_max and query and len(candidates) > effective_max:
        query_words = set(re.findall(r"\w+", query.lower()))
        def relevance_score(entry: Dict[str, Any]) -> float:
            name_words = set(re.findall(r"\w+", entry["name"].lower()))
            desc_words = set(re.findall(r"\w+", entry["description"].lower()))
            # Essential baseline tools receive baseline weighting
            baseline = 1.0 if entry["name"] in ("calculate", "get_system_status", "read_file", "search_files", "web_search", "run_command") else 0.0
            overlap = len(query_words & name_words) * 3.0 + len(query_words & desc_words) * 1.0
            return baseline + overlap

        candidates = sorted(candidates, key=relevance_score, reverse=True)[:effective_max]

    result = []
    for entry in candidates:
        definition = tool_registry.get_tool(entry["name"])
        signature = inspect.signature(definition["execute"])
        properties = {}
        for name, kind in entry["schema"].items():
            if name == "confirmed":
                continue
            kind = _TYPES.get(kind, kind)
            properties[name] = {} if kind == "any" else {"type": kind}
            if kind == "array":
                properties[name]["items"] = {}
        required = [
            name
            for name, param in signature.parameters.items()
            if name in properties and param.default is inspect.Parameter.empty
        ]
        result.append({
            "name": entry["name"],
            "description": entry["description"],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        })
    return result


def execute_agent_tool(
    name: str,
    arguments: Any,
    advertised: Any,
    role: str,
    timeout: float = 15.0,
) -> str:
    """Fail closed: no legacy fallback, invented tools, or model-supplied approval."""
    from tools.registry import tool_registry
    from tools.identity.permission_manager import permission_manager

    if not isinstance(name, str) or name not in advertised:
        return json.dumps({"error": "Tool is not available for this request"})
    if not isinstance(arguments, dict):
        return json.dumps({"error": "Tool arguments must be an object"})
    definition = tool_registry.get_tool(name)
    if not definition or set(arguments) - (set(definition["schema"]) - {"confirmed"}):
        return json.dumps({"error": "Unknown or authorization-related tool arguments"})
    allowed, reason = permission_manager.check_tool_permission(name, user_role=role)
    if not allowed:
        return json.dumps({"error": reason})
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(tool_registry.execute_tool, name, arguments, confirmed=False)
            res = future.result(timeout=timeout)
        return json.dumps(res, default=str)
    except concurrent.futures.TimeoutError:
        return json.dumps({"error": f"Tool '{name}' execution timed out after {timeout}s"})
    except PermissionError as pe:
        return json.dumps({"error": f"Permission denied: {pe}"})
    except Exception:
        return json.dumps({"error": "Tool execution failed; no fallback was attempted"})
