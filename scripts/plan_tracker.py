"""Offline roadmap checks. Suggestions never authorize execution or certify dependencies."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

ROW = re.compile(r'^- \[([ xX])\] \*\*((?:JRV|JF)-\d{4})\*\*')
STATES = {'unverified', 'in_progress', 'blocked', 'implemented_pending_verification',
          'verified_offline', 'verified_live', 'deprecated'}


def parse_plan(text: str) -> dict:
    rows = {}
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        identifier = match[2]
        if identifier in rows:
            raise ValueError(f'Duplicate feature ID: {identifier}')
        metadata = {}
        for comment in re.findall(r'<!--(.*?)-->', line):
            for field in comment.split(';'):
                key, sep, value = field.partition(':')
                if sep:
                    metadata[key.strip()] = value.strip()
        status = metadata.get('status', 'unverified')
        if status not in STATES:
            raise ValueError(f'{identifier}: invalid status {status}')
        checked = match[1].lower() == 'x'
        if checked:
            if status not in {'verified_offline', 'verified_live'}:
                raise ValueError(f'{identifier}: checked without verified status')
            for required in ('verified', 'revision', 'evidence'):
                if not metadata.get(required):
                    raise ValueError(f'{identifier}: completion missing {required}')
            if not re.fullmatch(r'[0-9a-fA-F]{7,40}', metadata['revision']):
                raise ValueError(f'{identifier}: revision must be an actual Git hash')
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', metadata['verified']):
                raise ValueError(f'{identifier}: invalid verification date')
        rows[identifier] = {'status': status, 'checked': checked, 'metadata': metadata}
    if not rows:
        raise ValueError('No feature rows found')
    return rows


def check_index(root: Path, rows: dict, index: dict, compare_status: bool = True) -> list:
    errors = []
    entries = index.get('items', []) + index.get('supplemental_items', [])
    ids = [item['id'] for item in entries]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate JSON feature IDs')
    if set(ids) != set(rows):
        errors.append('PLAN and JSON feature IDs differ')
    for count, key in [('count', 'items'), ('supplemental_count', 'supplemental_items'), ('legacy_count', 'legacy_items')]:
        if index.get(count, 0) != len(index.get(key, [])):
            errors.append(f'{count} does not match {key}')
    for entry in entries:
        row = rows.get(entry['id'])
        if row is None:
            continue
        if compare_status and (entry.get('status') != row['status'] or entry.get('checked') != row['checked']):
            errors.append(f"{entry['id']}: stale JSON status; run --sync after reviewing PLAN")
        evidence = row['metadata'].get('evidence')
        if evidence:
            path = (root / evidence).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                errors.append(f"{entry['id']}: evidence must exist within repository")
    return errors


def suggestions(rows: dict, index: dict, limit: int) -> list:
    entries = index['items'] + index.get('supplemental_items', [])
    ordered = index.get('resume_order', []) + [e['id'] for e in sorted(entries, key=lambda e: (e.get('priority', 'P3'), e['id']))]
    result = []
    for identifier in ordered:
        row = rows.get(identifier)
        if row and not row['checked'] and row['status'] not in {'blocked', 'deprecated'} and identifier not in result:
            result.append(identifier)
        if len(result) >= limit:
            break
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--validate', action='store_true')
    group.add_argument('--sync', action='store_true')
    group.add_argument('--summary', action='store_true')
    group.add_argument('--next', type=int, metavar='COUNT')
    args = parser.parse_args(argv)
    try:
        if args.next is not None and not 1 <= args.next <= 100:
            raise ValueError('--next must be between 1 and 100')
        root = args.root.resolve()
        plan = (root / 'PLAN.md').read_text()
        rows = parse_plan(plan)
        index = json.loads((root / 'JARVIS_PLAN_FEATURES.json').read_text())
        errors = check_index(root, rows, index, compare_status=not args.sync)
        pairs = [('PLAN.md', 'PLAN2.md'), ('JARVIS_PLAN_FEATURES.json', 'JARVIS_PLAN_FEATURES2.json'), ('NEXT_AGENT_PROMPT.md', 'NEXT_AGENT_PROMPT2.md')]
        if not args.sync:
            for main_file, mirror in pairs:
                if (root / main_file).read_bytes() != (root / mirror).read_bytes():
                    errors.append(f'{mirror} differs from canonical {main_file}')
        if errors:
            raise ValueError('\n'.join(errors))
        if args.sync:
            for entry in index['items'] + index.get('supplemental_items', []):
                entry.update(rows[entry['id']])
            (root / 'JARVIS_PLAN_FEATURES.json').write_text(json.dumps(index, indent=2, ensure_ascii=False) + '\n')
            for main_file, mirror in pairs:
                (root / mirror).write_bytes((root / main_file).read_bytes())
            print('Synced JSON status and three handoff copies; no feature completion inferred.')
        elif args.summary:
            print(json.dumps({'primary': index['count'], 'supplemental': index.get('supplemental_count', 0),
                              'preserved_legacy': index.get('legacy_count', 0), 'checked': sum(r['checked'] for r in rows.values()),
                              'states': dict(Counter(r['status'] for r in rows.values()))}, indent=2))
        elif args.next:
            print('Navigation hints only; verify prerequisites, active owner and approvals:')
            print('\n'.join(suggestions(rows, index, args.next)))
        else:
            print(f'PASS: {len(rows)} primary/supplemental IDs, statuses, evidence references and handoff copies consistent.')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'Plan validation failed: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
