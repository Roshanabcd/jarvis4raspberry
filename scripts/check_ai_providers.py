#!/usr/bin/env python3
"""Print a credential-free provider report. --live sends small paid API requests."""
import argparse
import json
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Send one synthetic prompt per configured cloud provider')
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env', override=False)
    from ai.brain import JARVISBrain
    from ai.providers.credentials import ENV_KEYS, usable_key
    from ai.providers.diagnostics import probe_provider
    brain = object.__new__(JARVISBrain)
    brain._providers = []
    brain._init_providers()
    report = []
    for provider in brain._providers:
        if provider.name not in ENV_KEYS:
            continue
        if args.live:
            report.append(probe_provider(provider))
        else:
            configured = usable_key(provider.api_key)
            report.append({'provider': provider.name, 'model': provider.model,
                           'enabled': provider.enabled,
                           'credential_configured': configured,
                           'status': 'not_tested' if configured else 'missing_key'})
    print(json.dumps({'live_requested': args.live, 'results': report}, indent=2))


if __name__ == '__main__':
    main()
