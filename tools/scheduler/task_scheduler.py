"""
JARVIS Automation Scheduler
Supports cron-style scheduling with SQLite-backed task storage.
"""
import sqlite3
import json
import logging
import threading
import time
import re
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("JARVIS.Scheduler")


def _parse_daily_time(cron_expr: str) -> Optional[tuple]:
    """
    Parse simple daily HH:MM format.
    Returns (hour, minute) or None if not matched.
    """
    m = re.match(r'^(\d{1,2}):(\d{2})$', cron_expr.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


class TaskScheduler:
    """
    Lightweight in-process task scheduler.
    Stores tasks in SQLite. Checks due tasks every 60 seconds.
    Supports: daily HH:MM, interval Xs, once (run immediately once).
    """

    def __init__(self, db_path: str = "jarvis_memory.db") -> None:
        self.db_path = db_path
        self._callbacks: Dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT UNIQUE NOT NULL,
                    description TEXT,
                    schedule    TEXT NOT NULL,
                    command     TEXT NOT NULL,
                    args        TEXT DEFAULT '[]',
                    enabled     INTEGER DEFAULT 1,
                    last_run    REAL,
                    run_count   INTEGER DEFAULT 0,
                    created_at  REAL NOT NULL
                )
            """)

    def schedule_task(self, name: str, schedule: str,
                      command: str, args: Optional[List] = None,
                      description: str = "") -> int:
        """
        Schedule a task.
        schedule: 'HH:MM' (daily), 'every Xs' (interval in seconds), 'once'
        command: registered callback name or shell command key
        """
        args = args or []
        now = time.time()
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT OR REPLACE INTO scheduled_tasks
                   (name, description, schedule, command, args, enabled, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (name, description, schedule, command, json.dumps(args), now)
            )
            task_id = cur.lastrowid
        logger.info(f"Scheduled task '{name}' ({schedule}) id={task_id}")
        return str(task_id)

    def register_callback(self, name: str, fn: Callable) -> None:
        """Register a Python function that can be called by scheduled tasks."""
        self._callbacks[name] = fn

    def _is_due(self, task: sqlite3.Row) -> bool:
        schedule = task["schedule"]
        last_run = task["last_run"] or 0.0
        now = time.time()

        parsed = _parse_daily_time(schedule)
        if parsed:
            import datetime
            h, m = parsed
            today = datetime.date.today()
            target_ts = datetime.datetime.combine(
                today, datetime.time(h, m)
            ).timestamp()
            return now >= target_ts and last_run < target_ts

        if schedule.startswith("every ") and schedule.endswith("s"):
            try:
                interval = int(schedule[6:-1])
                return (now - last_run) >= interval
            except ValueError:
                pass

        if schedule == "once":
            return last_run == 0.0

        return False

    def run_due_tasks(self) -> List[str]:
        """Check all enabled tasks and run any that are due. Returns list of run task names."""
        run_names = []
        with self._get_conn() as conn:
            tasks = conn.execute(
                "SELECT * FROM scheduled_tasks WHERE enabled = 1"
            ).fetchall()

        for task in tasks:
            if self._is_due(task):
                try:
                    cmd = task["command"]
                    args = json.loads(task["args"] or "[]")
                    logger.info(f"Running scheduled task: {task['name']}")
                    if cmd in self._callbacks:
                        self._callbacks[cmd](*args)
                    else:
                        logger.warning(f"No callback registered for '{cmd}'")
                    with self._get_conn() as conn:
                        conn.execute(
                            "UPDATE scheduled_tasks SET last_run=?, run_count=run_count+1 WHERE id=?",
                            (time.time(), task["id"])
                        )
                    run_names.append(task["name"])
                except Exception as e:
                    logger.error(f"Scheduled task '{task['name']}' failed: {e}")
        return run_names

    def list_tasks(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM scheduled_tasks ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def pause_task(self, task_id: int) -> None:
        with self._get_conn() as conn:
            conn.execute("UPDATE scheduled_tasks SET enabled=0 WHERE id=?", (task_id,))
        logger.info(f"Paused task id={task_id}")
        return True

    def resume_task(self, task_id: int) -> None:
        with self._get_conn() as conn:
            conn.execute("UPDATE scheduled_tasks SET enabled=1 WHERE id=?", (task_id,))
        logger.info(f"Resumed task id={task_id}")
        return True

    def delete_task(self, task_id: int) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM scheduled_tasks WHERE id=?", (task_id,))
        logger.info(f"Deleted task id={task_id}")
        return True

    def start(self) -> None:
        """Start background scheduler loop."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="Scheduler")
        self._thread.start()
        logger.info("Scheduler started.")

    def stop(self) -> None:
        self._running = False
        logger.info("Scheduler stopped.")

    def _loop(self) -> None:
        while self._running:
            try:
                ran = self.run_due_tasks()
                if ran:
                    logger.info(f"Ran tasks: {ran}")
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            time.sleep(30)  # Check every 30s
