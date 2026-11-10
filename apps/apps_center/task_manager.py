"""
JARVIS OS — Application Background Task Manager.
Coordinates background jobs, asynchronous execution, task state transitions,
progress reporting, cancellation, and user authorization boundaries.
"""

import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from apps.apps_center.database import apps_db
from apps.apps_center.models import AppTaskRecord, TaskStatus
from apps.apps_center.resource_manager import resource_manager

logger = logging.getLogger("JARVIS.AppsCenter.TaskManager")


class AppTaskManager:
    """Thread-safe background task executor for Apps Center modules."""
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppTaskManager, cls).__new__(cls)
                cls._instance._running_threads: Dict[str, threading.Thread] = {}
                cls._instance._cancellation_tokens: Dict[str, threading.Event] = {}
            return cls._instance

    def submit_task(
        self,
        app_id: str,
        user_id: str,
        task_type: str,
        worker_func: Callable[..., Any],
        resource_profile: str = "medium",
        payload: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Submit a new background job with admission control and user binding.
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = time.time()

        task_record = {
            "task_id": task_id,
            "app_id": app_id,
            "user_id": user_id,
            "task_type": task_type,
            "status": TaskStatus.QUEUED.value,
            "progress_pct": 0,
            "message": "Task queued for execution",
            "payload_json": payload or {},
            "result_json": {},
            "error": None,
            "created_at": now,
            "started_at": None,
            "completed_at": None,
        }
        apps_db.save_task(task_record)

        cancel_event = threading.Event()
        with self._lock:
            self._cancellation_tokens[task_id] = cancel_event

        def runner():
            logger.info("Executing task %s for app %s (user: %s)", task_id, app_id, user_id)
            admitted = resource_manager.acquire_job(resource_profile)
            if not admitted:
                task_record["status"] = TaskStatus.FAILED.value
                task_record["error"] = "System resource limits exceeded on Raspberry Pi 5"
                task_record["completed_at"] = time.time()
                apps_db.save_task(task_record)
                return

            task_record["status"] = TaskStatus.RUNNING.value
            task_record["started_at"] = time.time()
            task_record["message"] = "Task is running..."
            apps_db.save_task(task_record)

            try:
                if cancel_event.is_set():
                    task_record["status"] = TaskStatus.CANCELLED.value
                    task_record["completed_at"] = time.time()
                    apps_db.save_task(task_record)
                    return

                # Pass update callback if accepted
                res = worker_func(cancel_event=cancel_event, *args, **kwargs)
                task_record["status"] = TaskStatus.COMPLETED.value
                task_record["progress_pct"] = 100
                task_record["result_json"] = res if isinstance(res, dict) else {"output": res}
                task_record["message"] = "Task completed successfully"
            except Exception as e:
                logger.error("Task %s failed: %s", task_id, e)
                task_record["status"] = TaskStatus.FAILED.value
                task_record["error"] = str(e)
                task_record["message"] = f"Failed: {e}"
            finally:
                resource_manager.release_job(resource_profile)
                task_record["completed_at"] = time.time()
                apps_db.save_task(task_record)
                with self._lock:
                    self._running_threads.pop(task_id, None)
                    self._cancellation_tokens.pop(task_id, None)

        thread = threading.Thread(target=runner, name=f"Task-{task_id}", daemon=True)
        with self._lock:
            self._running_threads[task_id] = thread
        thread.start()

        return task_record

    def cancel_task(self, task_id: str, user_id: str, is_admin: bool = False) -> bool:
        """Cancel a running or queued task, checking user ownership."""
        task = apps_db.get_task(task_id)
        if not task:
            return False

        if not is_admin and task.get("user_id") != user_id:
            logger.warning("Unauthorized task cancellation attempt: user %s tried to cancel task %s owned by %s",
                           user_id, task_id, task.get("user_id"))
            return False

        with self._lock:
            event = self._cancellation_tokens.get(task_id)
            if event:
                event.set()
        task["status"] = TaskStatus.CANCELLED.value
        task["message"] = "Task cancelled by user"
        task["completed_at"] = time.time()
        apps_db.save_task(task)
        return True

    def get_task_status(self, task_id: str, user_id: str, is_admin: bool = False) -> Optional[Dict[str, Any]]:
        """Get task status with user isolation enforcement."""
        task = apps_db.get_task(task_id)
        if not task:
            return None
        if not is_admin and task.get("user_id") != user_id:
            return None
        return task

    def list_user_tasks(self, user_id: str, app_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List tasks owned strictly by user_id."""
        return apps_db.list_tasks_for_user(user_id=user_id, app_id=app_id, limit=limit)


# Global singleton instance
task_manager = AppTaskManager()
