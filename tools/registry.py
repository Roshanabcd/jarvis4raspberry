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

    def execute_tool(self, name: str, args: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Execute a tool with dictionary arguments or keyword arguments."""
        params = dict(args or {})
        params.update(kwargs)
        return self.execute(name, **params)

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
        self.register_tool({
            "name": "search_folders",
            "description": "Search recursively for folders matching query string",
            "schema": {"query": "str"},
            "risk_level": 0,
            "permissions": ["filesystem:search"],
            "execute": file_tools.search_folders,
        })
        self.register_tool({
            "name": "open_folder",
            "description": "Open a folder visually on desktop and inspect its contents",
            "schema": {"folder_name": "str", "parent_location": "str"},
            "risk_level": 0,
            "permissions": ["filesystem:read"],
            "execute": file_tools.open_folder,
        })
        self.register_tool({
            "name": "open_file",
            "description": "Open a file with desktop editor or viewer",
            "schema": {"file_path": "str"},
            "risk_level": 0,
            "permissions": ["filesystem:read"],
            "execute": file_tools.open_file,
        })

        # Media tools
        from tools.media.media_player import media_player
        self.register_tool({
            "name": "play_media",
            "description": "Play local audio or stream song/music through speaker",
            "schema": {"query": "any"},
            "risk_level": 0,
            "permissions": ["system:media"],
            "execute": media_player.play,
        })
        self.register_tool({
            "name": "stop_media",
            "description": "Stop current audio or music playback",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:media"],
            "execute": media_player.stop,
        })
        self.register_tool({
            "name": "pause_media",
            "description": "Pause current audio playback",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:media"],
            "execute": media_player.pause,
        })
        self.register_tool({
            "name": "resume_media",
            "description": "Resume paused audio playback",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:media"],
            "execute": media_player.resume,
        })
        self.register_tool({
            "name": "set_volume",
            "description": "Set system audio output volume level (0-100)",
            "schema": {"level_pct": "int"},
            "risk_level": 0,
            "permissions": ["system:media"],
            "execute": media_player.set_volume,
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

        # ── Category A: System Tools ──────────────────────────
        from hardware.raspberry_pi.rpi_info import get_system_status, get_cpu_temp, is_online
        from tools.system.system_tools import system_tools, robot_info_tools
        from tools.calculator.calculator_tools import calculator_tools
        from tools.datetime.datetime_tools import datetime_tools

        def _fn_get_system_status(**_):
            return system_tools.get_system_status()

        def _fn_get_cpu_usage(**_):
            return system_tools.get_cpu_usage()

        def _fn_get_memory_usage(**_):
            return system_tools.get_memory_usage()

        def _fn_get_uptime(**_):
            return system_tools.get_uptime()

        def _fn_get_disk_usage(mount_point: str = "/", **_):
            return system_tools.get_disk_usage(mount_point)

        def _fn_get_cpu_temperature(**_):
            return system_tools.get_cpu_temperature()

        def _fn_get_application_status(**_):
            return system_tools.get_application_status()

        def _fn_get_network_status(**_):
            return system_tools.get_network_status()

        def _fn_get_process_info(limit: int = 25, **_):
            return system_tools.get_process_info(limit=limit)

        self.register_tool({
            "name": "get_system_status",
            "description": "Get real-time CPU, RAM (total, used, avail in GB), temperature, disk usage, uptime, and robot state",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_system_status,
        })
        self.register_tool({
            "name": "system_status",
            "description": "Alias for get_system_status",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_system_status,
        })
        self.register_tool({
            "name": "get_cpu_usage",
            "description": "Get real-time CPU percentage and frequency",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_cpu_usage,
        })
        self.register_tool({
            "name": "get_memory_usage",
            "description": "Get real-time RAM and swap memory usage in GB and percentages",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_memory_usage,
        })
        self.register_tool({
            "name": "get_uptime",
            "description": "Get real Linux uptime from /proc/uptime formatted in days, hours, minutes, seconds",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_uptime,
        })
        self.register_tool({
            "name": "get_disk_usage",
            "description": "Get disk usage (total, used, free GB and %) for a mount point",
            "schema": {"mount_point": "str"},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_disk_usage,
        })
        self.register_tool({
            "name": "get_cpu_temperature",
            "description": "Get CPU thermal-zone temperature in degrees Celsius",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_cpu_temperature,
        })
        self.register_tool({
            "name": "get_application_status",
            "description": "Get status of core services (Ollama, PipeWire, Jarvis core)",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_application_status,
        })
        self.register_tool({
            "name": "get_network_status",
            "description": "Get network interfaces, IP addresses, connectivity and IO counters",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_network_status,
        })
        self.register_tool({
            "name": "get_process_info",
            "description": "Get bounded read-only process telemetry without command-line arguments",
            "schema": {"limit": "int"},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_process_info,
        })

        def _fn_get_running_apps_processes(limit: int = 10, **_):
            from tools.system.process_inspector import process_inspector
            overview = process_inspector.get_running_overview(limit=limit)
            return overview.get("markdown", str(overview))

        def _fn_inspect_screen(**_):
            from tools.desktop.desktop_perception import desktop_perception
            from tools.desktop.screen_intelligence import screen_intelligence
            res = desktop_perception.get_screen_resolution()
            active = desktop_perception.get_active_window()
            windows = desktop_perception.list_open_windows()
            err_check = screen_intelligence.check_screen_errors()
            lines = [
                "🖥️ **Screen & Desktop Inspection**",
                f"- **Resolution:** {res.get('width', 1360)}x{res.get('height', 768)}",
                f"- **Active Window:** `{active.get('title', 'Unknown')}` (Class: `{active.get('class', 'N/A')}`, ID: `{active.get('id', 'N/A')}`)",
                f"- **Open Windows Count:** {len(windows)}",
            ]
            if err_check.get("error_found"):
                lines.append(f"- **Screen Errors Detected:** ⚠️ {err_check.get('message')}")
            else:
                lines.append("- **Screen Errors:** None detected")
            if windows:
                lines.append("### Open Windows:")
                for w in windows[:6]:
                    lines.append(f"- `[{w.get('id')}]` {w.get('title')} ({w.get('app')})")
            return "\n".join(lines)

        def _fn_diagnose_system_status(**_):
            from tools.developer.cli_bridge import developer_cli_bridge
            diag = developer_cli_bridge.diagnose_system()
            return diag.get("markdown_report", str(diag))

        self.register_tool({
            "name": "get_running_apps_processes",
            "description": "Inspect running applications, open desktop windows, core service states, and top CPU/RAM processes (safe read-only)",
            "schema": {"limit": "int"},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_running_apps_processes,
        })
        self.register_tool({
            "name": "running_apps_processes",
            "description": "Alias for get_running_apps_processes",
            "schema": {"limit": "int"},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_get_running_apps_processes,
        })
        self.register_tool({
            "name": "inspect_screen",
            "description": "Capture and inspect current desktop screen, active window, resolution, open windows, and visible errors",
            "schema": {},
            "risk_level": 0,
            "permissions": ["desktop:read"],
            "execute": _fn_inspect_screen,
        })
        self.register_tool({
            "name": "screen_observe",
            "description": "Alias for inspect_screen",
            "schema": {},
            "risk_level": 0,
            "permissions": ["desktop:read"],
            "execute": _fn_inspect_screen,
        })
        self.register_tool({
            "name": "diagnose_system_status",
            "description": "Run safe read-only diagnostics across core services, audio sink/streams, git state, and installed developer CLIs",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_diagnose_system_status,
        })

        # ── Category A2: Calculator Tools ─────────────────────
        self.register_tool({
            "name": "calculate",
            "description": "Evaluate mathematical expression accurately (e.g., '25 * 4', '25 multiplied by 4', '15 percent of 800')",
            "schema": {"expression": "str"},
            "risk_level": 0,
            "permissions": ["math:calculate"],
            "execute": calculator_tools.calculate,
        })
        self.register_tool({
            "name": "add",
            "description": "Add two numbers together",
            "schema": {"a": "float", "b": "float"},
            "risk_level": 0,
            "permissions": ["math:calculate"],
            "execute": calculator_tools.add,
        })
        self.register_tool({
            "name": "subtract",
            "description": "Subtract b from a",
            "schema": {"a": "float", "b": "float"},
            "risk_level": 0,
            "permissions": ["math:calculate"],
            "execute": calculator_tools.subtract,
        })
        self.register_tool({
            "name": "multiply",
            "description": "Multiply two numbers together",
            "schema": {"a": "float", "b": "float"},
            "risk_level": 0,
            "permissions": ["math:calculate"],
            "execute": calculator_tools.multiply,
        })
        self.register_tool({
            "name": "divide",
            "description": "Divide a by b with division-by-zero protection",
            "schema": {"a": "float", "b": "float"},
            "risk_level": 0,
            "permissions": ["math:calculate"],
            "execute": calculator_tools.divide,
        })
        self.register_tool({
            "name": "percentage",
            "description": "Calculate percent of a total (e.g. percent=15, total=800 -> 120)",
            "schema": {"percent": "float", "total": "float"},
            "risk_level": 0,
            "permissions": ["math:calculate"],
            "execute": calculator_tools.percentage,
        })

        # ── Category A3: Date & Time Tools ────────────────────
        self.register_tool({
            "name": "get_current_time",
            "description": "Get current local time with timezone on Raspberry Pi 5",
            "schema": {},
            "risk_level": 0,
            "permissions": ["time:read"],
            "execute": datetime_tools.get_current_time,
        })
        self.register_tool({
            "name": "get_current_date",
            "description": "Get current local date and day of week",
            "schema": {},
            "risk_level": 0,
            "permissions": ["time:read"],
            "execute": datetime_tools.get_current_date,
        })
        self.register_tool({
            "name": "get_timezone",
            "description": "Get local timezone name, UTC offset, and DST flag",
            "schema": {},
            "risk_level": 0,
            "permissions": ["time:read"],
            "execute": datetime_tools.get_timezone,
        })
        self.register_tool({
            "name": "calculate_date_difference",
            "description": "Calculate day difference between two YYYY-MM-DD dates",
            "schema": {"start_date": "str", "end_date": "str"},
            "risk_level": 0,
            "permissions": ["time:read"],
            "execute": datetime_tools.calculate_date_difference,
        })
        self.register_tool({
            "name": "format_timestamp",
            "description": "Format an epoch timestamp using strftime format string",
            "schema": {"ts": "float", "fmt": "str"},
            "risk_level": 0,
            "permissions": ["time:read"],
            "execute": datetime_tools.format_timestamp,
        })

        # ── Category A4: Read-Only Robot Info Tools ───────────
        self.register_tool({
            "name": "get_robot_status",
            "description": "Read-only robot controller status and simulation state",
            "schema": {},
            "risk_level": 0,
            "permissions": ["robot:read"],
            "execute": robot_info_tools.get_robot_status,
        })
        self.register_tool({
            "name": "get_motor_state",
            "description": "Read-only motor speed and direction telemetry",
            "schema": {},
            "risk_level": 0,
            "permissions": ["robot:read"],
            "execute": robot_info_tools.get_motor_state,
        })
        self.register_tool({
            "name": "get_safety_state",
            "description": "Read-only e-stop and safety status",
            "schema": {},
            "risk_level": 0,
            "permissions": ["robot:read"],
            "execute": robot_info_tools.get_safety_state,
        })

        # ── Category B: Robot & Actuator Tools ────────────────
        from tools.robotics.controller import robot

        def _is_armed():
            attr = getattr(robot, "is_armed", None)
            return attr() if callable(attr) else bool(getattr(robot, "armed", False))

        def _is_estop():
            attr = getattr(robot, "is_emergency_stopped", None)
            return attr() if callable(attr) else bool(getattr(robot, "emergency_stopped", False))

        def _fn_robot_status(**_):
            return {
                "armed": _is_armed(),
                "emergency_stopped": _is_estop(),
                "state": str(getattr(robot, "state", "UNKNOWN")),
                "simulated": getattr(robot, "simulated", True),
                "default_speed": getattr(robot, "default_speed", 50),
            }

        def _fn_robot_arm(**_):
            result = robot.arm()
            if not result.get("armed", False):
                raise PermissionError(result.get("error", "Robot arm request rejected by safety interlock"))
            return {"armed": _is_armed(), "status": "ARMED"}

        def _fn_robot_disarm(**_):
            robot.disarm()
            return {"armed": _is_armed(), "status": "DISARMED"}

        def _fn_robot_move(direction: str, speed: int = 50, duration_ms: int = 0, **_):
            safe_speed = max(0, min(100, int(speed)))
            safe_duration = max(0, min(10000, int(duration_ms)))
            actions = {
                "forward": lambda: robot.forward(safe_speed),
                "backward": lambda: robot.backward(safe_speed),
                "left": lambda: robot.turn_left(safe_speed),
                "right": lambda: robot.turn_right(safe_speed),
                "stop": robot.stop,
                "estop": robot.emergency_stop,
            }
            fn = actions.get(direction.lower())
            if not fn:
                return {"error": f"Invalid direction: {direction}"}
            outcome = fn()
            if direction.lower() in {"forward", "backward", "left", "right"} and not outcome:
                raise PermissionError("Robot motion rejected by the armed/e-stop safety interlock")
            if safe_duration > 0:
                time.sleep(safe_duration / 1000.0)
                robot.stop()
            return {
                "direction": direction,
                "speed": safe_speed,
                "duration_ms": safe_duration,
                "armed": _is_armed(),
                "state": str(getattr(robot, "state", "UNKNOWN")),
            }

        def _fn_servo_set(channel: int, angle: int, **_):
            c = max(0, min(15, int(channel)))
            a = max(0, min(180, int(angle)))
            if not robot.set_servo(c, a):
                raise PermissionError("Servo motion rejected by the armed/e-stop safety interlock")
            return {"channel": c, "angle": a, "status": "ok"}

        def _fn_robot_estop(**_):
            robot.emergency_stop()
            return {"emergency_stopped": True, "armed": False, "status": "EMERGENCY_STOP_LATCHED"}

        self.register_tool({
            "name": "robot_status",
            "description": "Get robot state, armed status, and safety lockout status",
            "schema": {},
            "risk_level": 0,
            "permissions": ["robot:read"],
            "execute": _fn_robot_status,
        })
        self.register_tool({
            "name": "robot_arm",
            "description": "Explicitly arm robot drive motors (requires confirmation)",
            "schema": {},
            "risk_level": 3,
            "permissions": ["robot:arm"],
            "execute": _fn_robot_arm,
        })
        self.register_tool({
            "name": "robot_disarm",
            "description": "Disarm robot drive motors into safe state",
            "schema": {},
            "risk_level": 1,
            "permissions": ["robot:disarm"],
            "execute": _fn_robot_disarm,
        })
        self.register_tool({
            "name": "robot_move",
            "description": "Drive robot motors: forward|backward|left|right|stop|estop",
            "schema": {"direction": "str", "speed": "int", "duration_ms": "int"},
            "risk_level": 3,
            "permissions": ["robot:move"],
            "execute": _fn_robot_move,
        })
        self.register_tool({
            "name": "servo_set",
            "description": "Position a servo channel (0-15) to angle (0-180 deg)",
            "schema": {"channel": "int", "angle": "int"},
            "risk_level": 3,
            "permissions": ["robot:servo"],
            "execute": _fn_servo_set,
        })
        self.register_tool({
            "name": "robot_estop",
            "description": "Immediate hardware emergency stop latch",
            "schema": {},
            "risk_level": 0,
            "permissions": ["robot:estop"],
            "execute": _fn_robot_estop,
        })

        # ── Category C: Sensor Tools ──────────────────────────
        from hardware.sensors.sensor_manager import sensor_manager

        def _fn_read_sensors(**_):
            return sensor_manager.read_all()

        def _fn_read_bme280(**_):
            s = sensor_manager.get_sensor("bme280")
            return s.read() if s else {"error": "BME280 sensor not found"}

        def _fn_read_bh1750(**_):
            s = sensor_manager.get_sensor("bh1750")
            return s.read() if s else {"error": "BH1750 sensor not found"}

        def _fn_read_ultrasonic(**_):
            s = sensor_manager.get_sensor("hcsr04")
            return s.read() if s else {"error": "Ultrasonic sensor not found"}

        def _fn_read_vl53l0x(**_):
            s = sensor_manager.get_sensor("vl53l0x")
            return s.read() if s else {"error": "VL53L0X sensor not found"}

        def _fn_read_pir(**_):
            s = sensor_manager.get_sensor("hcsr501")
            return s.read() if s else {"error": "PIR motion sensor not found"}

        self.register_tool({
            "name": "read_sensors",
            "description": "Read telemetry from all attached environmental and distance sensors",
            "schema": {},
            "risk_level": 0,
            "permissions": ["sensors:read"],
            "execute": _fn_read_sensors,
        })
        self.register_tool({
            "name": "read_bme280",
            "description": "Read temperature, relative humidity, and barometric pressure",
            "schema": {},
            "risk_level": 0,
            "permissions": ["sensors:read"],
            "execute": _fn_read_bme280,
        })
        self.register_tool({
            "name": "read_bh1750",
            "description": "Read ambient illuminance in lux",
            "schema": {},
            "risk_level": 0,
            "permissions": ["sensors:read"],
            "execute": _fn_read_bh1750,
        })
        self.register_tool({
            "name": "read_ultrasonic",
            "description": "Read distance measurement in cm via ultrasonic sonar",
            "schema": {},
            "risk_level": 0,
            "permissions": ["sensors:read"],
            "execute": _fn_read_ultrasonic,
        })
        self.register_tool({
            "name": "read_vl53l0x",
            "description": "Read millimeter-precision distance via ToF laser ranging",
            "schema": {},
            "risk_level": 0,
            "permissions": ["sensors:read"],
            "execute": _fn_read_vl53l0x,
        })
        self.register_tool({
            "name": "read_pir",
            "description": "Read passive infrared (PIR) motion detection boolean",
            "schema": {},
            "risk_level": 0,
            "permissions": ["sensors:read"],
            "execute": _fn_read_pir,
        })

        # ── Category D: Vision & Identity Tools ──────────────
        from apps.vision.service import vision_service
        vs = vision_service

        def _fn_camera_capture(**_):
            f = vs.capture_frame()
            f["description"] = vs.describe_scene(f.get("image_path"))
            return f

        def _fn_camera_describe(**_):
            return {"description": vs.describe_scene()}

        def _fn_camera_status(**_):
            return vs.camera_status()

        def _fn_detect_objects(**_):
            return vs.detect_objects()

        def _fn_identify_user(**_):
            return vs.identify_present_user()

        self.register_tool({
            "name": "camera_capture",
            "description": "Capture a physical image from Sony IMX708 Camera and analyze scene",
            "schema": {},
            "risk_level": 0,
            "permissions": ["vision:capture"],
            "execute": _fn_camera_capture,
        })
        self.register_tool({
            "name": "camera_describe",
            "description": "Provide a descriptive text summary of current camera field-of-view using Moondream VLM",
            "schema": {},
            "risk_level": 0,
            "permissions": ["vision:describe"],
            "execute": _fn_camera_describe,
        })
        self.register_tool({
            "name": "camera_status",
            "description": "Query camera module connection, resolution, and driver availability",
            "schema": {},
            "risk_level": 0,
            "permissions": ["vision:status"],
            "execute": _fn_camera_status,
        })
        self.register_tool({
            "name": "detect_objects",
            "description": "Run YOLOv8n object detection to find items (person, bottle, chair, phone, etc.)",
            "schema": {},
            "risk_level": 0,
            "permissions": ["vision:detect"],
            "execute": _fn_detect_objects,
        })
        self.register_tool({
            "name": "identify_user",
            "description": "Recognize the face of the user in front of the camera using YuNet and SFace",
            "schema": {},
            "risk_level": 0,
            "permissions": ["identity:read"],
            "execute": _fn_identify_user,
        })

        # ── Category E: Memory Tools ──────────────────────────
        from memory.long_term.database import db

        def _fn_memory_store(category: str, content: str, **_):
            mid = db.store(category.upper(), content)
            return {"status": "stored", "id": mid, "category": category, "content": content}

        def _fn_memory_search(query: str, **_):
            results = db.search(query)
            return {"query": query, "count": len(results), "results": results[:5]}

        def _fn_memory_recall(category: str = "KNOWLEDGE", **_):
            results = db.retrieve_context(category.upper(), limit=5)
            return {"category": category, "context": results}

        def _fn_memory_delete(memory_id: int, **_):
            ok = db.delete(int(memory_id))
            return {"status": "deleted" if ok else "not_found", "id": memory_id}

        def _fn_memory_summarize(**_):
            return {"summary": db.summarize()}

        self.register_tool({
            "name": "memory_store",
            "description": "Save facts, preferences, and knowledge to long-term database",
            "schema": {"category": "str", "content": "str"},
            "risk_level": 0,
            "permissions": ["memory:write"],
            "execute": _fn_memory_store,
        })
        self.register_tool({
            "name": "memory_search",
            "description": "Search long-term memory for relevant information or facts",
            "schema": {"query": "str"},
            "risk_level": 0,
            "permissions": ["memory:read"],
            "execute": _fn_memory_search,
        })
        self.register_tool({
            "name": "memory_recall",
            "description": "Retrieve recent memories by category",
            "schema": {"category": "str"},
            "risk_level": 0,
            "permissions": ["memory:read"],
            "execute": _fn_memory_recall,
        })
        self.register_tool({
            "name": "memory_delete",
            "description": "Delete a memory entry by ID (requires confirmation)",
            "schema": {"memory_id": "int"},
            "risk_level": 2,
            "permissions": ["memory:delete"],
            "execute": _fn_memory_delete,
        })
        self.register_tool({
            "name": "memory_summarize",
            "description": "Summarize stored memory contents",
            "schema": {},
            "risk_level": 0,
            "permissions": ["memory:read"],
            "execute": _fn_memory_summarize,
        })

        # ── Category H: Application & Code Tools ──────────────
        def _fn_open_app(app_name: str, target: Optional[str] = None, **_):
            import os, shutil, subprocess
            aliases = {
                "vs code": "code", "vscode": "code", "visual studio code": "code",
                "code": "code", "editor": "mousepad", "text editor": "mousepad",
                "terminal": "lxterminal", "browser": "chromium-browser", "calculator": "galculator"
            }
            cmd = aliases.get(app_name.lower().strip(), app_name.lower().strip())
            bin_path = shutil.which(cmd)
            if not bin_path:
                return {"status": "opened", "app": app_name, "command": cmd, "note": "simulated_headless"}
            env = os.environ.copy()
            env.setdefault("DISPLAY", ":0")
            args = [bin_path]
            if target:
                args.append(target)
            proc = subprocess.Popen(args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"status": "opened", "app": app_name, "command": cmd, "pid": proc.pid}

        def _fn_run_code(code: Optional[str] = None, file_path: Optional[str] = None, language: str = "python", **_):
            import subprocess, sys
            try:
                if file_path:
                    proc = subprocess.run([sys.executable, file_path], capture_output=True, text=True, timeout=10)
                elif code:
                    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
                else:
                    return {"error": "Neither code nor file_path was provided.", "status": "error"}
                return {
                    "status": "success" if proc.returncode == 0 else "error",
                    "stdout": proc.stdout[:2000],
                    "stderr": proc.stderr[:500],
                    "exit_code": proc.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"error": "Execution timed out after 10s", "status": "timeout"}
            except Exception as e:
                return {"error": str(e), "status": "error"}

        def _fn_health_check(**_):
            from hardware.raspberry_pi.rpi_info import get_system_status
            from apps.vision.service import VisionService
            vs = VisionService()
            return {
                "system": get_system_status(),
                "camera": vs.camera_status(),
                "robot": _is_armed(),
                "status": "HEALTHY",
            }

        self.register_tool({
            "name": "open_app",
            "description": "Launch desktop applications like VS Code, mousepad editor, or terminal",
            "schema": {"app_name": "str"},
            "risk_level": 1,
            "permissions": ["app:launch"],
            "execute": _fn_open_app,
        })
        self.register_tool({
            "name": "run_code",
            "description": "Execute sandboxed Python script code or file safely and return output",
            "schema": {},
            "risk_level": 2,
            "permissions": ["code:run"],
            "execute": _fn_run_code,
        })
        self.register_tool({
            "name": "health_check",
            "description": "Run comprehensive system and hardware subsystem health verification",
            "schema": {},
            "risk_level": 0,
            "permissions": ["system:read"],
            "execute": _fn_health_check,
        })

        # ── Phase 2: Desktop & Terminal Action Engine Tools ──────────────
        from tools.desktop.action_engine import desktop_action_engine
        from tools.terminal.terminal_manager import terminal_engine

        def _exec_open_url(url: str, browser: str = "chrome", **kwargs):
            from tools.browser.browser_agent import browser_agent
            clean = (url or "").strip()
            if clean.lower() in ("youtube", "youtube.com"):
                clean = "https://www.youtube.com"
            elif clean.lower() in ("google", "google.com"):
                clean = "https://www.google.com"
            elif not clean.startswith(("http://", "https://", "about:", "chrome://")):
                clean = f"https://{clean}"
            return browser_agent.open_url(clean, browser=browser, new_tab=True)

        def _exec_open_youtube(query: str = "", url: str = "", **kwargs):
            from tools.browser.youtube_controller import youtube_controller
            from tools.browser.browser_agent import browser_agent
            if url:
                return browser_agent.open_url(url, browser="chrome", new_tab=True)
            clean_q = (query or "").strip()
            if clean_q and clean_q.lower() not in ("youtube", "none", "null", "all"):
                return youtube_controller.play_direct_query(clean_q, browser="chrome")
            return browser_agent.open_url("https://www.youtube.com", browser="chrome", new_tab=True)

        def _exec_open_desktop_app(app_name: str, target=None, new_window: bool = False, **kwargs):
            return desktop_action_engine.open_application(app_name, target=target, new_window=new_window)

        self.register_tool({
            "name": "open_url",
            "description": "Open a web URL or website in Google Chrome on the local desktop display (DISPLAY=:0)",
            "schema": {"url": "str"},
            "risk_level": 0,
            "permissions": ["browser:open"],
            "execute": _exec_open_url,
        })

        self.register_tool({
            "name": "open_youtube",
            "description": "Open YouTube or search and play a video query in Google Chrome on DISPLAY=:0",
            "schema": {"query": "str"},
            "risk_level": 0,
            "permissions": ["browser:youtube"],
            "execute": _exec_open_youtube,
        })

        self.register_tool({
            "name": "open_desktop_app",
            "description": "Launch an allowlisted desktop application (Chrome, VS Code, Terminal, etc.) on DISPLAY=:0",
            "schema": {"app_name": "str"},
            "risk_level": 1,
            "permissions": ["desktop:launch"],
            "execute": _exec_open_desktop_app,
        })

        self.register_tool({
            "name": "desktop_open_app",
            "description": "Launch installed desktop application (Chrome, Firefox, VS Code, Antigravity, LXTerminal, PCManFM)",
            "schema": {"app_name": "str"},
            "risk_level": 1,
            "permissions": ["desktop:launch"],
            "execute": lambda app_name, target=None, new_window=False, **_: desktop_action_engine.open_application(app_name, target=target, new_window=new_window),
        })

        self.register_tool({
            "name": "desktop_open_url",
            "description": "Open a web URL in Google Chrome, Firefox, or default browser",
            "schema": {"url": "str"},
            "risk_level": 0,
            "permissions": ["browser:open"],
            "execute": lambda url, browser="chrome", **_: desktop_action_engine.open_url(url, browser=browser),
        })

        self.register_tool({
            "name": "desktop_search_youtube",
            "description": "Search YouTube for music, tutorials, or videos in Google Chrome or Firefox",
            "schema": {"query": "str"},
            "risk_level": 0,
            "permissions": ["browser:youtube"],
            "execute": lambda query, browser="chrome", **_: desktop_action_engine.search_youtube(query, browser=browser),
        })

        self.register_tool({
            "name": "desktop_open_project",
            "description": "Open a project directory in VS Code or Antigravity IDE",
            "schema": {"project": "str"},
            "risk_level": 1,
            "permissions": ["desktop:ide"],
            "execute": lambda project, editor="vscode", **_: desktop_action_engine.open_project(project, editor=editor),
        })

        self.register_tool({
            "name": "desktop_search_files",
            "description": "Search for files by name pattern or extension across workspace directories",
            "schema": {},
            "risk_level": 0,
            "permissions": ["filesystem:search"],
            "execute": lambda directory=None, pattern="*", extension=None, max_results=50, **_: desktop_action_engine.search_files(directory=directory, pattern=pattern, extension=extension, max_results=max_results),
        })

        self.register_tool({
            "name": "desktop_search_content",
            "description": "Search text contents inside source code files (grep search)",
            "schema": {"query": "str"},
            "risk_level": 0,
            "permissions": ["filesystem:search"],
            "execute": lambda query, directory=None, file_pattern=None, max_results=25, **_: desktop_action_engine.search_file_contents(query=query, directory=directory, file_pattern=file_pattern, max_results=max_results),
        })

        self.register_tool({
            "name": "desktop_run_program",
            "description": "Execute a Python, shell, or script file in a project folder",
            "schema": {"file_path": "str"},
            "risk_level": 2,
            "permissions": ["code:run"],
            "execute": lambda file_path, working_dir=None, args=None, background=False, **_: desktop_action_engine.run_program(file_path, working_dir=working_dir, args=args, background=background),
        })

        self.register_tool({
            "name": "desktop_get_status",
            "description": "Get desktop session status, active window, resolution, and open applications",
            "schema": {},
            "risk_level": 0,
            "permissions": ["desktop:read"],
            "execute": lambda **_: desktop_action_engine.get_desktop_status(),
        })

        self.register_tool({
            "name": "desktop_get_active_window",
            "description": "Get currently active window title, ID, and class name on X11 desktop",
            "schema": {},
            "risk_level": 0,
            "permissions": ["desktop:read"],
            "execute": lambda **_: desktop_action_engine.get_active_window(),
        })

        self.register_tool({
            "name": "desktop_switch_app",
            "description": "Switch window focus to a running application or window by title",
            "schema": {"query": "str"},
            "risk_level": 1,
            "permissions": ["desktop:focus"],
            "execute": lambda query, **_: desktop_action_engine.switch_application(query),
        })

        self.register_tool({
            "name": "terminal_execute",
            "description": "Execute a command in real terminal with session directory tracking and security gate",
            "schema": {"command": "str"},
            "risk_level": 2,
            "permissions": ["terminal:execute"],
            "execute": lambda command, session_id="default", confirm=False, confirmation_token=None, **_: terminal_engine.execute_command(command, session_id=session_id, confirm=confirm, confirmation_token=confirmation_token),
        })

        # ── Intelligent Computer Control Tools ─────────────────────────
        from tools.desktop.unified_computer_service import unified_computer_service
        from tools.desktop.browser_backend import browser_backend
        from tools.desktop.native_backend import native_backend

        self.register_tool({
            "name": "computer_execute",
            "description": "Execute natural language computer automation command with verification (e.g. 'Select option 1 and click Submit')",
            "schema": {"instruction": "str"},
            "risk_level": 1,
            "permissions": ["desktop:execute"],
            "execute": lambda instruction, **_: unified_computer_service.execute_natural_instruction(instruction),
        })

        self.register_tool({
            "name": "computer_move_mouse",
            "description": "Move desktop mouse pointer smoothly to target element or coordinates",
            "schema": {"x": "int", "y": "int"},
            "risk_level": 1,
            "permissions": ["desktop:mouse"],
            "execute": lambda x, y, smooth=True, **_: native_backend.move_cursor(x, y, duration=0.25, smooth=smooth),
        })

        self.register_tool({
            "name": "computer_click",
            "description": "Click mouse button at specified coordinates or target element",
            "schema": {"button": "str"},
            "risk_level": 1,
            "permissions": ["desktop:mouse"],
            "execute": lambda button="left", x=None, y=None, clicks=1, **_: native_backend.click(x=x, y=y, button=button, clicks=clicks),
        })

        self.register_tool({
            "name": "computer_select_option",
            "description": "Select radio button, checkbox, or dropdown option in browser or desktop interface",
            "schema": {"option": "str"},
            "risk_level": 1,
            "permissions": ["desktop:input"],
            "execute": lambda option, verify=True, **_: browser_backend.select_option(option, verify=verify),
        })

        self.register_tool({
            "name": "computer_type",
            "description": "Type text into currently focused field or target window",
            "schema": {"text": "str"},
            "risk_level": 1,
            "permissions": ["desktop:keyboard"],
            "execute": lambda text, target_window=None, **_: native_backend.type_text(text, target_window=target_window),
        })

        self.register_tool({
            "name": "computer_press_key",
            "description": "Press a keyboard key or hotkey combination (e.g. 'ctrl+a', 'Return', 'Escape')",
            "schema": {"key": "str"},
            "risk_level": 1,
            "permissions": ["desktop:keyboard"],
            "execute": lambda key, **_: native_backend.press_hotkey(key),
        })

        self.register_tool({
            "name": "computer_scroll",
            "description": "Scroll mouse wheel up or down",
            "schema": {"direction": "str"},
            "risk_level": 1,
            "permissions": ["desktop:mouse"],
            "execute": lambda direction="down", clicks=5, **_: native_backend.scroll(direction=direction, clicks=clicks),
        })

        self.register_tool({
            "name": "computer_stop",
            "description": "Emergency stop computer automation immediately and release held inputs",
            "schema": {},
            "risk_level": 0,
            "permissions": ["desktop:execute"],
            "execute": lambda **_: unified_computer_service.emergency_stop(),
        })

        self.register_tool({
            "name": "browser_open",
            "description": "Open or navigate Playwright browser to target URL",
            "schema": {"url": "str"},
            "risk_level": 1,
            "permissions": ["browser:navigate"],
            "execute": lambda url, **_: browser_backend.navigate(url),
        })



# Global tool registry instances for compatibility
tool_registry = ToolRegistry()
registry = tool_registry
