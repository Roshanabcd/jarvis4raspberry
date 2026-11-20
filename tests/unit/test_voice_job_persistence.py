"""Durable voice metadata tests; never use the production singleton or devices."""
import json
import os
import stat
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from apps.voice.voice_jobs import (
    INTERRUPTED_ERROR,
    MAX_STORE_BYTES,
    REDACTED_ERROR,
    STORE_VERSION,
    VoiceJobManager,
)


@pytest.fixture
def store(tmp_path):
    return tmp_path / "private" / "history.json"


@pytest.fixture
def managers(store):
    opened = []

    def create(**kwargs):
        manager = VoiceJobManager(store_path=store, **kwargs)
        opened.append(manager)
        return manager

    yield create
    for manager in opened:
        manager.close()


def test_default_managers_are_ephemeral_and_durable_store_is_lazy(store, managers):
    manager = VoiceJobManager()
    manager.create_job("ephemeral content")
    durable = managers()
    assert not store.exists()
    assert durable.cancel_active_jobs() == 0
    assert not store.parent.exists()


@pytest.mark.parametrize("status", ["queued", "synthesizing", "playing"])
def test_restart_fails_interrupted_jobs_without_replay(managers, store, status):
    original = managers()
    job = original.create_job("private reply")
    if status != "queued":
        original.update_job(job.job_id, status="synthesizing")
    if status == "playing":
        original.update_job(job.job_id, status="playing")
    original.close()

    restored = managers()
    recovered = restored.get_job(job.job_id)
    assert recovered.status == "failed"
    assert recovered.error == INTERRUPTED_ERROR
    assert recovered.text == ""
    assert recovered.audio_id is recovered.audio_url is None
    assert json.loads(store.read_text())["jobs"][0]["status"] == "failed"
    restored.update_job(job.job_id, status="playing")
    assert restored.get_job(job.job_id).status == "failed"
    restored.close()
    assert managers().get_job(job.job_id).error == INTERRUPTED_ERROR


@pytest.mark.parametrize("status", ["completed", "cancelled", "failed"])
def test_terminal_history_survives_without_sensitive_payload(managers, store, status):
    original = managers()
    job = original.create_job("sensitive reply sentinel")
    original.update_job(job.job_id, status="synthesizing", provider="omnivoice",
                        audio_id="sensitive-audio-id", audio_url="https://secret/audio",
                        latency_ms=123, is_cloned=True)
    original.update_job(job.job_id, status="playing")
    original.update_job(job.job_id, status=status, error="sensitive error sentinel")
    original.close()
    raw = store.read_text()
    assert "sensitive" not in raw
    assert "secret" not in raw
    assert "audio_id" not in raw
    assert '"text"' not in raw
    restored = managers().get_job(job.job_id)
    assert restored.status == status
    assert restored.created_at == job.created_at
    assert restored.provider == "omnivoice"
    assert restored.latency_ms == 123
    assert restored.is_cloned is True
    assert restored.error == (REDACTED_ERROR if status == "failed" else None)
    assert stat.S_IMODE(store.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.parent.stat().st_mode) == 0o700


def test_unsafe_provider_output_not_persisted(managers, store):
    manager = managers()
    job = manager.create_job("reply")
    manager.update_job(job.job_id, provider="https://provider/?token=secret", latency_ms=float("nan"))
    record = json.loads(store.read_text())["jobs"][0]
    assert record["provider"] is record["latency_ms"] is None


def test_capacity_and_eviction_survive_reload(managers):
    manager = managers(max_history=2)
    first = manager.create_job("first", preserve_active=True)
    second = manager.create_job("second", preserve_active=True)
    with pytest.raises(RuntimeError, match="full"):
        manager.create_job("rejected", preserve_active=True)
    manager.cancel_job(first.job_id)
    third = manager.create_job("third", preserve_active=True)
    manager.close()
    restored = managers(max_history=2)
    assert [job.job_id for job in restored.list_jobs()] == [third.job_id, second.job_id]
    assert restored.get_job(first.job_id) is None
    restored.close()
    assert [job.job_id for job in managers(max_history=1).list_jobs()] == [third.job_id]


def test_cancel_all_is_persisted_once_and_does_not_capture_devices(managers):
    manager = managers()
    jobs = [manager.create_job("reply") for _ in range(2)]
    speech = MagicMock()
    with patch.dict("sys.modules", {"apps.voice.speech_manager": MagicMock(speech_manager=speech)}):
        assert manager.cancel_active_jobs() == 2
    speech.stop.assert_called_once()
    manager.close()
    restored = managers()
    assert all(restored.get_job(job.job_id).status == "cancelled" for job in jobs)


