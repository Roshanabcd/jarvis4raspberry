"""Disposable stores and injected workers only; no providers, devices or credentials."""
import importlib
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.tasks.background import BackgroundTasks, Identity, QueueFull, TokenConflict

GUEST = Identity('guest', 'GUEST', 'test-session')


@pytest.fixture
def managers(tmp_path):
    opened = []
    releases = []

    def create(**kwargs):
        path = kwargs.pop('store_path', tmp_path / ('private' + str(len(opened))) / 'jobs.sqlite3')
        manager = BackgroundTasks(store_path=path, canceller=Mock(), **kwargs)
        opened.append(manager)
        return manager

    yield create, releases
    for event in releases:
        event.set()
    for manager in opened:
        manager.close()


def blocking(managers, **kwargs):
    create, releases = managers
    started, release = threading.Event(), threading.Event()
    releases.append(release)
    calls = []

    def run(work, progress):
        calls.append(work)
        started.set()
        assert release.wait(5)
        return {'response': 'private final answer'}

    return create(runner=run, **kwargs), started, release, calls


def wait_status(manager, job_id, status, who=GUEST):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        result = manager.get(job_id, who)
        if result['status'] == status:
            return result
        time.sleep(0.005)
    pytest.fail(f'Job never reached {status}')


def test_lazy_import_and_constructor_do_not_open_runtime_files(tmp_path):
    script = '''
import builtins, os, sqlite3, threading
from unittest.mock import patch
import fastapi, pydantic
with patch.object(sqlite3, 'connect', side_effect=AssertionError('store on import')), patch.object(threading.Thread, 'start', side_effect=AssertionError('worker on import')):
    from apps.api.task_jobs_api import router
    from apps.tasks.background import BackgroundTasks
    m = BackgroundTasks(store_path=__import__('pathlib').Path('/unused/tasks.sqlite3'))
    assert m._db is None and m._threads == []
'''
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_immediate_acceptance_idempotency_capacity_and_isolated_sessions(managers):
    manager, started, release, calls = blocking(managers, capacity=2)
    start = time.monotonic()
    one = manager.submit('private prompt one', 'request01', GUEST)
    assert time.monotonic() - start < 1
    assert one['status'] == 'accepted'
    assert started.wait(2)
    duplicate = manager.submit('private prompt one', 'request01', GUEST)
    assert duplicate['job_id'] == one['job_id']
    with pytest.raises(TokenConflict):
        manager.submit('different prompt', 'request01', GUEST)
    two = manager.submit('private prompt two', 'request02', GUEST)
    with pytest.raises(QueueFull):
        manager.submit('overflow', 'request03', GUEST)
    assert two['session_id'] != one['session_id']
    assert calls[0].identity == GUEST
    release.set()
    assert wait_status(manager, two['job_id'], 'succeeded')['response'] == 'private final answer'
    assert len(calls) == 2


def test_queued_cancel_never_dispatches_and_running_cancel_wins(managers):
    manager, started, release, calls = blocking(managers, capacity=2)
    first = manager.submit('one', 'request01', GUEST)
    assert started.wait(2)
    second = manager.submit('two', 'request02', GUEST)
    assert manager.cancel(second['job_id'], GUEST)['status'] == 'cancelled'
    assert manager.cancel(first['job_id'], GUEST)['status'] == 'cancelled'
    manager.canceller.assert_called_once_with(first['request_id'])
    # Running cancellation retains its worker slot until execution actually ends.
    third = manager.submit('three', 'request03', GUEST)
    with pytest.raises(QueueFull):
        manager.submit('four', 'request04', GUEST)
    release.set()
    wait_status(manager, third['job_id'], 'succeeded')
    assert len(calls) == 2
    cancelled = manager.get(first['job_id'], GUEST)
    assert cancelled['status'] == 'cancelled' and cancelled['response'] is None
    assert manager.get(second['job_id'], GUEST)['status'] == 'cancelled'


@pytest.mark.parametrize('result', [{'response': 'plausible', 'error': 'private secret'},
                                    {'status': 'failed', 'response': 'plausible'},
                                    {'response': ''}, {'response': ' ', 'status': 'ok'}, None])
def test_provider_errors_never_become_success_or_leak(managers, result):
    manager = managers[0](runner=lambda *_: result)
    job = manager.submit('private prompt', 'request01', GUEST)
    failed = wait_status(manager, job['job_id'], 'failed')
    assert failed['error_code'] == 'execution_failed'
    assert failed['response'] is None
    assert 'private' not in manager.path.read_bytes().decode(errors='ignore')


