import inspect
import json
import logging
from pathlib import Path
import re
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Dict, List, Optional, Set

from .models import Agent, Capability, CheckpointEntry, Task, TaskState
from .adapters import RateLimitError

logger = logging.getLogger("JARVIS.Developer.Core")

_SECRET = re.compile(r"(?i)(api[_-]?key|token|password|secret)(\s*[=:]\s*)[^\s,;]+")

def redact(value: Any) -> str:
    return _SECRET.sub(r"\1\2[REDACTED]", str(value))


class Orchestrator:
    """
    SQLite-backed dependency queue with:
    - Persistent checkpointing
    - Interruption recovery
    - Dynamic agent routing & rate-limit failover
    - Concurrency and dependency gating
    - Autonomous queue processing
    """
    def __init__(self, database="orchestration.sqlite3", max_concurrency=4):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, Agent] = {}
        self._lock = threading.RLock()
        self._cancelled_tasks: Set[str] = set()
        self.max_concurrency = max_concurrency
        self._scheduler_running = False
        self._scheduler_thread: Optional[threading.Thread] = None

        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, task_id TEXT, event TEXT)")
            db.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "task_id TEXT NOT NULL, "
                "step INTEGER NOT NULL, "
                "diff TEXT, "
                "status TEXT, "
                "created_at REAL NOT NULL, "
                "summary TEXT)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS reviews ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "task_id TEXT NOT NULL, "
                "reviewer_id TEXT NOT NULL, "
                "status TEXT NOT NULL, "
                "score REAL, "
                "notes TEXT, "
                "created_at REAL NOT NULL)"
            )

        # Recover any tasks left in RUNNING state on startup
        self.recover_interrupted_tasks()

    def register(self, agent: Agent):
        if not agent.agent_id or agent.agent_id in self.agents:
            raise ValueError("agent id must be nonempty and unique")
        self.agents[agent.agent_id] = agent

    def create_task(self, task: Task) -> Task:
        if not isinstance(task, Task) or not task.prompt.strip() or task.timeout <= 0 or task.max_retries < 0:
            raise ValueError("invalid task")
        self._validate_owned_paths(task.owned_paths)
        with sqlite3.connect(self.database) as db:
            if db.execute("SELECT 1 FROM tasks WHERE id=?", (task.task_id,)).fetchone():
                raise ValueError("duplicate task id")
            for dep in task.dependencies:
                if not db.execute("SELECT 1 FROM tasks WHERE id=?", (dep,)).fetchone():
                    raise ValueError("unknown dependency")
            for (raw_data,) in db.execute("SELECT data FROM tasks"):
                existing = json.loads(raw_data)
                if existing.get("state") not in {TaskState.PENDING.value, TaskState.READY.value, TaskState.RUNNING.value}:
                    continue
                if self._paths_conflict(task.owned_paths, existing.get("owned_paths", [])):
                    raise ValueError("owned paths conflict with an active task")
            self._save(db, task, "created")
        return task

    @staticmethod
    def _validate_owned_paths(paths):
        for raw_path in paths:
            path = Path(raw_path)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("owned paths must be safe relative paths")

    @staticmethod
    def _paths_conflict(left, right):
        for raw_left in left:
            left_path = Path(raw_left)
            for raw_right in right:
                right_path = Path(raw_right)
                if left_path == right_path or left_path in right_path.parents or right_path in left_path.parents:
                    return True
        return False

    def _save(self, db: sqlite3.Connection, task: Task, event: str):
        data = {
            k: (v.value if isinstance(v, TaskState) else list(v) if isinstance(v, tuple) else v)
            for k, v in vars(task).items()
        }
        db.execute("INSERT OR REPLACE INTO tasks(id,data) VALUES(?,?)", (task.task_id, json.dumps(data)))
        db.execute("INSERT INTO audit(task_id,event) VALUES(?,?)", (task.task_id, redact(event)))

    def get_task(self, task_id: str) -> Optional[Task]:
        with sqlite3.connect(self.database) as db:
            row = db.execute("SELECT data FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        data["state"] = TaskState(data["state"])
        data["dependencies"] = tuple(data.get("dependencies", ()))
        data["capabilities"] = tuple(data.get("capabilities", ()))
        data["owned_paths"] = tuple(data.get("owned_paths", ()))
        data["failover_history"] = tuple(data.get("failover_history", ()))
        data.setdefault("review", None)
        data.setdefault("verification", None)

        valid_keys = inspect.signature(Task).parameters.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return Task(**filtered)

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self.get_task(task_id)
            if task is None or task.state in (TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED):
                return False
            self._cancelled_tasks.add(task_id)
            task.state = TaskState.CANCELLED
            with sqlite3.connect(self.database) as db:
                self._save(db, task, "cancelled")
            return True

    def discover(self, root: Path | str) -> List[str]:
        """Return relative file paths only; no file content is read."""
        r = Path(root)
        return sorted(p.relative_to(r).as_posix() for p in r.rglob("*") if p.is_file())

    def save_checkpoint(self, task_id: str, diff: str = "", status: str = "", summary: str = "") -> CheckpointEntry:
        """Persist a structured checkpoint for a task to SQLite."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        with sqlite3.connect(self.database) as db:
            row = db.execute("SELECT MAX(step) FROM checkpoints WHERE task_id=?", (task_id,)).fetchone()
            step = (row[0] or 0) + 1 if (row and row[0] is not None) else 1
            now = time.time()
            cur = db.execute(
                "INSERT INTO checkpoints(task_id, step, diff, status, created_at, summary) VALUES (?,?,?,?,?,?)",
                (task_id, step, redact(diff), status, now, summary),
            )
            cid = cur.lastrowid
            task.checkpoint = status
            self._save(db, task, f"checkpoint_step_{step}")

        return CheckpointEntry(
            task_id=task_id,
            step=step,
            status=status,
            diff=diff,
            summary=summary,
            created_at=now,
            id=cid,
        )

    def get_checkpoints(self, task_id: str) -> List[Dict[str, Any]]:
        """Retrieve all recorded checkpoints for a task."""
        with sqlite3.connect(self.database) as db:
            rows = db.execute(
                "SELECT id, step, diff, status, created_at, summary FROM checkpoints WHERE task_id=? ORDER BY step ASC",
                (task_id,)
            ).fetchall()
        return [
            {
                "id": r[0],
                "task_id": task_id,
                "step": r[1],
                "diff": r[2],
                "status": r[3],
                "created_at": r[4],
                "summary": r[5],
            }
            for r in rows
        ]

    def recover_interrupted_tasks(self) -> List[str]:
        """Identify tasks left in RUNNING state across restarts and transition them to INTERRUPTED."""
        recovered = []
        with sqlite3.connect(self.database) as db:
            rows = db.execute("SELECT id, data FROM tasks").fetchall()
            for (tid, raw_data) in rows:
                try:
                    data = json.loads(raw_data)
                    if data.get("state") == TaskState.RUNNING.value:
                        data["state"] = TaskState.INTERRUPTED.value
                        data["error"] = "Orchestrator restarted while task was executing"
                        db.execute("INSERT OR REPLACE INTO tasks(id,data) VALUES(?,?)", (tid, json.dumps(data)))
                        db.execute("INSERT INTO audit(task_id,event) VALUES(?,?)", (tid, "interrupted_by_restart"))
                        recovered.append(tid)
                except Exception:
                    pass
        if recovered:
            logger.info("Recovered %d interrupted tasks: %s", len(recovered), recovered)
        return recovered

    def resume_task(self, task_id: str) -> Task:
        """Resume an interrupted, failed, or cancelled task from its preserved checkpoint/worktree."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.state not in (TaskState.INTERRUPTED, TaskState.FAILED, TaskState.CANCELLED):
            raise RuntimeError(f"Cannot resume task in state {task.state}")

        task.state = TaskState.PENDING
        task.error = None
        self._cancelled_tasks.discard(task_id)

        with sqlite3.connect(self.database) as db:
            self._save(db, task, "resumed")
        return task

    def select_agent(self, task: Task, exclude_agent_ids: Optional[Set[str]] = None) -> Optional[Agent]:
        """Intelligently select matching agent with rate-limit avoidance and failover."""
        exclude = exclude_agent_ids or set()

        # 1. Direct explicit agent request
        if getattr(task, "agent_id", None) and task.agent_id in self.agents and task.agent_id not in exclude:
            ag = self.agents[task.agent_id]
            adapter = getattr(ag, "adapter", None)
            if hasattr(adapter, "rate_limited_until") and adapter.rate_limited_until and time.time() < adapter.rate_limited_until:
                logger.warning("Requested agent %s is currently rate-limited; looking for matching failover", task.agent_id)
            else:
                return ag

        # 2. Dynamic matching by capabilities
        matching = [
            a for a in self.agents.values()
            if a.agent_id not in exclude and set(task.capabilities) <= {c.name for c in a.capabilities}
        ]
        if not matching:
            return None

        # Filter out rate-limited agents
        healthy = [
            a for a in matching
            if not (hasattr(a.adapter, "rate_limited_until") and a.adapter.rate_limited_until and time.time() < a.adapter.rate_limited_until)
        ]
        candidates = healthy if healthy else matching
        return candidates[0]

    def run(self, task_id: str) -> Task:
        """Execute a single task with dependency checks, retries, and dynamic agent failover."""
        with self._lock:
            task = self.get_task(task_id)
            if task is None:
                raise ValueError("unknown task")
            if task.state in (TaskState.SUCCEEDED, TaskState.CANCELLED, TaskState.MERGED):
                return task
            if task.state == TaskState.RUNNING:
                raise RuntimeError("task is already running")
            for dep in task.dependencies:
                dependency = self.get_task(dep)
                if dependency is None or dependency.state != TaskState.SUCCEEDED:
                    raise RuntimeError("dependencies are not complete")

            initial_agent = self.select_agent(task)
            if initial_agent is None:
                raise RuntimeError("no matching agent")

            task.agent_id = initial_agent.agent_id
            task.state = TaskState.RUNNING
            with sqlite3.connect(self.database) as db:
                self._save(db, task, "running")

        tried_agents: Set[str] = set()
        max_agent_swaps = max(1, len(self.agents))
        agent_swaps = 0

        while agent_swaps < max_agent_swaps:
            current_agent = self.select_agent(task, exclude_agent_ids=tried_agents)
            if not current_agent:
                break
            task.agent_id = current_agent.agent_id

            rate_limit_occurred = False
            for attempt in range(task.max_retries + 1):
                task.attempts += 1
                pool = ThreadPoolExecutor(max_workers=1)
                future = pool.submit(current_agent.adapter.execute, task)
                timed_out = False
                try:
                    result = future.result(timeout=task.timeout)
                    if self._is_cancelled(task.task_id):
                        task.state = TaskState.CANCELLED
                        self._cancel_adapter(current_agent.adapter)
                        break
                    if isinstance(result, str):
                        if not result.strip():
                            raise ValueError("agent produced invalid or empty output")
                    elif isinstance(result, dict):
                        result_status = result.get("status")
                        if result_status == "error":
                            err_msg = result.get("message", "agent execution failed")
                            if "usage limit" in err_msg.lower() or "rate limit" in err_msg.lower():
                                raise RateLimitError(err_msg)
                            raise RuntimeError(err_msg)
                        if not isinstance(result_status, str) or not result_status.strip():
                            raise ValueError("agent produced invalid or empty output")
                    else:
                        raise ValueError("agent produced invalid or empty output")
                    task.result = result
                    task.state = TaskState.SUCCEEDED
                    task.error = None
                    break
                except RateLimitError as rl_err:
                    logger.warning("Agent %s rate-limited: %s. Initiating failover.", current_agent.agent_id, rl_err)
                    tried_agents.add(current_agent.agent_id)
                    task.failover_history = task.failover_history + (f"failover_from_{current_agent.agent_id}",)
                    task.error = redact(rl_err)
                    self._cancel_adapter(current_agent.adapter)
                    rate_limit_occurred = True
                    break  # Swap to next capable agent
                except TimeoutError:
                    timed_out = True
                    task.error = f"agent exceeded timeout of {task.timeout}s"
                    self._cancel_adapter(current_agent.adapter)
                except KeyboardInterrupt:
                    task.error = "agent execution interrupted"
                    self._cancel_adapter(current_agent.adapter)
                    task.state = TaskState.FAILED
                    break
                except Exception as exc:
                    err_str = str(exc)
                    if "usage limit" in err_str.lower() or "rate limit" in err_str.lower():
                        logger.warning("Agent %s usage limited: %s. Failover.", current_agent.agent_id, err_str)
                        tried_agents.add(current_agent.agent_id)
                        task.failover_history = task.failover_history + (f"failover_from_{current_agent.agent_id}",)
                        task.error = redact(err_str)
                        self._cancel_adapter(current_agent.adapter)
                        rate_limit_occurred = True
                        break
                    task.error = redact(exc)
                    if attempt == task.max_retries:
                        task.state = TaskState.FAILED
                finally:
                    pool.shutdown(wait=not timed_out, cancel_futures=True)

                if self._is_cancelled(task.task_id):
                    task.state = TaskState.CANCELLED
                    break

            if task.state in (TaskState.SUCCEEDED, TaskState.CANCELLED):
                break
            if rate_limit_occurred:
                agent_swaps += 1
                continue
            break

        if task.state == TaskState.RUNNING:
            task.state = TaskState.FAILED
        with sqlite3.connect(self.database) as db:
            self._save(db, task, task.state.value)
        return task

    def run_concurrent(self, task_ids: List[str]) -> List[Task]:
        """Execute multiple independent tasks in parallel up to max_concurrency."""
        if not task_ids:
            return []
        workers = min(len(task_ids), self.max_concurrency)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(self.run, task_ids))

    def process_pending_queue(self) -> Dict[str, Any]:
        """Inspect all pending/ready tasks, evaluate dependency graphs & path conflicts, and run ready tasks."""
        with sqlite3.connect(self.database) as db:
            rows = db.execute("SELECT data FROM tasks").fetchall()

        all_tasks = []
        for (r,) in rows:
            try:
                all_tasks.append(json.loads(r))
            except Exception:
                pass

        task_map = {t["task_id"]: t for t in all_tasks}
        ready_task_ids = []
        active_owned_paths: List[str] = []

        # Find paths from currently running tasks
        for t in all_tasks:
            if t.get("state") == TaskState.RUNNING.value:
                active_owned_paths.extend(t.get("owned_paths", []))

        # Check pending/ready tasks
        for t in all_tasks:
            if t.get("state") in (TaskState.PENDING.value, TaskState.READY.value):
                deps_met = True
                for dep in t.get("dependencies", []):
                    dep_task = task_map.get(dep)
                    if not dep_task or dep_task.get("state") != TaskState.SUCCEEDED.value:
                        deps_met = False
                        break
                if not deps_met:
                    continue

                t_paths = t.get("owned_paths", [])
                if self._paths_conflict(t_paths, active_owned_paths):
                    continue

                ready_task_ids.append(t["task_id"])
                active_owned_paths.extend(t_paths)

        executed = []
        if ready_task_ids:
            batch = ready_task_ids[:self.max_concurrency]
            executed = self.run_concurrent(batch)

        return {
            "ready_count": len(ready_task_ids),
            "executed_count": len(executed),
            "task_ids": [t.task_id for t in executed],
            "states": {t.task_id: t.state.value for t in executed},
        }

    def _is_cancelled(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._cancelled_tasks

    @staticmethod
    def _cancel_adapter(adapter):
        cancel = getattr(adapter, "cancel", None) or getattr(adapter, "cancel_task", None)
        if cancel:
            try:
                cancel()
            except Exception:
                pass
