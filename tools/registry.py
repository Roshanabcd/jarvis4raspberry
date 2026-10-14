"""Tool Registry for JARVIS OS.

Provides centralized registration, schema validation, permission checks,
safety verifications, and audit logging for all tools in the operating environment.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

from config.config_manager import config
from security.audit.audit_logger import audit_logger
from security.permissions.permission_manager import permission_manager

logger = logging.getLogger("JARVIS-TOOL-REGISTRY")

TYPE_MAPPING = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": (float, int),
    "number": (float, int),
    "bool": bool,
    "boolean": bool,
    "list": list,
    "array": list,
    "dict": dict,
    "object": dict,
    "any": object,
}


class ToolRegistry:
    """Central registry and execution manager for JARVIS OS tools."""

    def __init__(self, auto_register_core: bool = True) -> None:
        """Initialize ToolRegistry.

        Args:
            auto_register_core: Whether to automatically register core built-in tools.
        """
        self._tools: Dict[str, Dict[str, Any]] = {}
        if auto_register_core:
            try:
                self.register_core_tools()
            except Exception as exc:
                logger.warning(f"Could not auto-register core tools: {exc}")

    def register_tool(self, tool_def: Dict[str, Any]) -> None:
        """Register a new tool definition with schema and execution metadata.

        Args:
            tool_def: Dictionary containing:
                - name (str): Unique name of the tool.
                - description (str): Purpose and instructions for the tool.
                - schema (dict): Mapping of parameter names to expected type strings.
                - risk_level (int): Risk rating from 0 to 4.
                - permissions (list): List of required permission scopes.
                - execute (callable): The function or coroutine to execute.
                - validate (callable, optional): Custom validator function.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = ["name", "description", "schema", "risk_level", "permissions", "execute"]
        for field in required_fields:
            if field not in tool_def:
                raise ValueError(f"Tool definition missing required field: '{field}'")

        name = tool_def["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tool 'name' must be a non-empty string.")

        if not callable(tool_def["execute"]):
            raise ValueError(f"Tool '{name}' 'execute' property must be callable.")

        risk_level = tool_def["risk_level"]
        if not isinstance(risk_level, int) or not (0 <= risk_level <= 4):
            raise ValueError(f"Tool '{name}' 'risk_level' must be an integer between 0 and 4.")

        # Default validator if not supplied
        validate_fn = tool_def.get("validate")
        if validate_fn is None or not callable(validate_fn):
            validate_fn = self._build_default_validator(tool_def["schema"], tool_def["execute"])

        entry = {
            "name": name,
            "description": tool_def["description"],
            "schema": dict(tool_def["schema"]),
            "risk_level": risk_level,
            "permissions": list(tool_def["permissions"]),
            "execute": tool_def["execute"],
            "validate": validate_fn,
        }

        self._tools[name] = entry
        logger.info(f"Registered tool: '{name}' (risk_level={risk_level})")

    def register(self, name: str, func: Callable[..., Any], description: str = "", risk_level: int = 1) -> None:
        """Convenience method for registering simple callable tools (backward-compatibility).

        Args:
            name: Tool identifier.
            func: Executable callable.
            description: Tool description.
            risk_level: Risk score (0-4).
        """
        self.register_tool({
            "name": name,
            "description": description or f"Execute {name}",
            "schema": {},
            "risk_level": risk_level,
            "permissions": [name],
            "execute": func,
            "validate": lambda kwargs: (True, None),
        })

    def _build_default_validator(
        self,
        schema: Dict[str, str],
        execute_fn: Optional[Callable[..., Any]] = None,
    ) -> Callable[[Dict[str, Any]], tuple[bool, Optional[str]]]:
        """Construct a schema validation function for input parameters.

        Args:
            schema: Mapping of parameter name to type string.
            execute_fn: Optional target callable to check required positional/keyword arguments.

        Returns:
            Callable returning (is_valid, error_message).
        """
        def default_validate(kwargs: Dict[str, Any]) -> tuple[bool, Optional[str]]:
            # Check required arguments from execute_fn signature if available
            if execute_fn is not None:
                try:
                    sig = inspect.signature(execute_fn)
                    for param_name, param in sig.parameters.items():
                        if param_name in ("self", "cls", "confirmed"):
                            continue
                        if param.default == inspect.Parameter.empty and param.kind in (
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            inspect.Parameter.KEYWORD_ONLY,
                        ):
                            if param_name not in kwargs:
                                return False, f"Missing required parameter '{param_name}'"
                except (ValueError, TypeError):
                    pass

            for param_name, type_str in schema.items():
                if param_name in kwargs:
                    val = kwargs[param_name]
                    target_type = TYPE_MAPPING.get(type_str.lower(), object)
                    if type_str.lower() in ("int", "integer"):
                        if isinstance(val, bool) or not isinstance(val, int):
                            return False, f"Parameter '{param_name}' must be an integer, got {type(val).__name__}"
                    elif type_str.lower() in ("bool", "boolean"):
                        if not isinstance(val, bool):
                            return False, f"Parameter '{param_name}' must be a boolean, got {type(val).__name__}"
                    elif not isinstance(val, target_type):
                        return False, f"Parameter '{param_name}' must be {type_str}, got {type(val).__name__}"
            return True, None

        return default_validate

    def schema_validate(self, tool: Dict[str, Any], kwargs: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate input arguments against tool schema or custom validator.

        Args:
            tool: Tool definition dictionary.
            kwargs: Arguments to validate.

        Returns:
            tuple[bool, Optional[str]]: (Success boolean, Error message or None).
        """
        try:
            validator = tool.get("validate")
            if callable(validator):
                res = validator(kwargs)
                if isinstance(res, tuple) and len(res) == 2:
                    return bool(res[0]), res[1]
                if isinstance(res, bool):
                    return res, None if res else "Schema validation failed"
            return True, None
        except Exception as exc:
            return False, f"Validation exception: {exc}"

    def permission_check(self, tool: Dict[str, Any], confirmed: bool = False) -> tuple[bool, Optional[str]]:
        """Check whether execution is authorized under security policies.

        Args:
            tool: Tool definition dictionary.
            confirmed: Whether the caller has passed explicit confirmation.

        Returns:
            tuple[bool, Optional[str]]: (Authorized boolean, Error message or None).
        """
        tool_name = tool["name"]
        risk_level = tool["risk_level"]
        allowed = permission_manager.check_permission(tool_name, risk_level=risk_level, confirmed=confirmed)
        if not allowed:
            return False, f"Permission denied for tool '{tool_name}' (risk={risk_level}, confirmed={confirmed})"
        return True, None

    def safety_check(self, tool: Dict[str, Any], kwargs: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Apply simulation-mode guards and pre-execution safety barriers.

        Args:
            tool: Tool definition dictionary.
            kwargs: Execution arguments.

        Returns:
            tuple[bool, Optional[str]]: (Safe boolean, Error message or None).
        """
        simulated = config.get("simulation_mode", True)
        if tool["risk_level"] >= 3:
            logger.info(f"Safety check passed for high-risk tool '{tool['name']}' (simulation_mode={simulated})")
        return True, None

    def execute(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a tool through the complete safety and audit pipeline.

        Pipeline:
            1. schema_validate
            2. permission_check
            3. safety_check
            4. execute
            5. audit_log

        Args:
            name: Tool identifier.
            **kwargs: Arguments passed to the tool's execution callable.

        Returns:
            Dictionary with {'success': bool, 'result': Any, 'error': str | None}.
        """
        start_time = time.perf_counter()
        confirmed = bool(kwargs.pop("confirmed", False))

        if name not in self._tools:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Tool '{name}' not found in registry."
            audit_logger.log_event(
                service="tool_registry",
                event="tool_execution_failed",
                tool=name,
                user_request=str(kwargs),
                status="not_found",
                risk_level=0,
                duration_ms=duration_ms,
                error=error_msg,
            )
            return {"success": False, "result": None, "error": error_msg}

        tool = self._tools[name]
        risk_level = tool["risk_level"]

        # 1. Schema Validation
        valid, val_err = self.schema_validate(tool, kwargs)
        if not valid:
            duration_ms = (time.perf_counter() - start_time) * 1000
            audit_logger.log_event(
                service="tool_registry",
                event="schema_validation_failed",
                tool=name,
                user_request=str(kwargs),
                status="invalid_schema",
                risk_level=risk_level,
                duration_ms=duration_ms,
                error=val_err,
            )
            return {"success": False, "result": None, "error": val_err}

        # 2. Permission Check
        permitted, perm_err = self.permission_check(tool, confirmed=confirmed)
        if not permitted:
            duration_ms = (time.perf_counter() - start_time) * 1000
            audit_logger.log_event(
                service="tool_registry",
                event="permission_check_failed",
                tool=name,
                user_request=str(kwargs),
                status="permission_denied",
                risk_level=risk_level,
                duration_ms=duration_ms,
                error=perm_err,
            )
            return {"success": False, "result": None, "error": perm_err}

        # 3. Safety Check
        safe, safety_err = self.safety_check(tool, kwargs)
        if not safe:
            duration_ms = (time.perf_counter() - start_time) * 1000
            audit_logger.log_event(
                service="tool_registry",
                event="safety_check_failed",
                tool=name,
                user_request=str(kwargs),
                status="safety_aborted",
                risk_level=risk_level,
                duration_ms=duration_ms,
                error=safety_err,
            )
            return {"success": False, "result": None, "error": safety_err}

        # 4. Execute
        exec_fn = tool["execute"]
        result: Any = None
        error_str: Optional[str] = None
        success = False

        # If confirmed was requested by function signature, pass it back
        sig = inspect.signature(exec_fn)
        call_kwargs = dict(kwargs)
        if "confirmed" in sig.parameters:
            call_kwargs["confirmed"] = confirmed

        try:
            if inspect.iscoroutinefunction(exec_fn):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        result = pool.submit(asyncio.run, exec_fn(**call_kwargs)).result()
                else:
                    result = asyncio.run(exec_fn(**call_kwargs))
            else:
                result = exec_fn(**call_kwargs)

            success = True
        except Exception as exc:
            error_str = f"Execution error in '{name}': {str(exc)}"
            logger.error(error_str, exc_info=True)
            success = False

        duration_ms = (time.perf_counter() - start_time) * 1000

        # 5. Audit Log
        audit_logger.log_event(
            service="tool_registry",
            event="tool_executed" if success else "tool_execution_failed",
            tool=name,
            user_request=str(kwargs),
            status="success" if success else "error",
            risk_level=risk_level,
            duration_ms=duration_ms,
            error=error_str,
        )

        return {
            "success": success,
            "result": result,
            "error": error_str,
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve tool metadata by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of all registered tool metadata dictionaries."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "schema": t["schema"],
                "risk_level": t["risk_level"],
                "permissions": t["permissions"],
            }
            for t in self._tools.values()
        ]

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool if it exists."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def register_core_tools(self) -> None:
        """Register built-in core tools across filesystem, shell, web, git, and scheduler."""
        from tools.filesystem.file_tools import file_tools
        from tools.shell.command_runner import command_runner
        from tools.web_search.searcher import web_searcher
        from tools.git.git_tools import git_tools
        from tools.scheduler.task_scheduler import task_scheduler

        # Filesystem tools
        self.register_tool({
            "name": "read_file",
            "description": "Read contents of a file within allowed workspaces",
            "schema": {"path": "str"},
            "risk_level": 0,
            "permissions": ["filesystem:read"],
            "execute": file_tools.read_file,
        })
        self.register_tool({
            "name": "write_file",
            "description": "Write text content to a file within allowed workspaces",
            "schema": {"path": "str", "content": "str"},
            "risk_level": 1,
            "permissions": ["filesystem:write"],
            "execute": file_tools.write_file,
        })
        self.register_tool({
            "name": "append_file",
            "description": "Append text content to a file within allowed workspaces",
            "schema": {"path": "str", "content": "str"},
            "risk_level": 1,
            "permissions": ["filesystem:append"],
            "execute": file_tools.append_file,
        })
        self.register_tool({
            "name": "create_dir",
            "description": "Create a directory recursively within allowed workspaces",
            "schema": {"path": "str"},
            "risk_level": 1,
            "permissions": ["filesystem:mkdir"],
            "execute": file_tools.create_dir,
        })
        self.register_tool({
            "name": "list_dir",
            "description": "List directory contents within allowed workspaces",
            "schema": {"path": "str"},
            "risk_level": 0,
            "permissions": ["filesystem:list"],
            "execute": file_tools.list_dir,
        })
        self.register_tool({
            "name": "copy_file",
            "description": "Copy a file within allowed workspaces",
            "schema": {"src": "str", "dst": "str"},
            "risk_level": 1,
            "permissions": ["filesystem:copy"],
            "execute": file_tools.copy_file,
        })
        self.register_tool({
            "name": "move_file",
            "description": "Move a file within allowed workspaces",
            "schema": {"src": "str", "dst": "str"},
            "risk_level": 1,
            "permissions": ["filesystem:move"],
            "execute": file_tools.move_file,
        })
        self.register_tool({
            "name": "delete_file",
            "description": "Delete a file or directory within allowed workspaces (requires confirmation)",
            "schema": {"path": "str"},
            "risk_level": 3,
            "permissions": ["filesystem:delete"],
            "execute": file_tools.delete_file,
        })
        self.register_tool({
            "name": "search_files",
            "description": "Search recursively for files matching a glob pattern",
            "schema": {"directory": "str", "pattern": "str"},
            "risk_level": 0,
            "permissions": ["filesystem:search"],
            "execute": file_tools.search_files,
        })

        # Shell tools
        self.register_tool({
            "name": "run_command",
            "description": "Execute an allowed shell command safely without shell interpolation",
            "schema": {"command": "str"},
            "risk_level": 2,
            "permissions": ["shell:execute"],
            "execute": command_runner.execute_command,
        })

        # Web search tools
        self.register_tool({
            "name": "web_search",
            "description": "Search the web using DuckDuckGo Instant Answer API",
            "schema": {"query": "str"},
            "risk_level": 0,
            "permissions": ["web:search"],
            "execute": web_searcher.search,
        })
        self.register_tool({
            "name": "fetch_page",
            "description": "Fetch a web page and extract clean plain text",
            "schema": {"url": "str"},
            "risk_level": 0,
            "permissions": ["web:fetch"],
            "execute": web_searcher.fetch_page,
        })

        # Git tools
        self.register_tool({
            "name": "git_clone",
            "description": "Clone a Git repository into a workspace path",
            "schema": {"url": "str", "path": "str"},
            "risk_level": 1,
            "permissions": ["git:clone"],
            "execute": git_tools.clone,
        })
        self.register_tool({
            "name": "git_status",
            "description": "Check Git repository status",
            "schema": {"repo_path": "str"},
            "risk_level": 0,
            "permissions": ["git:status"],
            "execute": git_tools.status,
        })
        self.register_tool({
            "name": "git_log",
            "description": "View commit log history of a Git repository",
            "schema": {"repo_path": "str"},
            "risk_level": 0,
            "permissions": ["git:log"],
            "execute": git_tools.log,
        })
        self.register_tool({
            "name": "git_diff",
            "description": "View unstaged git diff",
            "schema": {"repo_path": "str"},
            "risk_level": 0,
            "permissions": ["git:diff"],
            "execute": git_tools.diff,
        })
        self.register_tool({
            "name": "git_checkout",
            "description": "Switch branches in a git repository",
            "schema": {"repo_path": "str", "branch": "str"},
            "risk_level": 1,
            "permissions": ["git:checkout"],
            "execute": git_tools.checkout,
        })
        self.register_tool({
            "name": "git_commit",
            "description": "Commit staged changes in a git repository",
            "schema": {"repo_path": "str", "message": "str"},
            "risk_level": 2,
            "permissions": ["git:commit"],
            "execute": git_tools.commit,
        })
        self.register_tool({
            "name": "push_git",
            "description": "Push commits to remote git repository (requires confirmation)",
            "schema": {"repo_path": "str"},
            "risk_level": 3,
            "permissions": ["git:push"],
            "execute": git_tools.push,
        })

        # Scheduler tools
        self.register_tool({
            "name": "schedule_task",
            "description": "Schedule a command to run periodically (HH:MM format)",
            "schema": {"name": "str", "cron_expr": "str", "command": "str"},
            "risk_level": 2,
            "permissions": ["scheduler:manage"],
            "execute": task_scheduler.schedule_task,
        })
        self.register_tool({
            "name": "list_tasks",
            "description": "List all scheduled background tasks",
            "schema": {},
            "risk_level": 0,
            "permissions": ["scheduler:read"],
            "execute": task_scheduler.list_tasks,
        })
        self.register_tool({
            "name": "pause_task",
            "description": "Pause a scheduled task by ID",
            "schema": {"task_id": "str"},
            "risk_level": 1,
            "permissions": ["scheduler:manage"],
            "execute": task_scheduler.pause_task,
        })
        self.register_tool({
            "name": "resume_task",
            "description": "Resume a paused scheduled task by ID",
            "schema": {"task_id": "str"},
            "risk_level": 1,
            "permissions": ["scheduler:manage"],
            "execute": task_scheduler.resume_task,
        })
        self.register_tool({
            "name": "delete_task",
            "description": "Delete a scheduled task by ID",
            "schema": {"task_id": "str"},
            "risk_level": 2,
            "permissions": ["scheduler:manage"],
            "execute": task_scheduler.delete_task,
        })


# Global tool registry instances for compatibility
tool_registry = ToolRegistry()
registry = tool_registry