def test_exceptions_are_generic_and_no_automatic_retry(managers):
    runner = Mock(side_effect=ValueError('private key sentinel'))
    manager = managers[0](runner=runner)
    job = manager.submit('prompt', 'request01', GUEST)
    failed = wait_status(manager, job['job_id'], 'failed')
    assert failed['error_code'] == 'execution_failed'
    assert runner.call_count == 1
    assert 'sentinel' not in repr(failed)


def test_private_allowlisted_metadata_survives_without_results_or_prompts(managers):
    def run(work, progress):
        progress({'stage': 'private secret', 'detail': 'sensitive argument'})
        return {'response': 'sensitive result', 'error': None}

    manager = managers[0](runner=run)
    job = manager.submit('sensitive transcript', 'sensitive-token', GUEST)
    wait_status(manager, job['job_id'], 'succeeded')
    raw = manager.path.read_bytes()
    assert all(value not in raw for value in [b'sensitive', b'private secret', b'test-session'])
    assert stat.S_IMODE(manager.path.stat().st_mode) == 0o600
    assert stat.S_IMODE(manager.path.parent.stat().st_mode) == 0o700
    manager.close()
    restored = managers[0](runner=Mock(), store_path=manager.path)
    result = restored.get(job['job_id'], GUEST)
    assert result['status'] == 'succeeded' and not result['result_available']
    assert restored.submit('new ignored text', 'sensitive-token', GUEST)['job_id'] == job['job_id']
    restored.runner.assert_not_called()


def test_restart_marks_accepted_and_running_interrupted_without_replay(managers):
    manager = managers[0](runner=lambda *_: {'response': 'ok'})
    one = manager.submit('one', 'request01', GUEST)
    wait_status(manager, one['job_id'], 'succeeded')
    two = manager.submit('two', 'request02', GUEST)
    wait_status(manager, two['job_id'], 'succeeded')
    manager.close()
    # Simulate durable states left by process death without any real process work.
    with sqlite3.connect(manager.path) as db:
        db.execute("UPDATE jobs SET status='accepted' WHERE job_id=?", (one['job_id'],))
        db.execute("UPDATE jobs SET status='running' WHERE job_id=?", (two['job_id'],))
    restored = managers[0](runner=Mock(), store_path=manager.path)
    assert {j['status'] for j in restored.list(GUEST)} == {'interrupted'}
    assert restored.submit('one', 'request01', GUEST)['status'] == 'interrupted'
    restored.runner.assert_not_called()
    assert not restored._threads


def test_second_owner_and_unsafe_store_are_rejected(managers, tmp_path):
    manager = managers[0](runner=Mock())
    manager.list(GUEST)
    other = managers[0](runner=Mock(), store_path=manager.path)
    with pytest.raises(RuntimeError, match='unavailable'):
        other.list(GUEST)
    public = tmp_path / 'public'
    public.mkdir(mode=0o755)
    unsafe = managers[0](runner=Mock(), store_path=public / 'jobs.sqlite3')
    with pytest.raises(RuntimeError, match='unavailable'):
        unsafe.list(GUEST)
    link = tmp_path / 'link'
    link.symlink_to(manager.path.parent, target_is_directory=True)
    unsafe = managers[0](runner=Mock(), store_path=link / 'jobs.sqlite3')
    with pytest.raises(RuntimeError, match='unavailable'):
        unsafe.list(GUEST)


def test_history_is_bounded_and_jobs_are_owner_scoped(managers):
    manager = managers[0](runner=lambda *_: {'response': 'ok'}, capacity=1, history=2)
    ids = []
    for n in range(3):
        job = manager.submit('one', f'request0{n}', GUEST)
        wait_status(manager, job['job_id'], 'succeeded')
        ids.append(job['job_id'])
    assert len(manager.list(GUEST)) == 2
    assert manager.get(ids[0], GUEST) is None
    stranger = Identity('other', 'ADMIN', 'different')
    assert manager.list(stranger) == []
    assert manager.get(ids[-1], stranger) is None
    assert manager.cancel(ids[-1], stranger) is None


def test_close_retains_owner_lock_until_running_work_finishes(managers):
    manager, started, release, calls = blocking(managers)
    manager.submit('one', 'request01', GUEST)
    assert started.wait(2)
    with pytest.raises(RuntimeError, match='still stopping'):
        manager.close(timeout=0)
    other = managers[0](runner=Mock(), store_path=manager.path)
    with pytest.raises(RuntimeError):
        other.list(GUEST)
    release.set()
    manager.close()
    assert other.list(GUEST)[0]['status'] == 'interrupted'


