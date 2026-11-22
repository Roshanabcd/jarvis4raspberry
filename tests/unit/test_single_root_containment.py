"""Unit test verifying 100% single-root self-contained operation inside JARVIS_ROOT."""

import os
import unittest
from pathlib import Path

from core.paths import (
    JARVIS_ROOT,
    MODULES_DIR,
    DATA_DIR,
    CAPTURES_DIR,
    PHOTOS_DIR,
    SCREENSHOTS_DIR,
    DOWNLOADS_DIR,
    DB_DIR,
    VOICE_SAMPLES_DIR,
    MODULE_ARCHIVES_DIR,
    NOTEBOOKS_DIR,
    LOGS_DIR,
    WORKTREES_DIR,
    is_contained_in_root,
    ensure_runtime_dirs,
)


class TestSingleRootContainment(unittest.TestCase):
    """Verify all paths, modules, tools, and extensions resolve strictly inside JARVIS_ROOT."""

    def setUp(self):
        ensure_runtime_dirs()

    def test_jarvis_root_resolution(self):
        """JARVIS_ROOT must resolve strictly to /home/roshan/.gemini/antigravity/scratch/jarvis-os."""
        expected = Path("/home/roshan/.gemini/antigravity/scratch/jarvis-os").resolve()
        self.assertEqual(JARVIS_ROOT, expected)
        self.assertTrue(JARVIS_ROOT.is_dir())

    def test_default_paths_inside_jarvis_root(self):
        """All default data, log, capture, module, and worktree paths live strictly inside JARVIS_ROOT."""
        paths_to_verify = [
            ("MODULES_DIR", MODULES_DIR),
            ("DATA_DIR", DATA_DIR),
            ("CAPTURES_DIR", CAPTURES_DIR),
            ("PHOTOS_DIR", PHOTOS_DIR),
            ("SCREENSHOTS_DIR", SCREENSHOTS_DIR),
            ("DOWNLOADS_DIR", DOWNLOADS_DIR),
            ("DB_DIR", DB_DIR),
            ("VOICE_SAMPLES_DIR", VOICE_SAMPLES_DIR),
            ("MODULE_ARCHIVES_DIR", MODULE_ARCHIVES_DIR),
            ("NOTEBOOKS_DIR", NOTEBOOKS_DIR),
            ("LOGS_DIR", LOGS_DIR),
            ("WORKTREES_DIR", WORKTREES_DIR),
        ]
        for name, p in paths_to_verify:
            self.assertTrue(
                is_contained_in_root(p),
                f"Path {name} ({p}) is NOT contained in JARVIS_ROOT ({JARVIS_ROOT})"
            )
            self.assertTrue(p.exists(), f"Directory {name} ({p}) does not exist on disk")

    def test_zero_feature_registry_external_references(self):
        """Feature registry modules must not reference Downloads or external .gemini paths."""
        from jarvis_feature_suite_loader.loader import FEATURE_REGISTRY

        self.assertGreaterEqual(len(FEATURE_REGISTRY), 42)
        for spec in FEATURE_REGISTRY:
            for key, val in spec.items():
                if isinstance(val, str):
                    self.assertNotIn(
                        "/home/roshan/Downloads",
                        val,
                        f"Module {spec.get('id')} has external Downloads reference in {key}: {val}"
                    )
                    self.assertNotIn(
                        "/home/roshan/.gemini/antigravity-cli",
                        val,
                        f"Module {spec.get('id')} has external antigravity-cli reference in {key}: {val}"
                    )

    def test_extension_catalog_containment(self):
        """Extension catalog entries must not point to external folders."""
        from fastapi import FastAPI
        from apps.apps_center.extension_catalog import extension_apps

        dummy_app = FastAPI()
        apps = extension_apps(dummy_app)
        for app_manifest in apps:
            for field in [app_manifest.route, app_manifest.roadmap, app_manifest.description]:
                if field:
                    self.assertNotIn("/home/roshan/Downloads", field)
                    self.assertNotIn("/home/roshan/.gemini/antigravity-cli", field)

    def test_capability_registry_containment(self):
        """All capabilities in CapabilityRegistry must be self-contained without external hardcodes."""
        from ai.capabilities.registry import get_capability_registry

        reg = get_capability_registry()
        caps = reg.list_capabilities()
        self.assertGreaterEqual(len(caps), 57)
        for c in caps:
            self.assertNotIn("/home/roshan/Downloads", c.route or "")
            for a in c.actions:
                for p in a.parameters:
                    if isinstance(p.default, str):
                        self.assertNotIn("/home/roshan/Downloads", p.default)
                        self.assertNotIn("/home/roshan/.gemini/antigravity-cli", p.default)

    def test_camera_manager_photos_containment(self):
        """CameraManager PICTURES_DIR must be within JARVIS_ROOT by default."""
        from tools.vision.camera_manager import PICTURES_DIR
        self.assertTrue(
            is_contained_in_root(PICTURES_DIR),
            f"PICTURES_DIR ({PICTURES_DIR}) is outside JARVIS_ROOT"
        )
        self.assertTrue(PICTURES_DIR.exists())

    def test_module_42_config_containment(self):
        """Module 42 ExtensionManagerConfig default_archives_dir must be inside JARVIS_ROOT."""
        from modules.module_42_unified_extension_manager.backend.app.config import ExtensionManagerConfig
        cfg = ExtensionManagerConfig()
        self.assertTrue(
            is_contained_in_root(cfg.default_archives_dir),
            f"ExtensionManagerConfig default_archives_dir ({cfg.default_archives_dir}) is outside JARVIS_ROOT"
        )

    def test_colab_runner_voice_samples_containment(self):
        """ColabAutoRunner default notebook and samples must be inside JARVIS_ROOT."""
        from apps.voice.colab_runner import DEFAULT_NOTEBOOK_PATH, DEFAULT_VOICE_SAMPLE, FALLBACK_VOICE_SAMPLE
        self.assertTrue(is_contained_in_root(DEFAULT_NOTEBOOK_PATH))
        self.assertTrue(is_contained_in_root(DEFAULT_VOICE_SAMPLE))
        self.assertTrue(is_contained_in_root(FALLBACK_VOICE_SAMPLE))
        self.assertTrue(Path(DEFAULT_NOTEBOOK_PATH).exists())
        self.assertTrue(Path(DEFAULT_VOICE_SAMPLE).exists())

    def test_youtube_database_containment(self):
        """YouTube database DEFAULT_DB_PATH must reside inside JARVIS_ROOT/data/."""
        from apps.youtube.database import DEFAULT_DB_PATH
        self.assertTrue(is_contained_in_root(DEFAULT_DB_PATH))


if __name__ == "__main__":
    unittest.main()
