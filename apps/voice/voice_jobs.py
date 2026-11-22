"""Bounded voice jobs with optional private, durable metadata for JARVIS OS.

Tracks asynchronous speech synthesis and audio playback jobs with explicit job IDs,
status lifecycle, error capture, and safe cancellation to prevent overlapping playback.
"""
from __future__ import annotations

import collections
import fcntl
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("JARVIS.Voice.Jobs")

MAX_JOB_HISTORY = 100
JOB_STATUSES = frozenset({"queued", "synthesizing", "playing", "completed", "cancelled", "failed"})
TERMINAL_STATUSES = frozenset({"completed", "cancelled", "failed"})
STORE_VERSION = 1
MAX_STORE_BYTES = 1024 * 1024
INTERRUPTED_ERROR = "Voice delivery interrupted by process restart; not replayed"
REDACTED_ERROR = "Voice delivery failed; details were not retained"


def default_store_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "voice_jobs" / "history.json"


class VoiceJob(BaseModel):
    job_id: str
    text: str
    status: str = "queued"  # queued, synthesizing, playing, completed, cancelled, failed
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    audio_id: Optional[str] = None
    audio_url: Optional[str] = None
    provider: Optional[str] = None
    is_cloned: bool = False
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    generation: int = 0
    turn_id: Optional[str] = None
    message_id: Optional[str] = None



