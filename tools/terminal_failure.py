"""Safe, opt-in command execution with local failure diagnostics.

This module intentionally runs only the argv supplied by the caller. It does
not inspect shell history, invoke a shell, transmit output, or apply repairs.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence

MAX_CAPTURE_BYTES = 16_384
MAX_TASK_BYTES = 64_000
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|token|password|secret|authorization)\b\s*[:=]\s*(['\"]?)[^\s,'\";]+"),
    re.compile(r"(?i)\b(?:sk|ghp|github_pat|xox[baprs])[-_a-z0-9]{8,}\b"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+"),
)


def _write_private(path: Path, text: str) -> None:
    """Replace diagnostic metadata atomically, private from its first byte."""
    fd, temporary = tempfile.mkstemp(prefix='.jarvis-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def redact(text: str, *, max_bytes: int = MAX_CAPTURE_BYTES) -> str:
    """Redact common credential-shaped values and bound UTF-8 output."""
    value = text or ""
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore") + "\n[truncated]"


def _git_metadata(cwd: Path) -> Dict[str, Any]:
    """Collect non-sensitive project metadata without reading history or files."""
    metadata: Dict[str, Any] = {}
    for key, command in (
        ("branch", ["git", "branch", "--show-current"]),
        ("status", ["git", "status", "--porcelain", "--untracked-files=no"]),
    ):
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode == 0:
            if key == "status":
                metadata[key] = result.stdout.splitlines()[:40]
            else:
                metadata[key] = result.stdout.strip()[:120]
    return metadata


def _diagnosis(argv: Sequence[str], returncode: int, output: str) -> Dict[str, str]:
    """Provide a conservative local hint, never present it as a root-cause proof."""
    lowered = output.lower()
    if returncode == 127 or "command not found" in lowered:
        return {
            "category": "missing_command",
            "explanation": "The requested executable was not found on PATH.",
            "next_step": "Verify the command name and local installation; do not install automatically.",
        }
    if "modulenotfounderror" in lowered or "no module named" in lowered:
        return {
            "category": "missing_dependency",
            "explanation": "The process reported a missing Python module or dependency.",
            "next_step": "Inspect the project environment and dependency manifest before installing anything.",
        }
    if "syntaxerror" in lowered:
        return {
            "category": "syntax_error",
            "explanation": "The process reported a Python syntax error.",
            "next_step": "Inspect the reported file and line, reproduce with the same command, then propose a minimal diff.",
        }
    if returncode < 0:
        return {
            "category": "terminated_by_signal",
            "explanation": f"The process was terminated by signal {-returncode}.",
            "next_step": "Check the process owner and system logs before retrying.",
        }
    return {
        "category": "command_failed",
        "explanation": f"The command exited with status {returncode}; the captured output is evidence, not instructions.",
        "next_step": "Inspect the reported files and reproduce this exact argv before proposing a minimal diff.",
    }


def create_diagnostic_task(
    *,
    argv: Sequence[str],
    cwd: Path,
    returncode: int,
    stdout: str,
    stderr: str,
    task_dir: Optional[Path] = None,
    execution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist a bounded, redacted diagnostic task locally and return its record."""
    task_root = task_dir or (cwd / ".jarvis" / "diagnostics")
    task_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    task_id = f"diag_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    combined = "\n".join(part for part in (stdout, stderr) if part)
    record: Dict[str, Any] = {
        "task_id": task_id,
        "status": "open",
        "created_at": time.time(),
        "command": [redact(item, max_bytes=2_048) for item in argv],
        "cwd": str(cwd),
        "exit_code": returncode,
        "stdout": redact(stdout),
        "stderr": redact(stderr),
        "metadata": _git_metadata(cwd),
        "diagnosis": _diagnosis(argv, returncode, redact(combined)),
        "repair": {
            "applied": False,
            "requires_review": True,
            "scope": str(cwd),
        },
    }
    if execution is not None:
        record['execution'] = {
            'timed_out': bool(execution.get('timed_out', False)),
            'output_truncated': bool(execution.get('output_truncated', False)),
        }
    payload = json.dumps(record, indent=2, sort_keys=True)
    if len(payload.encode("utf-8")) > MAX_TASK_BYTES:
        record["stdout"] = redact(stdout, max_bytes=4_096)
        record["stderr"] = redact(stderr, max_bytes=4_096)
        payload = json.dumps(record, indent=2, sort_keys=True)
    path = task_root / f"{task_id}.json"
    # Create privately from the first byte; never overwrite an existing path
    # (including a symlink) before changing its permissions.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(payload + "\n")
    record["path"] = str(path)
    return record