@pytest.mark.parametrize("shape", ["list", "unversioned", "v0"])
def test_migrates_legacy_model_snapshots_and_scrubs_content(managers, store, shape):
    legacy = VoiceJobManager().create_job("legacy sensitive text").model_dump()
    legacy.update(audio_url="https://secret", error="sensitive error")
    payload = [legacy] if shape == "list" else {"jobs": [legacy]}
    if shape == "v0":
        payload["version"] = 0
    store.parent.mkdir(mode=0o700)
    store.write_text(json.dumps(payload))
    recovered = managers().get_job(legacy["job_id"])
    assert recovered.status == "failed"
    assert recovered.text == ""
    saved = json.loads(store.read_text())
    assert saved["version"] == STORE_VERSION
    assert "sensitive" not in store.read_text()
    assert "secret" not in store.read_text()


@pytest.mark.parametrize("payload", ["{broken", '{"version":99,"jobs":[]}',
                                      '{"version":1,"jobs":[{}]}', "x" * (MAX_STORE_BYTES + 1)])
def test_invalid_or_future_store_is_preserved_and_reports_unavailable(managers, store, payload):
    store.parent.mkdir(mode=0o700)
    store.write_text(payload)
    manager = managers()
    with pytest.raises(RuntimeError, match="unavailable"):
        manager.list_jobs()
    assert store.read_text() == payload
    assert manager._store_lock_fd is None


def test_second_owner_cannot_interrupt_or_replace_live_jobs(managers, store):
    owner = managers()
    job = owner.create_job("live reply")
    other = managers()
    before = store.read_bytes()
    assert other.cancel_active_jobs() == 0
    with pytest.raises(RuntimeError, match="unavailable"):
        other.list_jobs()
    assert owner.get_job(job.job_id).status == "queued"
    assert store.read_bytes() == before
    owner.close()
    assert other.get_job(job.job_id).error == INTERRUPTED_ERROR


def test_abrupt_process_exit_leaves_recoverable_metadata(managers, store):
    script = """
import os
import sys
from apps.voice.voice_jobs import VoiceJobManager
manager = VoiceJobManager(store_path=sys.argv[1])
job = manager.create_job('process-only private reply')
manager.update_job(job.job_id, status='synthesizing')
os._exit(0)
"""
    subprocess.run([sys.executable, "-c", script, str(store)], check=True,
                   capture_output=True, timeout=10)
    recovered = managers().list_jobs()
    assert len(recovered) == 1
    assert recovered[0].status == "failed"
    assert recovered[0].error == INTERRUPTED_ERROR
    assert recovered[0].text == ""


def test_inherited_manager_cannot_write_in_another_process(managers, monkeypatch):
    manager = managers()
    job = manager.create_job("reply")
    pid = os.getpid()
    monkeypatch.setattr("apps.voice.voice_jobs.os.getpid", lambda: pid + 1)
    with pytest.raises(RuntimeError, match="another process"):
        manager.cancel_job(job.job_id)


def test_failed_atomic_write_keeps_original_memory_and_file(managers, store, monkeypatch):
    manager = managers()
    job = manager.create_job("reply")
    before = store.read_bytes()

    def fail_replace(*args):
        raise OSError("private failure details")

    monkeypatch.setattr("apps.voice.voice_jobs.os.replace", fail_replace)
    with pytest.raises(RuntimeError, match="could not be saved"):
        manager.update_job(job.job_id, status="synthesizing")
    assert manager.get_job(job.job_id).status == "queued"
    assert store.read_bytes() == before
    assert not list(store.parent.glob(".voice-jobs-*"))
    with pytest.raises(RuntimeError):
        manager.create_job("not accepted")
    assert len(manager.list_jobs()) == 1


def test_store_rejects_symlinks_and_public_directory(tmp_path):
    public = tmp_path / "public"
    public.mkdir(mode=0o755)
    with pytest.raises(RuntimeError, match="unavailable"):
        VoiceJobManager(store_path=public / "jobs.json").list_jobs()
    linked = tmp_path / "linked"
    linked.symlink_to(public, target_is_directory=True)
    with pytest.raises(RuntimeError, match="unavailable"):
        VoiceJobManager(store_path=linked / "jobs.json").list_jobs()
    assert not (public / "jobs.json").exists()


def test_closed_manager_cannot_accept_work(managers):
    manager = managers()
    manager.close()
    with pytest.raises(RuntimeError, match="closed"):
        manager.create_job("reply")
