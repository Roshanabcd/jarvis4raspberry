"""Tests 1-8 & 18: Archive Scanner, Security Safeguards, Mixed Layouts, Conflicts, and ARM64 Compatibility."""

from __future__ import annotations

import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.app.config import ExtensionManagerConfig
from backend.services.archive_scanner import ModuleArchiveScanner
from backend.services.compatibility_analyzer import CompatibilityAnalyzer
from backend.services.install_planner import InstallationPlanner


def _make_manifest(module_id: str, port: int = 8201, prefix: str = "/api/v1/demo", deps: list[str] | None = None) -> str:
    return json.dumps(
        {
            "module_id": module_id,
            "name": f"Module {module_id}",
            "version": "1.0.0",
            "category": "testing",
            "compatible_api_version": "1.0.0",
            "entrypoints": {"api_prefix": prefix, "default_port": port},
            "required_permissions": ["demo.read"],
            "dependencies": {"jarvis_modules": deps or []},
        }
    )


class TestScannerAndCompatibility(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.scanner = ModuleArchiveScanner(ExtensionManagerConfig(max_uncompressed_bytes=1024 * 1024))
        self.analyzer = CompatibilityAnalyzer()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_01_valid_zip_inspection(self) -> None:
        zp = self.root / "valid_mod.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("mod_a/manifest.json", _make_manifest("mod-a", 8201, "/api/v1/a"))
            zf.writestr("mod_a/README.md", "# Mod A")
            zf.writestr("mod_a/requirements.txt", "fastapi>=0.92.0\nhttpx>=0.23.3\n")
            zf.writestr("mod_a/frontend/package.json", json.dumps({"dependencies": {"react": "^18.3.0"}}))
            zf.writestr("mod_a/frontend/src/main.tsx", "// ui")
            zf.writestr("mod_a/backend/app/main.py", "from fastapi import APIRouter\nr = APIRouter(prefix='/api/v1/a')\n")
            zf.writestr("mod_a/docs/API.md", "# API")
            zf.writestr("mod_a/tests/backend/test_a.py", "# test")
            zf.writestr("mod_a/.env.example", "JARVIS_MOD_A_DB_PATH=./data/a.db\n")

        res = self.scanner.scan_archive(zp)
        self.assertTrue(res["valid"])
        self.assertEqual(res["missing_mandatory_files"], [])
        self.assertIn("backend/app/main.py", res["backend_entrypoints"])
        self.assertIn("frontend/src/main.tsx", res["frontend_entrypoints"])
        self.assertIn("docs/API.md", res["api_docs"])
        self.assertIn("JARVIS_MOD_A_DB_PATH", res["env_variables"])
        self.assertIn("/api/v1/a", res["detected_api_prefixes"])

    def test_02_invalid_zip_handling(self) -> None:
        bad = self.root / "corrupt.zip"
        bad.write_bytes(b"NOT_A_REAL_ZIP_ARCHIVE")
        res = self.scanner.scan_archive(bad)
        self.assertFalse(res["valid"])
        self.assertTrue(any("BadZipFile" in e for e in res["integrity_errors"]))

    def test_03_missing_manifest_detection(self) -> None:
        zp = self.root / "no_manifest.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("README.md", "# Missing manifest")
            zf.writestr("main.py", "print('never executed')")
        res = self.scanner.scan_archive(zp)
        self.assertTrue(res["valid"])
        self.assertIn("manifest.json", res["missing_mandatory_files"])
        compat = self.analyzer.analyze_single(res, target_arch="arm64")
        self.assertTrue(any("manifest.json" in m for m in compat["missing_information"]))

    def test_04_mixed_archive_layouts(self) -> None:
        # Flat layout (no top-level wrapper folder)
        flat = self.root / "flat.zip"
        with zipfile.ZipFile(flat, "w") as zf:
            zf.writestr("manifest.json", _make_manifest("mod-flat", 8202, "/api/v1/flat"))
            zf.writestr("README.md", "# Flat")

        # Deeply nested layout
        nested = self.root / "nested.zip"
        with zipfile.ZipFile(nested, "w") as zf:
            zf.writestr("outer/inner/manifest.json", _make_manifest("mod-nested", 8203, "/api/v1/nested"))
            zf.writestr("outer/inner/README.md", "# Nested")

        r1 = self.scanner.scan_archive(flat)
        r2 = self.scanner.scan_archive(nested)
        self.assertEqual(r1["manifest"]["module_id"], "mod-flat")
        self.assertEqual(r2["manifest"]["module_id"], "mod-nested")

    def test_05_path_traversal_rejection(self) -> None:
        evil = self.root / "traversal.zip"
        with zipfile.ZipFile(evil, "w") as zf:
            zf.writestr("../../etc/passwd", "root:x:0:0:")
        res = self.scanner.scan_archive(evil)
        self.assertFalse(res["valid"])
        self.assertTrue(any("traversal" in v.lower() for v in res["security_violations"]))

    def test_06_unsafe_symlink_handling(self) -> None:
        sym = self.root / "symlink.zip"
        with zipfile.ZipFile(sym, "w") as zf:
            info = zipfile.ZipInfo("mod_sym/link_to_etc")
            info.create_system = 3  # Unix
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, "/etc/shadow")
        res = self.scanner.scan_archive(sym)
        self.assertFalse(res["valid"])
        self.assertTrue(any("symlink" in v.lower() for v in res["security_violations"]))

    def test_07_archive_size_limits(self) -> None:
        small_scanner = ModuleArchiveScanner(ExtensionManagerConfig(max_uncompressed_bytes=1024))
        big = self.root / "oversized.zip"
        with zipfile.ZipFile(big, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mod_big/payload.txt", "A" * 4096)
        res = small_scanner.scan_archive(big)
        self.assertFalse(res["valid"])
        self.assertTrue(any("exceeds limit" in v.lower() for v in res["security_violations"]))

    def test_08_and_18_dependency_conflicts_and_arm64_compatibility(self) -> None:
        zp1 = self.root / "m1.zip"
        zp2 = self.root / "m2.zip"
        with zipfile.ZipFile(zp1, "w") as zf:
            zf.writestr("m1/manifest.json", _make_manifest("mod-one", port=8250, prefix="/api/v1/shared"))
            zf.writestr("m1/README.md", "# M1")
            zf.writestr("m1/requirements.txt", "pydantic==1.10.4\npywin32==306\n")
        with zipfile.ZipFile(zp2, "w") as zf:
            zf.writestr("m2/manifest.json", _make_manifest("mod-two", port=8250, prefix="/api/v1/shared", deps=["mod-one"]))
            zf.writestr("m2/README.md", "# M2")
            zf.writestr("m2/requirements.txt", "pydantic==2.9.0\nnvidia-cuda-runtime-cu12==12.1\n")

        s1, s2 = self.scanner.scan_archive(zp1), self.scanner.scan_archive(zp2)
        c1 = self.analyzer.analyze_single(s1, target_arch="arm64")
        c2 = self.analyzer.analyze_single(s2, target_arch="arm64")

        # ARM64 unsupported checks
        self.assertTrue(any("pywin32" in u for u in c1["unsupported_dependencies"]))
        self.assertTrue(any("nvidia-cuda" in u for u in c2["unsupported_dependencies"]))

        # Cross-module conflicts & dry-run topological planning
        mods = [
            {"module_id": "mod-one", "name": "One", "version": "1.0.0", "dependencies": {"jarvis_modules": []}, "required_permissions": ["p1"], "compatibility": c1},
            {"module_id": "mod-two", "name": "Two", "version": "1.0.0", "dependencies": {"jarvis_modules": ["mod-one"]}, "required_permissions": ["p2"], "compatibility": c2},
        ]
        conflicts = self.analyzer.detect_cross_module_conflicts(mods)
        types = {c["type"] for c in conflicts}
        self.assertIn("PORT_CONFLICT", types)
        self.assertIn("API_PREFIX_CONFLICT", types)
        self.assertIn("DEPENDENCY_VERSION_CONFLICT", types)

        plan = InstallationPlanner(self.analyzer).build_plan(mods)
        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["auto_execute"])
        self.assertFalse(plan["ready_for_approval"])
        self.assertEqual([s["module_id"] for s in plan["install_order"]], ["mod-one", "mod-two"])


if __name__ == "__main__":
    unittest.main()
