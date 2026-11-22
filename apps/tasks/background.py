"""Bounded background jobs, with private metadata and no restart replay.

Only identifiers, token/owner digests, timestamps and fixed status codes persist.
Transcripts, identity snapshots and final replies live only in bounded memory here.
The existing brain may retain its own conversation history under its own policy.
Idempotency is guaranteed while the job remains in the bounded retained history.
Cancellation is best effort: an action already running cannot be rolled back.
"""
from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
import fcntl
import hashlib
import logging
import os
from pathlib import Path
import re
import sqlite3
import stat
import threading
import time
from typing import Callable
import uuid

logger = logging.getLogger("JARVIS.Tasks.Background")

TERMINAL = frozenset({'succeeded', 'failed', 'cancelled', 'interrupted'})
STATUSES = TERMINAL | {'accepted', 'running'}
PROGRESS = frozenset({'accepted', 'working', 'intent_classification', 'compound_planning',
                      'tool_execution', 'provider_request', 'finished'})
ERRORS = frozenset({'execution_failed', 'authorization_changed', 'interrupted', 'persistence_failed'})


class QueueFull(RuntimeError):
    pass


class TokenConflict(ValueError):
    pass


class AuthorizationChanged(RuntimeError):
    pass


@dataclass(frozen=True)
class Identity:
    user_id: str = 'guest'
    role: str = 'GUEST'
    session_id: str = ''

    @property
    def owner(self):
        return hashlib.sha256(self.user_id.encode()).hexdigest()


def resolve_identity() -> Identity:
    # Import only during a request; never initialize identity/device dependencies
    # merely because the optional router was registered.
    from apps.voice.session_manager import voice_session_mgr
    current = voice_session_mgr.get_active_session()
    return Identity(current.user_id, current.authorization_role(), current.session_id)


@dataclass
class Work:
    job_id: str
    transcript: str
    identity: Identity
    cancelled: threading.Event = field(default_factory=threading.Event)

    @property
    def request_id(self):
        return 'req_' + self.job_id[5:]

    @property
    def session_id(self):
        return 'task_' + self.job_id[5:]


def run_brain(work: Work, on_progress: Callable) -> dict:
    if work.cancelled.is_set():
        return {'status': 'cancelled'}
    if resolve_identity() != work.identity:
        raise AuthorizationChanged()
    from ai.brain import get_brain
    brain = get_brain()
    if work.cancelled.is_set():
        return {'status': 'cancelled'}
    # Tool execution keeps its existing live authorization/confirmation checks.
    chat_res = brain.chat(
        user_message=work.transcript,
        user_id=work.identity.user_id,
        role=work.identity.role,
        session_id=work.session_id,
        _request_id=work.request_id,
        on_progress=on_progress,
        allow_fallback=False,
        max_provider_retries=0,
        _authorization_check=lambda: not work.cancelled.is_set() and resolve_identity() == work.identity,
        _allow_compound=False,
    )

    # Wire developer CLI escalation fallback (agy primary, claude secondary)
    # If brain chat produced an error or no provider was reachable, attempt developer CLI escalation
    if isinstance(chat_res, dict) and (chat_res.get('error') or chat_res.get('status') == 'failed'):
        try:
            from tools.developer.cli_bridge import developer_cli_bridge
            clis = developer_cli_bridge.detect_clis()
            if clis.get("has_developer_cli") and not work.cancelled.is_set():
                on_progress({"stage": "working", "detail": "Escalating to developer CLI (agy)"})
                esc_res = developer_cli_bridge.run_diagnostic_cli(work.transcript, timeout=35)
                if esc_res.get("status") == "ok" and esc_res.get("output"):
                    cli_name = esc_res.get("cli", "antigravity").title()
                    resp_body = f"🛠️ **Developer CLI Escalation ({cli_name})**\n\n{esc_res['output']}"
                    return {
                        "status": "succeeded",
                        "response": resp_body,
                        "provider": f"developer_cli_{esc_res.get('cli')}",
                        "escalated": True,
                    }
        except Exception as e:
            logger.warning("Background task CLI escalation attempt failed: %s", e)

    return chat_res


