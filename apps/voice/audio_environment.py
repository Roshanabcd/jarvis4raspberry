"""Connect system-service playback to its own user's local audio session."""
import os
import stat


def local_audio_environment():
    env = os.environ.copy()
    runtime = f'/run/user/{os.getuid()}'
    try:
        info = os.stat(runtime)
        if stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid():
            env.setdefault('XDG_RUNTIME_DIR', runtime)
            env.setdefault('DBUS_SESSION_BUS_ADDRESS', f'unix:path={runtime}/bus')
    except OSError:
        pass
    return env
