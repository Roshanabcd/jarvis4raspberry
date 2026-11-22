"""Explicit local-dashboard background task submission and polling."""
from pathlib import Path
import threading

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.tasks.background import BackgroundTasks, Identity, QueueFull, TokenConflict, resolve_identity


def local_dashboard(request: Request):
    from apps.api.active_desktop_api import require_local_dashboard
    return require_local_dashboard(request)


router = APIRouter(prefix='/api/task-jobs', tags=['Background tasks'],
                   dependencies=[Depends(local_dashboard)])
_manager = None
_manager_lock = threading.Lock()


def get_manager():
    global _manager
    with _manager_lock:
        if _manager is None:
            path = Path(__file__).resolve().parents[2] / 'data' / 'task_jobs' / 'history.sqlite3'
            _manager = BackgroundTasks(store_path=path)
        return _manager


def close_manager():
    """Shutdown never creates a worker or a store that was not already used."""
    with _manager_lock:
        if _manager is not None:
            _manager.close()


class SubmitTask(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    transcript: str = Field(min_length=1, max_length=4096)

    @field_validator('transcript')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Transcript must not be blank')
        return value


def identity():
    try:
        return resolve_identity()
    except Exception:
        raise HTTPException(503, 'Task identity unavailable') from None


def call(operation, *args):
    try:
        result = operation(*args)
    except QueueFull:
        raise HTTPException(429, 'Background task queue is full') from None
    except TokenConflict:
        raise HTTPException(409, 'Idempotency token already used for another task') from None
    except ValueError:
        raise HTTPException(422, 'Invalid background task request') from None
    except (RuntimeError, OSError):
        raise HTTPException(503, 'Background task history unavailable') from None
    if result is None:
        raise HTTPException(404, 'Task not found')
    return result


@router.post('', status_code=202)
def submit(req: SubmitTask, idempotency_key: str = Header(min_length=8, max_length=128, pattern=r'^[A-Za-z0-9_-]+$'),
           manager: BackgroundTasks = Depends(get_manager), who: Identity = Depends(identity)):
    return call(manager.submit, req.transcript, idempotency_key, who)


@router.get('')
def list_jobs(manager: BackgroundTasks = Depends(get_manager), who: Identity = Depends(identity)):
    return {'jobs': call(manager.list, who)}


@router.get('/{job_id}')
def get_job(job_id: str, manager: BackgroundTasks = Depends(get_manager), who: Identity = Depends(identity)):
    return call(manager.get, job_id, who)


@router.post('/{job_id}/cancel')
def cancel_job(job_id: str, manager: BackgroundTasks = Depends(get_manager), who: Identity = Depends(identity)):
    return call(manager.cancel, job_id, who)


@router.delete('/{job_id}')
def dismiss_job(job_id: str, manager: BackgroundTasks = Depends(get_manager), who: Identity = Depends(identity)):
    ok = call(manager.dismiss, job_id, who)
    return {'status': 'ok', 'dismissed': ok, 'job_id': job_id}


@router.post('/{job_id}/retry')
def retry_job(job_id: str, manager: BackgroundTasks = Depends(get_manager), who: Identity = Depends(identity)):
    return call(manager.retry, job_id, who)
