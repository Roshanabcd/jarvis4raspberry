import json
import subprocess
import sys

from tools.terminal_failure import create_diagnostic_task, redact, run_command


def test_redaction_removes_credentials_before_persistence():
    value = "token=sk-secret-value password=hunter2 bearer abc.def"
    cleaned = redact(value)
    assert "sk-secret-value" not in cleaned
    assert "hunter2" not in cleaned
    assert "abc.def" not in cleaned
    assert "[REDACTED]" in cleaned


def test_failed_command_creates_bounded_local_task_without_shell(tmp_path, capsys):
    task_dir = tmp_path / "tasks"
    code = "import sys; print('token=sk-secret-value'); print('bad', file=sys.stderr); raise SystemExit(7)"
    result = run_command([sys.executable, "-c", code], cwd=tmp_path, task_dir=task_dir)

    assert result == 7
    files = list(task_dir.glob("diag_*.json"))
    assert len(files) == 1
    task = json.loads(files[0].read_text())
    assert task["exit_code"] == 7
    assert task["repair"]["applied"] is False
    assert "sk-secret-value" not in files[0].read_text()
    assert "bad" in task["stderr"]
    assert "shell" not in task["command"]
    assert "diagnostic task" in capsys.readouterr().err


def test_success_does_not_create_task(tmp_path):
    task_dir = tmp_path / "tasks"
    result = run_command([sys.executable, "-c", "print('ok')"], cwd=tmp_path, task_dir=task_dir)
    assert result == 0
    assert not task_dir.exists()


def test_diagnostic_task_records_conservative_missing_command_hint(tmp_path):
    task = create_diagnostic_task(
        argv=["missing-command"],
        cwd=tmp_path,
        returncode=127,
        stdout="",
        stderr="missing-command: command not found",
        task_dir=tmp_path / "tasks",
    )
    assert task["diagnosis"]["category"] == "missing_command"
    assert task["repair"]["requires_review"] is True


def test_prevent_recursive_self_repair_loops(tmp_path):
    from tools.terminal_failure import run_command
    task_dir = tmp_path / "tasks"
    # Command invoking jarvis-run
    result = run_command(["jarvis-run", "--", "missing-subcmd"], cwd=tmp_path, task_dir=task_dir)
    assert not task_dir.exists()


def test_inspect_and_reproduce_diagnostic_task(tmp_path):
    from tools.terminal_failure import inspect_task, reproduce_task, run_command
    task_dir = tmp_path / "tasks"
    script = tmp_path / "failing_script.py"
    script.write_text("import sys\nprint('failing on purpose', file=sys.stderr)\nsys.exit(42)\n")

    code = run_command([sys.executable, str(script)], cwd=tmp_path, task_dir=task_dir)
    assert code == 42

    files = list(task_dir.glob("diag_*.json"))
    assert len(files) == 1
    task_id = files[0].stem

    inspected = inspect_task(task_id, task_dir=task_dir)
    assert inspected["exit_code"] == 42
    assert "failing on purpose" in inspected["stderr"]

    reproduced = reproduce_task(task_id, task_dir=task_dir)
    assert reproduced["reproduced"] is True
    assert reproduced["exit_code"] == 42


def test_propose_and_apply_minimal_diff_with_rollback(tmp_path):
    from tools.terminal_failure import apply_proposal, inspect_task, propose_fix, rollback_proposal, run_command
    task_dir = tmp_path / "tasks"
    script = tmp_path / "test_target.py"
    script.write_text("def run():\n    return 10 / 0\nrun()\n")

    code = run_command([sys.executable, str(script)], cwd=tmp_path, task_dir=task_dir)
    assert code != 0
    files = list(task_dir.glob("diag_*.json"))
    task_id = files[0].stem

    # Propose fix
    proposal = propose_fix(task_id, task_dir=task_dir, replacement_content="def run():\n    return 10 / 2\nrun()\n")
    assert proposal["status"] == "proposed"
    assert "patch_path" in proposal

    # Refuse apply without explicit confirmation
    denied = apply_proposal(task_id, task_dir=task_dir, confirm=False)
    assert denied["status"] == "approval_required"
    assert script.read_text() == "def run():\n    return 10 / 0\nrun()\n"

    # Apply with confirmation
    applied = apply_proposal(task_id, task_dir=task_dir, confirm=True)
    assert applied["status"] == "applied"
    assert applied["verified"] is True
    assert script.read_text() == "def run():\n    return 10 / 2\nrun()\n"

    # Rollback restores original
    rolled = rollback_proposal(task_id, task_dir=task_dir)
    assert rolled["status"] == "rolled_back"
    assert script.read_text() == "def run():\n    return 10 / 0\nrun()\n"