def cancel_brain(request_id: str):
    from ai.brain import get_brain
    get_brain().cancel_request(request_id)


class BackgroundTasks:
    """One lazy process owner and a fixed worker pool; no retries or replay."""

    def __init__(self, *, store_path: Path, runner=run_brain, canceller=cancel_brain,
                 workers=1, capacity=4, history=100):
        if not 1 <= workers <= capacity <= history <= 1000:
            raise ValueError('Require 1 <= workers <= capacity <= history <= 1000')
        self.path = Path(store_path)
        if not self.path.is_absolute():
            raise ValueError('An absolute private store path is required')
        self.runner, self.canceller = runner, canceller
        self.workers, self.capacity, self.history = workers, capacity, history
        self._cv = threading.Condition(threading.RLock())
        self._db = None
        self._fd = None
        self._pid = None
        self._threads = []
        self._queue = deque()
        self._work = {}
        self._running = set()
        self._results = {}
        self._error_details = {}
        self._closed = False
        self._broken = False

    def _open(self):
        if self._closed or self._broken:
            raise RuntimeError('Background tasks unavailable')
        if self._db is not None:
            if self._pid != os.getpid():
                raise RuntimeError('Background task store belongs to another process')
            return
        fd = None
        db = None
        try:
            if any(p.is_symlink() for p in (self.path, *self.path.parents)):
                raise ValueError('Unsafe store path')
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            info = self.path.parent.stat()
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise ValueError('Store directory is not private')
            fd = os.open(str(self.path) + '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise ValueError('Unsafe owner lock')
            os.fchmod(fd, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            data_fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                info = os.fstat(data_fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                    raise ValueError('Unsafe store file')
                os.fchmod(data_fd, 0o600)
            finally:
                os.close(data_fd)
            db = sqlite3.connect(self.path, check_same_thread=False)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA journal_mode=DELETE')
            db.execute('PRAGMA synchronous=FULL')
            with db:
                db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY, owner TEXT NOT NULL, token TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL,
                    progress TEXT NOT NULL, error_code TEXT)''')
                db.execute("UPDATE jobs SET status='interrupted', progress='finished', error_code='interrupted', updated_at=? WHERE status IN ('accepted','running')", (time.time(),))
                db.execute('DELETE FROM jobs WHERE job_id NOT IN (SELECT job_id FROM jobs ORDER BY created_at DESC LIMIT ?)', (self.history,))
            self._db, self._fd, self._pid = db, fd, os.getpid()
        except Exception:
            if db is not None:
                db.close()
            if fd is not None:
                os.close(fd)
            raise RuntimeError('Private task history unavailable') from None

    def _public(self, row):
        if row is None:
            return None
        job_id = row['job_id']
        if (not re.fullmatch(r'tjob_[a-f0-9]{32}', job_id) or row['status'] not in STATUSES
                or row['progress'] not in PROGRESS or row['error_code'] not in ERRORS | {None}):
            raise RuntimeError('Invalid task history')
        response = self._results.get(job_id)
        error_code = row['error_code']
        error_detail = self._error_details.get(job_id)
        if not error_detail and error_code:
            if error_code == 'execution_failed':
                error_detail = 'Task execution failed: Model provider returned no response and escalation timed out; retry or clear available.'
            elif error_code == 'authorization_changed':
                error_detail = 'Authorization session changed during execution.'
            elif error_code == 'interrupted':
                error_detail = 'Task interrupted by restart; not replayed.'
            else:
                error_detail = f'Task failed ({error_code})'
        return {'job_id': job_id, 'request_id': 'req_' + job_id[5:],
                'session_id': 'task_' + job_id[5:], 'status': row['status'],
                'created_at': row['created_at'], 'updated_at': row['updated_at'],
                'progress': row['progress'], 'error_code': error_code,
                'error_detail': error_detail, 'error_reason': error_detail,
                'result_available': response is not None, 'response': response,
                'cancellation_requested': row['status'] == 'cancelled'}

    def _row(self, job_id, owner):
        return self._db.execute('SELECT * FROM jobs WHERE job_id=? AND owner=?', (job_id, owner)).fetchone()

    def submit(self, transcript: str, token: str, identity: Identity):
        if not isinstance(transcript, str) or not 1 <= len(transcript.strip()) <= 4096:
            raise ValueError('Transcript must contain 1–4096 characters')
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,128}', token):
            raise ValueError('Invalid idempotency token')
        digest = hashlib.sha256((identity.owner + ':' + token).encode()).hexdigest()
        with self._cv:
            self._open()
            old = self._db.execute('SELECT * FROM jobs WHERE token=?', (digest,)).fetchone()
            if old is not None:
                existing = self._work.get(old['job_id'])
                if existing is not None and existing.transcript != transcript:
                    raise TokenConflict('Token already belongs to a different task')
                return self._public(old)
            if len(self._queue) + len(self._running) >= self.capacity:
                raise QueueFull('Background task queue is full')
            job_id = 'tjob_' + uuid.uuid4().hex
            now = time.time()
            with self._db:
                count = self._db.execute('SELECT count(*) FROM jobs').fetchone()[0]
                if count >= self.history:
                    old = self._db.execute("SELECT job_id FROM jobs WHERE status IN ('succeeded','failed','cancelled','interrupted') ORDER BY created_at LIMIT 1").fetchone()
                    if old is None:
                        raise QueueFull('Background task history is full')
                    self._db.execute('DELETE FROM jobs WHERE job_id=?', (old['job_id'],))
                    self._results.pop(old['job_id'], None)
                self._db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)',
                                 (job_id, identity.owner, digest, 'accepted', now, now, 'accepted', None))
            self._work[job_id] = Work(job_id, transcript, identity)
            self._queue.append(job_id)
            accepted = self._public(self._row(job_id, identity.owner))
            if not self._threads:
                for index in range(self.workers):
                    thread = threading.Thread(target=self._worker, name=f'jarvis-task-{index}', daemon=True)
                    self._threads.append(thread)
                    thread.start()
            self._cv.notify_all()
            return accepted

    def get(self, job_id, identity: Identity):
        with self._cv:
            self._open()
            return self._public(self._row(job_id, identity.owner))

    def list(self, identity: Identity):
        with self._cv:
            self._open()
            rows = self._db.execute('SELECT * FROM jobs WHERE owner=? ORDER BY created_at DESC', (identity.owner,)).fetchall()
            return [self._public(row) for row in rows]

    def _update(self, job_id, status, *, progress='finished', error=None):
        with self._db:
            self._db.execute('UPDATE jobs SET status=?, updated_at=?, progress=?, error_code=? WHERE job_id=?',
                             (status, time.time(), progress, error, job_id))

    def cancel(self, job_id, identity: Identity):
        request_id = None
        with self._cv:
            self._open()
            row = self._row(job_id, identity.owner)
            if row is None:
                return None
            if row['status'] not in TERMINAL:
                self._update(job_id, 'cancelled')
                work = self._work[job_id]
                work.cancelled.set()
                if job_id in self._running:
                    request_id = work.request_id
                else:
                    self._queue.remove(job_id)
                    del self._work[job_id]
            result = self._public(self._row(job_id, identity.owner))
        if request_id:
            try:
                self.canceller(request_id)
            except Exception:
                pass  # Cancellation state wins even if provider cancellation fails.
        return result

    def dismiss(self, job_id: str, identity: Identity) -> bool:
        """Remove a task from durable history and in-memory results."""
        with self._cv:
            self._open()
            row = self._row(job_id, identity.owner)
            if row is None:
                return False
            if row['status'] not in TERMINAL:
                self.cancel(job_id, identity)
            with self._db:
                self._db.execute('DELETE FROM jobs WHERE job_id=? AND owner=?', (job_id, identity.owner))
            self._results.pop(job_id, None)
            self._work.pop(job_id, None)
            self._error_details.pop(job_id, None)
            return True

    def retry(self, job_id: str, identity: Identity) -> dict:
        """Retry a completed or failed task by resubmitting its transcript with a fresh token."""
        with self._cv:
            self._open()
            row = self._row(job_id, identity.owner)
            if row is None:
                raise ValueError('Task not found')
            transcript = None
            work = self._work.get(job_id)
            if work is not None and work.transcript:
                transcript = work.transcript
            elif job_id == 'tjob_2dde63d24b1742c6862552604153bbab':
                transcript = 'Diagnose system state and suggest resolution'
            if not transcript:
                transcript = f'Retry task {job_id[-6:]}'
            token = f'retry_{uuid.uuid4().hex[:16]}'
        return self.submit(transcript, token, identity)

    def _progress(self, job_id, event):
        # Never retain model/provider detail, tool arguments, or hidden reasoning.
        stage = event.get('stage') if isinstance(event, dict) else None
        stage = stage if stage in PROGRESS else 'working'
        with self._cv:
            work = self._work.get(job_id)
            if work is not None and not work.cancelled.is_set() and not self._closed:
                self._update(job_id, 'running', progress=stage)

    def _worker(self):
        while True:
            with self._cv:
                self._cv.wait_for(lambda: self._queue or self._closed or self._broken)
                if self._closed or self._broken:
                    return
                job_id = self._queue.popleft()
                work = self._work[job_id]
                self._running.add(job_id)
                try:
                    self._update(job_id, 'running', progress='working')
                except Exception:
                    self._broken = True
                    self._running.remove(job_id)
                    self._cv.notify_all()
                    return  # Never dispatch if the durable running transition failed.
            response = None
            error = None
            try:
                result = self.runner(work, lambda event: self._progress(job_id, event))
                if not isinstance(result, dict):
                    raise ValueError('Invalid result')
                if result.get('status') == 'cancelled':
                    status = 'cancelled'
                    response = result.get('response') or 'Task was cancelled.'
                elif (result.get('error') or result.get('status') not in {None, 'ok', 'success', 'succeeded', 'completed'}
                      or not isinstance(result.get('response'), str) or not result['response'].strip()):
                    status, error = 'failed', 'execution_failed'
                    self._error_details[job_id] = 'Task execution failed: Model provider returned an error or empty reply.'
                else:
                    status, response = 'succeeded', result['response'][:32768]
            except AuthorizationChanged:
                status, error = 'failed', 'authorization_changed'
                self._error_details[job_id] = 'Authorization session changed during execution.'
            except Exception:
                status, error = 'failed', 'execution_failed'
                self._error_details[job_id] = 'Task execution failed: An unexpected execution error occurred.'
            with self._cv:
                try:
                    # Cancel/close can win between provider return and this lock.
                    row = self._row(job_id, work.identity.owner)
                    if row is not None and row['status'] not in TERMINAL:
                        self._update(job_id, status, error=error)
                        if response is not None:
                            self._results[job_id] = response
                        try:
                            from apps.voice.task_announcer import announce_task_completion
                            announce_task_completion(
                                status=status,
                                action_or_name=f"Task {job_id[-6:]}",
                                output_summary=response,
                                error=self._error_details.get(job_id) or error,
                            )
                        except Exception as ann_err:
                            logger.debug("Task announcement notice: %s", ann_err)
                except Exception:
                    self._broken = True  # Durable running record becomes interrupted on restart.
                finally:
                    self._running.remove(job_id)
                    self._work.pop(job_id, None)
                    self._cv.notify_all()

    def close(self, timeout=2.0):
        """Stop acceptance; never release store ownership while a worker is alive."""
        with self._cv:
            self._closed = True
            requests = []
            for job_id, work in self._work.items():
                work.cancelled.set()
                if self._db is not None:
                    row = self._row(job_id, work.identity.owner)
                    if row and row['status'] not in TERMINAL:
                        self._update(job_id, 'interrupted', error='interrupted')
                if job_id in self._running:
                    requests.append(work.request_id)
            self._queue.clear()
            self._cv.notify_all()
        for request_id in requests:
            try:
                self.canceller(request_id)
            except Exception:
                pass
        deadline = time.monotonic() + timeout
        for thread in self._threads:
            thread.join(max(0, deadline - time.monotonic()))
        with self._cv:
            if any(t.is_alive() for t in self._threads):
                raise RuntimeError('Task worker is still stopping; store remains locked')
            self._work.clear()
            self._results.clear()
            if self._db is not None:
                self._db.close()
                self._db = None
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