def _resolve_task_file(task_id_or_path: str | Path, task_dir: Optional[Path] = None, cwd: Optional[Path] = None) -> Path:
    p = Path(task_id_or_path)
    if p.is_file():
        return p
    search_dirs = []
    if task_dir:
        search_dirs.append(Path(task_dir))
    search_dirs.append((cwd or Path.cwd()) / ".jarvis" / "diagnostics")
    for d in search_dirs:
        if not d.is_dir():
            continue
        candidate = d / f"{p.stem}.json"
        if candidate.is_file():
            return candidate
        matches = list(d.glob(f"*{task_id_or_path}*.json"))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"Diagnostic task not found: {task_id_or_path}")


def inspect_task(task_id_or_path: str | Path, *, task_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Inspect an existing local diagnostic task record."""
    task_file = _resolve_task_file(task_id_or_path, task_dir=task_dir)
    with task_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["task_file"] = str(task_file)
    return data


def reproduce_task(task_id_or_path: str | Path, *, task_dir: Optional[Path] = None,
                   timeout: float = 30.0) -> Dict[str, Any]:
    """Re-run the exact recorded command in its recorded directory without applying repairs."""
    task = inspect_task(task_id_or_path, task_dir=task_dir)
    cmd = task.get("command", [])
    cwd = Path(task.get("cwd", ".")).resolve()
    if (not isinstance(cmd, list) or not cmd or
            any(not isinstance(arg, str) or '\x00' in arg or '[REDACTED]' in arg for arg in cmd)):
        return {'reproduced': False, 'exit_code': None, 'stdout': '',
                'stderr': 'Recorded command is invalid or redacted; supply a fresh command explicitly.'}
    try:
        res = _bounded_reproduction(cmd, cwd, timeout)
        reproduced = not res['timed_out'] and res['exit_code'] == task.get("exit_code")
        return {
            "reproduced": reproduced,
            **res,
        }
    except Exception as exc:
        return {
            "reproduced": False,
            "exit_code": 127,
            "stdout": "",
            "stderr": redact(str(exc)),
        }


def _bounded_reproduction(command, cwd, timeout, *, capture_limit=MAX_CAPTURE_BYTES,
                          echo=False, stdin=subprocess.DEVNULL, env=None):
    """Drain both pipes while bounding memory and the lifetime of the process group."""
    import math
    import selectors
    import signal
    import codecs
    if not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise ValueError('Reproduction timeout must be between 0 and 300 seconds')
    if type(capture_limit) is not int or not 1 <= capture_limit <= MAX_CAPTURE_BYTES:
        raise ValueError(f'Capture limit must be between 1 and {MAX_CAPTURE_BYTES} bytes')
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    decoders = {name: codecs.getincrementaldecoder('utf-8')(errors='replace') for name in buffers}
    truncated = False
    timed_out = False
    process = subprocess.Popen(command, cwd=cwd, stdin=stdin, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, 'stdout')
            selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
            while selector.get_map() or process.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fileobj.fileno(), 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        if echo:
                            stream = getattr(sys, key.data)
                            stream.write(decoders[key.data].decode(b'', final=True))
                            stream.flush()
                        continue
                    if echo:
                        stream = getattr(sys, key.data)
                        stream.write(decoders[key.data].decode(chunk))
                        stream.flush()
                    buffer = buffers[key.data]
                    room = capture_limit - len(buffer)
                    buffer.extend(chunk[:room])
                    truncated |= len(chunk) > room
    finally:
        # Also clean up descendants that inherited pipes or outlived their parent.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdout.close()
        process.stderr.close()
    return {'exit_code': process.returncode, 'timed_out': timed_out,
            'output_truncated': truncated,
            **{name: redact(bytes(value).decode('utf-8', errors='replace'))
               for name, value in buffers.items()}}


def propose_fix(
    task_id_or_path: str | Path,
    *,
    task_dir: Optional[Path] = None,
    replacement_content: Optional[str] = None,
    target_file: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Inspect failure evidence, validate workspace boundaries, and propose a minimal diff."""
    task = inspect_task(task_id_or_path, task_dir=task_dir)
    cwd_resolved = Path(task.get("cwd", ".")).resolve()
    if task.get('repair', {}).get('applied'):
        return {'status': 'conflict', 'error': 'Roll back or keep the applied repair before creating another task'}

    resolved_target: Optional[Path] = None
    if target_file:
        candidate = Path(target_file)
        resolved_target = (candidate if candidate.is_absolute() else cwd_resolved / candidate).resolve()
    else:
        combined = f"{task.get('stdout', '')}\n{task.get('stderr', '')}"
        m = re.search(r'File "([^"]+)", line \d+', combined)
        if m:
            cand = Path(m.group(1))
            resolved_target = cand if cand.is_absolute() else (cwd_resolved / cand).resolve()

    if not resolved_target:
        return {"status": "error", "error": "No target source file could be identified for repair proposal"}

    # Security: enforce authorized workspace boundary
    try:
        resolved_target.relative_to(cwd_resolved)
    except ValueError:
        return {
            "status": "error",
            "error": f"Target file is outside the authorized workspace boundary: {resolved_target}",
        }

    if not resolved_target.is_file():
        return {"status": "error", "error": f"Target file does not exist: {resolved_target}"}

    original_bytes = resolved_target.read_bytes()
    orig_content = original_bytes.decode('utf-8')
    if replacement_content is None:
        return {"status": "error", "error": "Replacement content required for diff generation"}

    diff_lines = list(difflib.unified_diff(
        orig_content.splitlines(keepends=True),
        replacement_content.splitlines(keepends=True),
        fromfile=str(resolved_target),
        tofile=str(resolved_target),
    ))
    diff_text = "".join(diff_lines)

    task_file = Path(task["task_file"])
    patch_path = task_file.with_suffix(".patch")
    _write_private(patch_path, diff_text)

    task["repair"] = {
        "status": "proposed",
        "patch_path": str(patch_path),
        "target_file": str(resolved_target),
        "diff": diff_text,
        "replacement_content": replacement_content,
        "original_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "replacement_sha256": hashlib.sha256(replacement_content.encode('utf-8')).hexdigest(),
        "applied": False,
        "requires_review": True,
    }
    _write_private(task_file, json.dumps(task, indent=2, sort_keys=True) + "\n")
    return {
        "status": "proposed",
        "task_id": task.get("task_id"),
        "patch_path": str(patch_path),
        "diff": diff_text,
    }


def apply_proposal(
    task_id_or_path: str | Path,
    *,
    task_dir: Optional[Path] = None,
    confirm: bool = False,
) -> Dict[str, Any]:
    """Apply proposed minimal diff only with explicit operator confirmation and automated verification."""
    task = inspect_task(task_id_or_path, task_dir=task_dir)
    repair = task.get("repair", {})
    if not confirm:
        return {
            "status": "approval_required",
            "message": "Applying a patch requires explicit operator review and confirmation.",
            "diff": repair.get("diff", ""),
        }

    target_file = repair.get("target_file")
    replacement_content = repair.get("replacement_content")
    if not target_file or replacement_content is None:
        return {"status": "error", "error": "No proposal found to apply"}

    target_path = Path(target_file).resolve()
    try:
        target_path.relative_to(Path(task['cwd']).resolve())
    except ValueError:
        return {'status': 'error', 'error': 'Target is outside the workspace boundary'}
    if repair.get('applied'):
        return {'status': 'error', 'error': 'Proposal is already applied'}
    original_bytes = target_path.read_bytes()
    if hashlib.sha256(original_bytes).hexdigest() != repair.get('original_sha256'):
        return {'status': 'conflict', 'error': 'Source changed since review; generate a fresh proposal'}
    if hashlib.sha256(replacement_content.encode('utf-8')).hexdigest() != repair.get('replacement_sha256'):
        return {'status': 'conflict', 'error': 'Replacement changed since proposal; review a fresh diff'}
    task_id = task.get("task_id", "task")
    if not re.fullmatch(r'[A-Za-z0-9_-]+', task_id):
        return {'status': 'error', 'error': 'Invalid task identifier'}
    backup_path = target_path.parent / f"{target_path.name}.orig.{task_id}"

    try:
        fd = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return {'status': 'conflict', 'error': 'Backup already exists; inspect it before retrying'}
    with os.fdopen(fd, 'wb') as stream:
        stream.write(original_bytes)

    target_path.write_text(replacement_content, encoding="utf-8")
    # Save rollback information before verification, which may be interrupted.
    task['repair'].update(applied=True, verified=False, backup_path=str(backup_path))
    task_file = Path(task['task_file'])
    _write_private(task_file, json.dumps(task, indent=2, sort_keys=True) + '\n')
    rep = reproduce_task(task_id_or_path, task_dir=task_dir)
    verified = rep.get("exit_code") == 0 and not rep.get("timed_out", False)

    task["repair"]["applied"] = True
    task["repair"]["verified"] = verified
    task["repair"]["exit_code"] = rep.get("exit_code")
    task["repair"]["backup_path"] = str(backup_path)

    task_file = Path(task["task_file"])
    _write_private(task_file, json.dumps(task, indent=2, sort_keys=True) + "\n")

    return {
        "status": "applied",
        "verified": verified,
        "exit_code": rep.get("exit_code"),
        "backup_path": str(backup_path),
    }


def rollback_proposal(task_id_or_path: str | Path, *, task_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Roll back applied proposal from checkpoint file."""
    task = inspect_task(task_id_or_path, task_dir=task_dir)
    repair = task.get("repair", {})
    backup_path_str = repair.get("backup_path")
    target_file_str = repair.get("target_file")
    if not backup_path_str or not target_file_str:
        return {"status": "error", "error": "No backup found for rollback"}

    backup_path = Path(backup_path_str).resolve()
    target_path = Path(target_file_str).resolve()
    try:
        target_path.relative_to(Path(task['cwd']).resolve())
        backup_path.relative_to(Path(task['cwd']).resolve())
    except ValueError:
        return {'status': 'error', 'error': 'Rollback path is outside the workspace boundary'}
    if not repair.get('applied') or not backup_path.is_file():
        return {'status': 'error', 'error': 'Applied proposal and original backup are required'}
    original_bytes = backup_path.read_bytes()
    if hashlib.sha256(original_bytes).hexdigest() != repair.get('original_sha256'):
        return {'status': 'conflict', 'error': 'Backup changed; rollback refused'}
    if not target_path.is_file() or hashlib.sha256(target_path.read_bytes()).hexdigest() != repair.get('replacement_sha256'):
        return {'status': 'conflict', 'error': 'Source changed after repair; rollback would overwrite newer edits'}
    target_path.write_bytes(original_bytes)
    backup_path.unlink()

    task["repair"]["applied"] = False
    task["repair"]["status"] = "rolled_back"
    task_file = Path(task["task_file"])
    _write_private(task_file, json.dumps(task, indent=2, sort_keys=True) + "\n")

    return {"status": "rolled_back", "target_file": target_file_str}


def run_command(
    argv: Sequence[str], *, cwd: Optional[Path] = None,
    task_dir: Optional[Path] = None, capture_limit: int = MAX_CAPTURE_BYTES,
    timeout: float = 300.0,
) -> int:
    """Stream an explicit command locally, retaining bounded failure evidence."""
    if isinstance(argv, (str, bytes)) or not argv or any(not isinstance(item, str) or '\x00' in item for item in argv) or not argv[0]:
        raise ValueError("A non-empty command argv is required")
    working_dir = (cwd or Path.cwd()).resolve()
    nested = os.environ.get('JARVIS_DIAGNOSTIC_ACTIVE') == '1'
    wrapper = Path(argv[0]).name == 'jarvis-run' or list(argv[1:3]) == ['-m', 'tools.terminal_failure']
    env = dict(os.environ, JARVIS_DIAGNOSTIC_ACTIVE='1')
    try:
        result = _bounded_reproduction(list(argv), working_dir, timeout,
            capture_limit=capture_limit, echo=True, stdin=None, env=env)
    except KeyboardInterrupt:
        print("JARVIS command interrupted; no repair was applied.", file=sys.stderr)
        return 130
    except OSError as exc:
        result = {'exit_code': 127, 'stdout': '', 'stderr': redact(str(exc)),
                  'timed_out': False, 'output_truncated': False}
        print(result['stderr'], file=sys.stderr)
    code = 124 if result['timed_out'] else result['exit_code']
    if result['timed_out']:
        print(f"JARVIS command exceeded its {timeout:g}-second timeout.", file=sys.stderr)
    if code != 0 and not nested and not wrapper:
        record = create_diagnostic_task(argv=argv, cwd=working_dir, returncode=code,
            stdout=result['stdout'], stderr=result['stderr'], task_dir=task_dir,
            execution=result)
        print(f"JARVIS diagnostic task {record['task_id']} created at {record['path']}. "
              "No repair was applied.", file=sys.stderr)
    return code


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis-run",
        description="Run one explicit command, inspect failures, or manage reviewed repairs.")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--task-dir", type=Path, help="Directory containing diagnostic tasks")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Deadline: 300 seconds for commands, 30 for reproduction; maximum 300")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--inspect", metavar="TASK_ID")
    actions.add_argument("--reproduce", metavar="TASK_ID")
    actions.add_argument("--propose", metavar="TASK_ID", help="Create a diff without changing the source")
    actions.add_argument("--apply", metavar="TASK_ID")
    actions.add_argument("--rollback", metavar="TASK_ID")
    parser.add_argument("--target", type=Path, help="Source file for a proposal, relative to task workspace")
    parser.add_argument("--replacement", type=Path, help="UTF-8 file containing proposed replacement text")
    parser.add_argument("--confirm", action="store_true", help="Apply only after reviewing the proposed diff")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(list(argv) if argv is not None else None)
    import math
    if args.timeout is not None and (not math.isfinite(args.timeout) or not 0 < args.timeout <= 300):
        parser.error("--timeout must be positive, finite, and no greater than 300")
    action = any((args.inspect, args.reproduce, args.propose, args.apply, args.rollback))
    if action and args.command:
        parser.error("choose a task action or a command, not both")
    if args.propose and not args.replacement:
        parser.error("--propose requires --replacement")
    if (args.replacement or args.target) and not args.propose:
        parser.error("--replacement and --target are only valid with --propose")
    if args.confirm and not args.apply:
        parser.error("--confirm is only valid with --apply")
    task_dir = args.task_dir or args.cwd / '.jarvis' / 'diagnostics'
    try:
        if args.inspect:
            print(json.dumps(inspect_task(args.inspect, task_dir=task_dir), indent=2))
            return 0
        if args.propose:
            result = propose_fix(args.propose, task_dir=task_dir, target_file=args.target,
                                 replacement_content=args.replacement.read_text(encoding='utf-8'))
            print(json.dumps(result, indent=2))
            return 0 if result.get('status') == 'proposed' else 1
        if args.reproduce:
            result = reproduce_task(args.reproduce, task_dir=task_dir,
                                    timeout=args.timeout if args.timeout is not None else 30.0)
            print(json.dumps(result, indent=2))
            return 0 if result['reproduced'] else 1
        if args.apply:
            result = apply_proposal(args.apply, task_dir=task_dir, confirm=args.confirm)
            print(json.dumps(result, indent=2))
            if result.get('status') == 'approval_required':
                return 2
            return 0 if result.get('verified') else 1
        if args.rollback:
            result = rollback_proposal(args.rollback, task_dir=task_dir)
            print(json.dumps(result, indent=2))
            return 0 if result.get('status') == 'rolled_back' else 1
        command = list(args.command)
        if command[:1] == ['--']:
            command = command[1:]
        if not command:
            parser.error("provide a command after -- or choose a task action")
        return run_command(command, cwd=args.cwd, task_dir=task_dir,
                           timeout=args.timeout if args.timeout is not None else 300.0)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"JARVIS action failed: {redact(str(exc))}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