def test_security_path_traversal_prevention_in_proposal(tmp_path):
    from tools.terminal_failure import propose_fix
    task_dir = tmp_path / "tasks"
    outside_file = tmp_path.parent / "sensitive.txt"
    outside_file.write_text("secret")

    # Manually constructed task with path traversal
    from tools.terminal_failure import create_diagnostic_task
    task = create_diagnostic_task(
        argv=["cat", str(outside_file)],
        cwd=tmp_path,
        returncode=1,
        stdout="",
        stderr=f"Error in file {outside_file}",
        task_dir=task_dir,
    )
    result = propose_fix(task["task_id"], task_dir=task_dir, target_file=outside_file)
    assert result["status"] == "error"
    assert "workspace boundary" in result["error"].lower()



def test_diagnostic_file_is_private_at_creation(tmp_path, monkeypatch):
    import os
    import tools.terminal_failure as module
    real_open = os.open
    observed = []
    def checked_open(path, flags, mode=0o777, **kwargs):
        observed.append((flags, mode))
        return real_open(path, flags, mode, **kwargs)
    monkeypatch.setattr(module.os, 'open', checked_open)
    task = create_diagnostic_task(argv=['false'], cwd=tmp_path, returncode=1,
                                  stdout='', stderr='failure', task_dir=tmp_path / 'tasks')
    assert observed[-1][1] == 0o600
    assert observed[-1][0] & os.O_EXCL
    assert os.stat(task['path']).st_mode & 0o777 == 0o600


def test_reproduction_timeout_is_not_success(tmp_path):
    from tools.terminal_failure import reproduce_task
    task = create_diagnostic_task(argv=[sys.executable, '-c', 'import time; time.sleep(20)'],
        cwd=tmp_path, returncode=1, stdout='', stderr='', task_dir=tmp_path / 'tasks')
    result = reproduce_task(task['path'], timeout=0.2)
    assert result['timed_out'] is True
    assert result['reproduced'] is False


def test_reproduction_bounds_both_output_streams(tmp_path):
    from tools.terminal_failure import reproduce_task, MAX_CAPTURE_BYTES
    task = create_diagnostic_task(argv=[sys.executable, '-c',
        "import sys; print('a'*100000); print('b'*100000,file=sys.stderr); sys.exit(7)"],
        cwd=tmp_path, returncode=7, stdout='', stderr='', task_dir=tmp_path / 'tasks')
    result = reproduce_task(task['path'])
    assert result['reproduced'] is True
    assert result['output_truncated'] is True
    assert len(result['stdout']) <= MAX_CAPTURE_BYTES
    assert len(result['stderr']) <= MAX_CAPTURE_BYTES


def test_redacted_command_is_not_replayed(tmp_path, monkeypatch):
    from tools.terminal_failure import reproduce_task
    task = create_diagnostic_task(argv=['program', 'token=private-token'], cwd=tmp_path,
        returncode=1, stdout='', stderr='', task_dir=tmp_path / 'tasks')
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: (_ for _ in ()).throw(AssertionError('must not run')))
    result = reproduce_task(task['path'])
    assert result['exit_code'] is None
    assert 'redacted' in result['stderr']


def test_initial_runner_bounds_capture_but_streams_output(tmp_path, capsys):
    task_dir = tmp_path / 'tasks'
    code = run_command([sys.executable, '-c', "import sys; print('x'*100000); sys.exit(3)"],
                       cwd=tmp_path, task_dir=task_dir, capture_limit=1024)
    assert code == 3
    task = json.loads(next(task_dir.glob('*.json')).read_text())
    assert len(task['stdout']) <= 1024
    assert task['execution']['output_truncated'] is True
    assert len(capsys.readouterr().out) == 100001


def test_initial_runner_timeout_creates_truthful_diagnostic(tmp_path, capsys):
    task_dir = tmp_path / 'tasks'
    result = run_command([sys.executable, '-c', 'import time; time.sleep(20)'],
                         cwd=tmp_path, task_dir=task_dir, timeout=0.2)
    assert result == 124
    task = json.loads(next(task_dir.glob('*.json')).read_text())
    assert task['execution']['timed_out'] is True
    assert 'timeout' in capsys.readouterr().err


