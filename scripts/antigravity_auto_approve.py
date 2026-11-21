#!/usr/bin/env python3
"""
JARVIS OS — Antigravity Auto-Approver CLI
Usage:
    python3 scripts/antigravity_auto_approve.py --apply-settings
    python3 scripts/antigravity_auto_approve.py --once
    python3 scripts/antigravity_auto_approve.py --daemon
    python3 scripts/antigravity_auto_approve.py --status
"""

import os
import sys
import time
import argparse
import asyncio
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure execution in project venv if available
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python3"
if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from tools.desktop.antigravity_approver import (
    apply_antigravity_settings,
    scan_and_auto_approve_cdp,
    antigravity_supervisor,
)


def main():
    parser = argparse.ArgumentParser(description="JARVIS Antigravity Auto-Approver & Settings Utility")
    parser.add_argument("--apply-settings", action="store_true", help="Apply eager auto-execution and PreToolUse hook")
    parser.add_argument("--once", action="store_true", help="Scan open Antigravity conversations once and auto-accept option 1")
    parser.add_argument("--daemon", action="store_true", help="Run supervisor daemon continuously in foreground")
    parser.add_argument("--status", action="store_true", help="Display Antigravity configuration & supervisor status")
    parser.add_argument("--port", type=int, default=9333, help="Antigravity CDP remote debugging port (default: 9333)")

    args = parser.parse_args()

    if args.apply_settings:
        print("[JARVIS] Applying Antigravity IDE auto-execution settings...")
        res = apply_antigravity_settings()
        if res["success"]:
            print("  ✓ Settings applied successfully:")
            for item in res["applied"]:
                print(f"    • {item}")
        else:
            print("  ✗ Some settings failed:")
            for err in res["errors"]:
                print(f"    • {err}")
        return

    if args.once:
        print(f"[JARVIS] Scanning Antigravity IDE (CDP port {args.port})...")
        res = asyncio.run(scan_and_auto_approve_cdp(cdp_port=args.port))
        if res.get("success"):
            actions = res.get("actions", [])
            print(f"  ✓ Scan completed. Actions taken: {len(actions)}")
            for act in actions:
                print(f"    • [{act.get('target')}] {act.get('page')}: {act.get('action')}")
        else:
            print(f"  ✗ Scan failed: {res.get('error')}")
        return

    if args.status:
        st = antigravity_supervisor.get_status()
        print("[JARVIS] Antigravity Supervisor Status:")
        for k, v in st.items():
            print(f"  {k}: {v}")
        return

    if args.daemon:
        print(f"[JARVIS] Starting Antigravity Auto-Approver Daemon on CDP port {args.port} (Ctrl+C to stop)...")
        apply_antigravity_settings()
        antigravity_supervisor.cdp_port = args.port
        antigravity_supervisor.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[JARVIS] Stopping supervisor daemon...")
            antigravity_supervisor.stop()
            print("Stopped.")
        return

    # Default action if no flag specified: apply settings and run once
    print("[JARVIS] Applying Antigravity settings and scanning open conversations...")
    set_res = apply_antigravity_settings()
    for item in set_res.get("applied", []):
        print(f"  • {item}")
    scan_res = asyncio.run(scan_and_auto_approve_cdp(cdp_port=args.port))
    print(f"  • Scanned Antigravity: {len(scan_res.get('actions', []))} prompts auto-approved.")


if __name__ == "__main__":
    main()