def test_default_runner_rechecks_identity_and_disables_provider_retry(monkeypatch):
    from apps.tasks import background
    work = background.Work('tjob_' + 'a' * 32, 'prompt', GUEST)
    monkeypatch.setattr(background, 'resolve_identity', lambda: Identity('other', 'ADMIN', 'new'))
    with pytest.raises(background.AuthorizationChanged):
        background.run_brain(work, Mock())
    brain = Mock()
    brain.chat.return_value = {'response': 'ok'}
    monkeypatch.setitem(sys.modules, 'ai.brain', Mock(get_brain=lambda: brain))
    monkeypatch.setattr(background, 'resolve_identity', lambda: GUEST)
    progress = Mock()
    background.run_brain(work, progress)
    kwargs = brain.chat.call_args.kwargs
    assert kwargs['role'] == 'GUEST'
    assert kwargs['user_id'] == 'guest'
    assert kwargs['session_id'] == work.session_id
    assert kwargs['_request_id'] == work.request_id
    assert kwargs['allow_fallback'] is False and kwargs['max_provider_retries'] == 0
    work.cancelled.set()
    assert background.run_brain(work, progress)['status'] == 'cancelled'
    assert brain.chat.call_count == 1


@pytest.fixture
def client(managers):
    from apps.api import task_jobs_api as api
    manager, started, release, calls = blocking(managers)
    app = FastAPI()
    app.include_router(api.router)
    app.dependency_overrides[api.get_manager] = lambda: manager
    app.dependency_overrides[api.identity] = lambda: GUEST
    with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1', 1234)) as client:
        yield client, manager


HEADERS = {'X-Jarvis-Client': 'dashboard', 'Idempotency-Key': 'request01', 'Origin': 'http://127.0.0.1'}


def test_router_guards_and_strict_submission(client):
    http, manager = client
    assert http.post('/api/task-jobs', json={'transcript': 'hello'}).status_code == 403
    assert http.get('/api/task-jobs').status_code == 403
    assert http.post('/api/task-jobs', json={'transcript': 'hello'}, headers={**HEADERS, 'Origin': 'https://attacker.example'}).status_code == 403
    for extra in ('role', 'user_id', 'provider', 'command'):
        assert http.post('/api/task-jobs', json={'transcript': 'hello', extra: 'ADMIN'}, headers=HEADERS).status_code == 422
    for text in ('', '   ', 'x' * 4097, 123):
        assert http.post('/api/task-jobs', json={'transcript': text}, headers=HEADERS).status_code == 422
    assert http.post('/api/task-jobs', json={'transcript': 'hello'}, headers={'X-Jarvis-Client': 'dashboard'}).status_code == 422
    assert manager._db is None


def test_api_accept_poll_duplicate_cancel_and_missing(client):
    http, manager = client
    response = http.post('/api/task-jobs', json={'transcript': 'hello'}, headers=HEADERS)
    assert response.status_code == 202
    job = response.json()
    assert job['status'] == 'accepted'
    assert http.post('/api/task-jobs', json={'transcript': 'hello'}, headers=HEADERS).json()['job_id'] == job['job_id']
    assert len(http.get('/api/task-jobs', headers=HEADERS).json()['jobs']) == 1
    assert http.get('/api/task-jobs/' + job['job_id'], headers=HEADERS).status_code == 200
    assert http.post('/api/task-jobs/' + job['job_id'] + '/cancel', headers=HEADERS).json()['status'] == 'cancelled'
    assert http.get('/api/task-jobs/unknown', headers=HEADERS).status_code == 404


def test_api_dismiss_and_retry_workflow(client):
    http, manager = client
    res = http.post('/api/task-jobs', json={'transcript': 'run diagnostic'}, headers=HEADERS)
    assert res.status_code == 202
    job_id = res.json()['job_id']
    
    # Retry task
    retry_res = http.post(f'/api/task-jobs/{job_id}/retry', headers=HEADERS)
    assert retry_res.status_code == 200
    retried_job = retry_res.json()
    assert retried_job['status'] == 'accepted'
    assert retried_job['job_id'] != job_id

    # Dismiss original task
    del_res = http.delete(f'/api/task-jobs/{job_id}', headers=HEADERS)
    assert del_res.status_code == 200
    assert del_res.json()['dismissed'] is True

    # Check original task is gone
    assert http.get(f'/api/task-jobs/{job_id}', headers=HEADERS).status_code == 404

