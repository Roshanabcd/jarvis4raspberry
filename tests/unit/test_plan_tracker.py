"""Roadmap integrity checks use only small offline fixtures."""
import pytest
from scripts.plan_tracker import parse_plan, check_index, suggestions

ROW = '- [ ] **JRV-0001** `P0` — Example'


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        parse_plan(ROW + '\n' + ROW)


@pytest.mark.parametrize('suffix', ['', '<!-- status: verified_live -->', '<!-- status: complete -->'])
def test_checked_without_full_verification_rejected(suffix):
    with pytest.raises(ValueError):
        parse_plan(ROW.replace('[ ]', '[x]') + suffix)


def test_offline_evidence_does_not_check_live_item():
    rows = parse_plan(ROW + ' <!-- status: verified_offline -->')
    assert not rows['JRV-0001']['checked']


def test_stale_json_detected(tmp_path):
    rows = parse_plan(ROW)
    index = {'count': 1, 'items': [{'id': 'JRV-0001', 'status': 'verified_live', 'checked': True}]}
    assert any('stale JSON' in e for e in check_index(tmp_path, rows, index))


def test_missing_or_outside_evidence_rejected(tmp_path):
    for path in ['missing.txt', '../outside.txt']:
        rows = parse_plan(ROW + f' <!-- evidence: {path} -->')
        index = {'count': 1, 'items': [{'id': 'JRV-0001', 'status': 'unverified', 'checked': False}]}
        assert any('evidence' in e for e in check_index(tmp_path, rows, index))


def test_next_respects_resume_order_and_skips_blocked_and_checked():
    rows = {f'JRV-000{i}': {'checked': i == 2, 'status': 'blocked' if i == 3 else 'unverified'} for i in range(1, 5)}
    index = {'items': [{'id': k, 'priority': 'P0'} for k in rows], 'resume_order': ['JRV-0003', 'JRV-0002', 'JRV-0004']}
    assert suggestions(rows, index, 2) == ['JRV-0004', 'JRV-0001']


def test_valid_checked_evidence(tmp_path):
    (tmp_path / 'evidence.txt').write_text('offline fixture')
    rows = parse_plan(ROW.replace('[ ]', '[x]') + ' <!-- status: verified_offline; revision: abc1234; verified: 2026-11-22; evidence: evidence.txt -->')
    index = {'count': 1, 'items': [{'id': 'JRV-0001', 'status': 'verified_offline', 'checked': True}]}
    assert check_index(tmp_path, rows, index) == []