class VoiceJobManager:
    """Bounded registry; persistence is opt-in and never retains reply content.

    A durable registry has one process owner. The store is opened lazily so imports
    and temporary, default managers do not read or mutate production history.
    """

    def __init__(
        self, max_history: int = MAX_JOB_HISTORY, *, store_path: Optional[Path | str] = None
    ) -> None:
        if max_history < 1:
            raise ValueError("max_history must be at least 1")
        self._jobs: collections.OrderedDict[str, VoiceJob] = collections.OrderedDict()
        self._lock = threading.RLock()
        self._max_history = max_history
        self._store_path = Path(store_path) if store_path is not None else None
        if self._store_path is not None and not self._store_path.is_absolute():
            raise ValueError("Voice job store path must be absolute")
        self._store_lock_fd: Optional[int] = None
        self._store_ready = False
        self._store_pid: Optional[int] = None
        self._closed = False

    @staticmethod
    def _metadata(job: VoiceJob) -> Dict[str, Any]:
        # Provider output, errors, text and audio references can carry credentials
        # or private content. Only bounded metadata and fixed error codes survive.
        provider = job.provider
        if not isinstance(provider, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", provider):
            provider = None
        latency = job.latency_ms
        if latency is not None and (not math.isfinite(latency) or latency < 0):
            latency = None
        return {
            "job_id": job.job_id, "status": job.status,
            "created_at": job.created_at, "updated_at": job.updated_at,
            "provider": provider, "is_cloned": job.is_cloned, "latency_ms": latency,
            "error_code": "interrupted" if job.error == INTERRUPTED_ERROR else (
                "failed" if job.status == "failed" else None
            ),
        }

    @staticmethod
    def _restore_record(record: Any) -> VoiceJob:
        if not isinstance(record, dict):
            raise ValueError("Invalid voice job metadata")
        job_id = record.get("job_id")
        if not isinstance(job_id, str) or not re.fullmatch(r"vjob_[0-9]{1,20}_[a-f0-9]{8}", job_id):
            raise ValueError("Invalid voice job ID")
        status = record.get("status", "queued")
        if status not in JOB_STATUSES:
            raise ValueError("Invalid stored voice job status")
        for field in ("created_at", "updated_at"):
            value = record.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("Invalid stored voice job timestamp")
        # Select fields explicitly even when importing legacy full-model records.
        job = VoiceJob(
            job_id=job_id, text="", status=status,
            created_at=record["created_at"], updated_at=record["updated_at"],
            provider=record.get("provider"), is_cloned=record.get("is_cloned", False),
            latency_ms=record.get("latency_ms"),
        )
        metadata = VoiceJobManager._metadata(job)
        job.provider = metadata["provider"]
        job.latency_ms = metadata["latency_ms"]
        if status not in TERMINAL_STATUSES:
            job.status = "failed"
            job.error = INTERRUPTED_ERROR
            job.updated_at = time.time()
        elif status == "failed":
            job.error = INTERRUPTED_ERROR if record.get("error_code") == "interrupted" else REDACTED_ERROR
        return job

    def _ensure_store(self) -> None:
        if self._closed:
            raise RuntimeError("Voice job registry is closed")
        if self._store_ready and self._store_pid != os.getpid():
            raise RuntimeError("Voice job registry belongs to another process")
        if self._store_path is None or self._store_ready:
            return
        path = self._store_path
        fd = None
        try:
            if any(parent.is_symlink() for parent in (path, *path.parents)):
                raise ValueError("Voice job store must not use symbolic links")
            path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            parent_stat = path.parent.stat()
            if parent_stat.st_uid != os.getuid() or stat.S_IMODE(parent_stat.st_mode) & 0o077:
                raise ValueError("Voice job store directory must be private to its owner")
            fd = os.open(str(path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            lock_stat = os.fstat(fd)
            if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_uid != os.getuid():
                raise ValueError("Invalid voice job store lock")
            os.fchmod(fd, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            restored: collections.OrderedDict[str, VoiceJob] = collections.OrderedDict()
            if path.exists():
                if not path.is_file() or path.stat().st_uid != os.getuid():
                    raise ValueError("Invalid voice job store file")
                with path.open(encoding="utf-8") as stream:
                    raw = stream.read(MAX_STORE_BYTES + 1)
                if len(raw.encode("utf-8")) > MAX_STORE_BYTES:
                    raise ValueError("Voice job store exceeds size limit")
                payload = json.loads(raw)
                # v0 was an unversioned list or {jobs: [...]} full-model snapshot.
                if isinstance(payload, list):
                    records = payload
                elif isinstance(payload, dict) and type(payload.get("version", 0)) is int and payload.get("version", 0) in (0, STORE_VERSION):
                    records = payload.get("jobs")
                else:
                    raise ValueError("Unsupported voice job store version")
                if not isinstance(records, list):
                    raise ValueError("Invalid voice job history")
                for record in records:
                    job = self._restore_record(record)
                    if job.job_id in restored:
                        raise ValueError("Duplicate stored voice job ID")
                    restored[job.job_id] = job
                while len(restored) > self._max_history:
                    restored.popitem(last=False)
            self._store_lock_fd = fd
            self._commit(restored)
            self._store_ready = True
            self._store_pid = os.getpid()
        except (OSError, ValueError, TypeError, RuntimeError):
            if fd is not None:
                os.close(fd)
            self._store_lock_fd = None
            # Do not echo private file contents, paths, or provider validation data.
            raise RuntimeError("Voice job history unavailable; store was not loaded") from None

    def _commit(self, jobs: collections.OrderedDict[str, VoiceJob]) -> None:
        if self._store_path is not None:
            payload = json.dumps({"version": STORE_VERSION, "jobs": [
                self._metadata(job) for job in jobs.values()
            ]}, allow_nan=False, separators=(",", ":"))
            if len(payload.encode("utf-8")) > MAX_STORE_BYTES:
                raise RuntimeError("Voice job history exceeds storage limit")
            temporary = None
            try:
                fd, temporary = tempfile.mkstemp(prefix=".voice-jobs-", dir=self._store_path.parent)
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self._store_path)
                directory_fd = os.open(self._store_path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                raise RuntimeError("Voice job history could not be saved") from None
            finally:
                if temporary is not None and os.path.exists(temporary):
                    os.unlink(temporary)
        self._jobs = jobs

    def close(self) -> None:
        """Release durable-store ownership; a closed registry cannot accept work."""
        with self._lock:
            if self._store_lock_fd is not None:
                os.close(self._store_lock_fd)
                self._store_lock_fd = None
            self._closed = True

    def create_job(self, text: str, *, preserve_active: bool = False, generation: int = 0, turn_id: Optional[str] = None, message_id: Optional[str] = None) -> VoiceJob:
        """Create a job; delivery callers may refuse eviction of active history."""
        job_id = f"vjob_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        job = VoiceJob(job_id=job_id, text=text, status="queued", generation=generation, turn_id=turn_id, message_id=message_id)
        with self._lock:
            self._ensure_store()
            jobs = self._jobs.copy()
            if len(jobs) >= self._max_history:
                if preserve_active:
                    evictable = next(
                        (key for key, item in jobs.items() if item.status in TERMINAL_STATUSES),
                        None,
                    )
                    if evictable is None:
                        raise RuntimeError("Voice job history is full of active jobs")
                    del jobs[evictable]
                else:
                    jobs.popitem(last=False)
            jobs[job_id] = job
            self._commit(jobs)
        logger.debug("Created voice job %s", job_id)
        return job.model_copy()

    def get_job(self, job_id: str) -> Optional[VoiceJob]:
        """Fetch voice job by ID."""
        with self._lock:
            self._ensure_store()
            job = self._jobs.get(job_id)
            return job.model_copy() if job else None

    def list_jobs(self, limit: int = 20) -> List[VoiceJob]:
        """List most recent voice jobs."""
        limit = max(0, limit)
        with self._lock:
            self._ensure_store()
            items = list(self._jobs.values())
            items.reverse()
            return [job.model_copy() for job in items[:limit]]

    def update_job(self, job_id: str, **kwargs: Any) -> Optional[VoiceJob]:
        """Atomically update job status and metadata."""
        with self._lock:
            self._ensure_store()
            job = self._jobs.get(job_id)
            if not job:
                return None
            validated: Dict[str, Any] = {}
            for key, val in kwargs.items():
                if key not in VoiceJob.model_fields:
                    raise ValueError(f"Unknown voice job field: {key}")
                if key == "status" and val not in JOB_STATUSES:
                    raise ValueError(f"Invalid voice job status: {val}")
                if key in {"job_id", "created_at", "text"}:
                    raise ValueError(f"Immutable voice job field: {key}")
                validated[key] = val
            values = job.model_dump()
            values.update(validated)
            values["updated_at"] = time.time()
            updated = VoiceJob.model_validate(values)
            if job.status in TERMINAL_STATUSES:
                return job.model_copy()
            if "status" in validated:
                next_status = validated["status"]
                allowed = {
                    "queued": {"synthesizing", "cancelled", "failed"},
                    "synthesizing": {"playing", "cancelled", "failed"},
                    "playing": {"completed", "cancelled", "failed"},
                }
                if next_status != job.status and next_status not in allowed.get(job.status, set()):
                    raise ValueError(
                        f"Invalid voice job transition: {job.status} -> {next_status}"
                    )
            jobs = self._jobs.copy()
            jobs[job_id] = updated
            self._commit(jobs)
            return updated.model_copy()

    def cancel_job(self, job_id: str):
        """Record cancellation and return whether playback may need stopping."""
        with self._lock:
            self._ensure_store()
            job = self._jobs.get(job_id)
            if not job or job.status in TERMINAL_STATUSES:
                return job.model_copy() if job else None, False
            active = job.status in {"synthesizing", "playing"}
            return self.update_job(job_id, status="cancelled"), active

    def cancel_active_jobs(self) -> int:
        """Cancel any jobs currently queued, synthesizing, or playing."""
        cancelled_count = 0
        with self._lock:
            # A capture daemon may request local playback cancellation before it
            # has any jobs. Never let that request claim the core delivery store.
            if self._store_path is not None and not self._store_ready and not self._closed:
                return 0
            self._ensure_store()
            jobs = self._jobs.copy()
            for job in self._jobs.values():
                if job.status in {"queued", "synthesizing", "playing"}:
                    jobs[job.job_id] = job.model_copy(update={"status": "cancelled", "updated_at": time.time()})
                    cancelled_count += 1
            if cancelled_count:
                self._commit(jobs)
        if cancelled_count:
            try:
                from apps.voice.speech_manager import speech_manager
                speech_manager.stop()
            except Exception:
                logger.exception("Failed to stop playback after cancelling voice jobs")
            logger.info("Cancelled %d active voice job(s) and halted playback.", cancelled_count)
        return cancelled_count


voice_job_mgr = VoiceJobManager(store_path=default_store_path())
