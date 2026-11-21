#!/usr/bin/env python3
"""Runnable end-to-end demonstration of JARVIS Module 43 — Autonomous Screen Guardian.

Demonstrates:
1. Rendering a real PNG image containing a Python ZeroDivisionError traceback.
2. Running real local Tesseract OCR on the image.
3. Contextual error detection & notification creation.
4. Repairing a disposable buggy Python workspace via ReferenceLocalRepairAgent.
5. Verifying the fix with real focused unittest execution -> outcome='verified_fixed'.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_43_autonomous_screen_guardian.backend.app.config import ScreenGuardianConfig
from modules.module_43_autonomous_screen_guardian.backend.services.guardian_service import ScreenGuardianService


def render_traceback_png(lines: list[str]) -> bytes:
    img = Image.new("RGB", (980, 260), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 24
    for line in lines:
        draw.text((24, y), line, fill=(0, 0, 0))
        y += 28
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="jarvis_m43_demo_") as tmp:
        tmp_path = Path(tmp)
        repo_dir = tmp_path / "buggy_app"
        repo_dir.mkdir(parents=True, exist_ok=True)
        tests_dir = repo_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Create a disposable buggy Python module + focused unit test
        (repo_dir / "calculator.py").write_text(
            "def divide(a, b):\n    return a / b\n",
            encoding="utf-8",
        )
        (tests_dir / "test_calculator.py").write_text(
            "import unittest\n"
            "from calculator import divide\n\n"
            "class TestCalc(unittest.TestCase):\n"
            "    def test_divide_by_zero_safe(self):\n"
            "        self.assertEqual(divide(10, 0), 0.0)\n"
            "    def test_divide_normal(self):\n"
            "        self.assertEqual(divide(10, 2), 5.0)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8",
        )

        config = ScreenGuardianConfig(
            db_path=str(tmp_path / "data" / "guardian_demo.db"),
            trusted_workspaces=[str(repo_dir.resolve())],
        )
        service = ScreenGuardianService(config=config)

        # 1. Start monitoring with explicit user consent
        service.capture.start(explicit_consent=True, monitor_id="primary", interval_sec=2.0)

        # 2. Render traceback PNG and run real Tesseract OCR + Error Detection
        png_bytes = render_traceback_png(
            [
                "Traceback (most recent call last):",
                "  File 'calculator.py', line 2, in divide",
                "    return a / b",
                "ZeroDivisionError: division by zero",
            ]
        )
        analysis = await service.analyze_frame(
            image_base64=base64.b64encode(png_bytes).decode("ascii"),
            source_app="VS Code Terminal",
            window_title="buggy_app - Terminal",
            use_vision_model=False,
        )

        err_id = analysis["errors"][0]["error_id"] if analysis["errors"] else None

        # 3. Create, approve, and execute authorized repair with focused test verification
        job = service.repair.create_repair_request(
            {
                "error_id": err_id,
                "mode": "assisted_repair",
                "agent_id": "reference_local_repair_agent",
                "workspace_path": str(repo_dir),
                "summary": "Fix ZeroDivisionError in calculator.py",
                "error_context": analysis["ocr"]["text"] or "ZeroDivisionError: division by zero",
            }
        )
        service.repair.approve_repair(job["repair_id"], "approve", reviewer="demo_user", notes="Approved demo repair")
        result = await service.repair.execute_repair(
            job["repair_id"],
            target_files=["calculator.py"],
            test_command=[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        )

        service.capture.stop()

        summary = {
            "ocr_engine": analysis["ocr"]["engine"],
            "ocr_available": analysis["ocr"]["available"],
            "ocr_excerpt": analysis["ocr"]["text"].strip().splitlines()[:4],
            "errors_detected": len(analysis["errors"]),
            "notifications_created": len(analysis["notifications_created"]),
            "repair_outcome": result["outcome"],
            "verification_passed": result["test_results"]["passed"],
            "diff_preview": (result.get("diff_text") or "").splitlines()[:8],
        }
        print(json.dumps(summary, indent=2))
        assert result["outcome"] == "verified_fixed", f"Expected verified_fixed, got {result['outcome']}"


if __name__ == "__main__":
    asyncio.run(main())
