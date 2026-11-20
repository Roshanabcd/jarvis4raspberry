import os
import stat
from types import SimpleNamespace

from apps.voice.audio_environment import local_audio_environment


def test_system_service_uses_only_its_own_user_audio_session(monkeypatch):
    monkeypatch.delenv('XDG_RUNTIME_DIR', raising=False)
    monkeypatch.delenv('DBUS_SESSION_BUS_ADDRESS', raising=False)
    actual_stat = os.stat
    runtime = f'/run/user/{os.getuid()}'
    def owned(path, *args, **kwargs):
        return SimpleNamespace(st_mode=stat.S_IFDIR, st_uid=os.getuid()) if path == runtime else actual_stat(path,*args,**kwargs)
    monkeypatch.setattr(os, 'stat', owned)
    result = local_audio_environment()
    assert result['XDG_RUNTIME_DIR'] == runtime
    assert result['DBUS_SESSION_BUS_ADDRESS'] == f'unix:path={runtime}/bus'
    assert 'XDG_RUNTIME_DIR' not in os.environ


def test_existing_audio_routing_is_preserved(monkeypatch):
    monkeypatch.setenv('XDG_RUNTIME_DIR', '/existing/runtime')
    monkeypatch.setenv('DBUS_SESSION_BUS_ADDRESS', 'unix:path=/existing/bus')
    result = local_audio_environment()
    assert result['XDG_RUNTIME_DIR'] == '/existing/runtime'
    assert result['DBUS_SESSION_BUS_ADDRESS'] == 'unix:path=/existing/bus'


def test_no_access_to_another_users_runtime(monkeypatch):
    monkeypatch.delenv('XDG_RUNTIME_DIR', raising=False)
    monkeypatch.delenv('DBUS_SESSION_BUS_ADDRESS', raising=False)
    actual_stat = os.stat
    runtime = f'/run/user/{os.getuid()}'
    def foreign(path, *args, **kwargs):
        return SimpleNamespace(st_mode=stat.S_IFDIR, st_uid=os.getuid()+1) if path == runtime else actual_stat(path,*args,**kwargs)
    monkeypatch.setattr(os, 'stat', foreign)
    assert 'XDG_RUNTIME_DIR' not in local_audio_environment()