def test_nested_runner_preserves_output_without_duplicate_task(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv('JARVIS_DIAGNOSTIC_ACTIVE', '1')
    task_dir = tmp_path / 'tasks'
    result = run_command([sys.executable, '-c', "import sys; print('nested'); sys.exit(4)"],
                         cwd=tmp_path, task_dir=task_dir)
    assert result == 4
    assert capsys.readouterr().out == 'nested\n'
    assert not task_dir.exists()


def _reviewed_repair(tmp_path):
    from tools.terminal_failure import propose_fix
    target = tmp_path / 'target.py'
    target.write_text('raise SystemExit(1)\n')
    task = create_diagnostic_task(argv=[sys.executable, str(target)], cwd=tmp_path,
        returncode=1, stdout='', stderr='', task_dir=tmp_path / 'tasks')
    propose_fix(task['path'], target_file=target, replacement_content='raise SystemExit(0)\n')
    return target, task['path']


def test_apply_preserves_edits_made_after_review(tmp_path):
    from tools.terminal_failure import apply_proposal
    target, task = _reviewed_repair(tmp_path)
    target.write_text('# newer user edit\n')
    assert apply_proposal(task, confirm=True)['status'] == 'conflict'
    assert target.read_text() == '# newer user edit\n'
    assert not list(tmp_path.glob('*.orig.*'))


def test_rollback_preserves_newer_edits(tmp_path):
    from tools.terminal_failure import apply_proposal, rollback_proposal
    target, task = _reviewed_repair(tmp_path)
    assert apply_proposal(task, confirm=True)['verified']
    target.write_text('# keep this edit\n')
    assert rollback_proposal(task)['status'] == 'conflict'
    assert target.read_text() == '# keep this edit\n'
    assert list(tmp_path.glob('*.orig.*'))


def test_missing_backup_does_not_claim_rollback(tmp_path):
    from tools.terminal_failure import apply_proposal, rollback_proposal
    from pathlib import Path
    target, task = _reviewed_repair(tmp_path)
    result = apply_proposal(task, confirm=True)
    Path(result['backup_path']).unlink()
    assert rollback_proposal(task)['status'] == 'error'
    assert target.read_text() == 'raise SystemExit(0)\n'


def test_apply_rechecks_symlink_boundary(tmp_path):
    from tools.terminal_failure import apply_proposal
    workspace = tmp_path / 'project'
    workspace.mkdir()
    target, task = _reviewed_repair(workspace)
    outside = tmp_path / 'outside.py'
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    assert apply_proposal(task, confirm=True)['status'] == 'error'
    assert outside.read_text() == 'raise SystemExit(1)\n'


def test_cli_review_apply_and_rollback_workflow(tmp_path, capsys):
    from tools.terminal_failure import main
    script = tmp_path / 'broken.py'
    script.write_text('raise SystemExit(7)\n')
    replacement = tmp_path / 'replacement.txt'
    replacement.write_text('raise SystemExit(0)\n')
    assert main(['--cwd', str(tmp_path), '--', sys.executable, str(script)]) == 7
    task = next((tmp_path / '.jarvis' / 'diagnostics').glob('*.json'))
    assert main(['--propose', str(task), '--target', 'broken.py', '--replacement', str(replacement)]) == 0
    assert script.read_text() == 'raise SystemExit(7)\n'
    assert main(['--apply', str(task)]) == 2
    assert main(['--apply', str(task), '--confirm']) == 0
    assert script.read_text() == 'raise SystemExit(0)\n'
    assert main(['--rollback', str(task)]) == 0
    assert script.read_text() == 'raise SystemExit(7)\n'
    assert main(['--rollback', str(task)]) == 1
    assert 'rolled_back' in capsys.readouterr().out


def test_interrupted_verification_retains_rollback_information(tmp_path, monkeypatch):
    import pytest
    import tools.terminal_failure as module
    target, task = _reviewed_repair(tmp_path)
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt()
    monkeypatch.setattr(module, 'reproduce_task', interrupt)
    with pytest.raises(KeyboardInterrupt):
        module.apply_proposal(task, confirm=True)
    saved = module.inspect_task(task)
    assert saved['repair']['applied'] is True
    assert saved['repair']['verified'] is False
    assert module.rollback_proposal(task)['status'] == 'rolled_back'
    assert target.read_text() == 'raise SystemExit(1)\n'


def test_cli_rejects_ambiguous_action_before_execution(tmp_path):
    import pytest
    from tools.terminal_failure import main
    with pytest.raises(SystemExit) as exc:
        main(['--inspect', 'unused', '--', sys.executable, '-c', 'raise SystemExit(0)'])
    assert exc.value.code == 2


def test_cli_reports_missing_task_without_traceback(tmp_path, capsys):
    from tools.terminal_failure import main
    assert main(['--inspect', str(tmp_path / 'missing.json')]) == 1
    assert 'Traceback' not in capsys.readouterr().err


def test_changed_replacement_requires_new_review(tmp_path):
    from tools.terminal_failure import apply_proposal
    target, task = _reviewed_repair(tmp_path)
    from pathlib import Path
    data = json.loads(Path(task).read_text())
    data['repair']['replacement_content'] = '# unexpected replacement\n'
    Path(task).write_text(json.dumps(data))
    assert apply_proposal(task, confirm=True)['status'] == 'conflict'
    assert target.read_text() == 'raise SystemExit(1)\n'
