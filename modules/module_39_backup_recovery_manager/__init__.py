"""JARVIS OS Extension Module #39: Backup & Recovery Manager."""

from __future__ import annotations

from modules.module_39_backup_recovery_manager.backend.app.main import create_app, mount_module

__version__ = "1.0.0"
__module_id__ = "module_39_backup_recovery_manager"
__module_name__ = "Backup & Recovery Manager"

__all__ = ["create_app", "mount_module", "__version__", "__module_id__", "__module_name__"]
