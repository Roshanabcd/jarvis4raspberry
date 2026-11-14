#!/usr/bin/env python3
"""Print a bounded developer automation status report.

Reports documented local CLI capabilities and (optionally) configured provider
status. This script performs read-only checks and never exposes credentials.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-providers",
        action="store_true",
        help="Include configured provider status from the local JARVIS brain",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON (default)",
    )
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)

    brain = None
    if args.with_providers:
        try:
            from dotenv import load_dotenv

            load_dotenv(ROOT / ".env", override=False)
            from ai.brain import JARVISBrain

            brain = object.__new__(JARVISBrain)
            brain._providers = []
            brain._init_providers()
        except Exception as exc:
            print(json.dumps({"error": f"provider_status_unavailable:{type(exc).__name__}"}))
            return 1

    from ai.providers.capabilities import build_developer_automation_report

    report = build_developer_automation_report(brain=brain)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
