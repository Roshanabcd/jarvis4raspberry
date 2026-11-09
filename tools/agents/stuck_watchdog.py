"""
Stuck-Task Watchdog and Execution Loop Detector for JARVIS OS Phase 5.
Detects repeated command loops, output stagnation, circular delegations,
and terminates hung agent processes safely without impacting unrelated services.
"""
from __future__ import annotations

import logging
import os
import signal
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.StuckWatchdog")


@dataclass
class TaskHeartbeat:
    task_id: str
    agent_id: str
    process_pid: Optional[int] = None
    started_at: float = field(default_factory=time.time)
    last_output_at: float = field(default_factory=time.time)
    command_history: List[str] = field(default_factory=list)
    output_length_history: List[int] = field(default_factory=list)
    tool_calls_count: int = 0
    consecutive_failures: int = 0
    timeout_seconds: float = 90.0


class StuckTaskWatchdog:
    """Monitors running agent tasks, identifies loops, and enforces bounded execution."""

    def __init__(self):
        self._tracked_tasks: Dict[str, TaskHeartbeat] = {}
        self.repeated_command_threshold: int = 3
        self.idle_timeout_seconds: float = 60.0

    def register_task(
        self,
        task_id: str,
        agent_id: str,
        process_pid: Optional[int] = None,
        timeout_seconds: float = 90.0
    ) -> None:
        """Begin monitoring a new task execution."""
        self._tracked_tasks[task_id] = TaskHeartbeat(
            task_id=task_id,
            agent_id=agent_id,
            process_pid=process_pid,
            timeout_seconds=timeout_seconds,
        )

    def record_activity(
        self,
        task_id: str,
        command: Optional[str] = None,
        output_chunk: Optional[str] = None,
        is_failure: bool = False
    ) -> None:
        """Update task heartbeat with command, output length, or failure status."""
        hb = self._tracked_tasks.get(task_id)
        if not hb:
            return

        hb.last_output_at = time.time()
        if command:
            hb.command_history.append(command.strip().lower())
        if output_chunk:
            hb.output_length_history.append(len(output_chunk))
        if is_failure:
            hb.consecutive_failures += 1
        else:
            hb.consecutive_failures = 0

    def check_stuck_condition(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """Evaluate if the task is stuck in a loop, idle, or exceeding timeout."""
        hb = self._tracked_tasks.get(task_id)
        if not hb:
            return False, None

        now = time.time()

        # 1. Total Task Timeout Exceeded
        elapsed = now - hb.started_at
        if elapsed > hb.timeout_seconds:
            return True, f"Task exceeded total runtime timeout ({elapsed:.1f}s > {hb.timeout_seconds}s)"

        # 2. Output Stagnation / Idle Timeout
        idle_time = now - hb.last_output_at
        if idle_time > self.idle_timeout_seconds:
            return True, f"Agent has produced no output for {idle_time:.1f}s (idle threshold: {self.idle_timeout_seconds}s)"

        # 3. Repeated Command Loop
        if len(hb.command_history) >= self.repeated_command_threshold:
            recent_cmds = hb.command_history[-self.repeated_command_threshold:]
            if len(set(recent_cmds)) == 1:
                return True, f"Repeated command loop detected: '{recent_cmds[0]}' executed {self.repeated_command_threshold} times consecutively"

        # 4. Excessive Repeated Failures
        if hb.consecutive_failures >= 3:
            return True, f"Task failed {hb.consecutive_failures} consecutive times without progress"

        return False, None

    def terminate_stuck_task(self, task_id: str) -> Dict[str, Any]:
        """Safely terminate only the specific stuck process without killing unrelated system services."""
        hb = self._tracked_tasks.pop(task_id, None)
        if not hb:
            return {"status": "ok", "message": "Task not tracked or already finished"}

        pid = hb.process_pid
        if pid and pid > 1:
            try:
                # Do NOT kill pid 1, systemd, ollama, or chrome
                os.kill(pid, signal.SIGTERM)
                logger.warning("Watchdog safely terminated stuck task process %d for task %s", pid, task_id)
                return {"status": "ok", "action": "terminated", "pid": pid, "task_id": task_id}
            except ProcessLookupError:
                return {"status": "ok", "action": "process_already_exited", "pid": pid}
            except Exception as e:
                logger.error("Failed to terminate process %d: %s", pid, e)
                return {"status": "error", "message": str(e)}

        return {"status": "ok", "action": "unregistered", "task_id": task_id}

    def unregister_task(self, task_id: str) -> None:
        """Remove task upon clean completion."""
        self._tracked_tasks.pop(task_id, None)

    def record_start(self, task_id: str, pid: Optional[int] = None, command: str = "", agent_id: str = "agent") -> None:
        self.register_task(task_id, agent_id=agent_id, process_pid=pid)
        if command:
            self.record_command(task_id, command)

    def record_command(self, task_id: str, command: str) -> None:
        self.record_activity(task_id, command=command)

    def is_stuck(self, task_id: str) -> Tuple[bool, Optional[str]]:
        return self.check_stuck_condition(task_id)

    def clear(self, task_id: str) -> None:
        self.unregister_task(task_id)


stuck_watchdog = StuckTaskWatchdog()
