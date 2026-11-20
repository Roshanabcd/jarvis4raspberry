# Terminal assistance

Run an explicitly chosen command from the project root:

```bash
scripts/jarvis-run --timeout 60 -- venv/bin/python -m pytest tests/unit/test_terminal_failure_assistance.py -q
```

Output streams to your terminal immediately. At most 16 KiB per stream is retained
for diagnostic evidence. Terminal output is unchanged; persisted text is redacted
for common credential patterns, which cannot guarantee removal of every secret.

Successful commands create no task. Failures create private JSON records under
`.jarvis/diagnostics` in the working directory, including exit status and timeout/
truncation flags. No repair is applied and no output is sent to a cloud provider.
The initial command deadline defaults to 300 seconds; `--timeout` accepts a positive
finite value up to 300. Timeout returns 124 and Ctrl+C returns 130. The process group,
including background descendants, is cleaned up; use your normal shell for services.

Inspect an emitted task path:

```bash
scripts/jarvis-run --inspect /path/to/diagnostic.json
```

After reviewing the command and its effects, explicitly reproduce it:

```bash
scripts/jarvis-run --reproduce /path/to/diagnostic.json
```

Reproduction has a separate 30-second default deadline and no interactive input.
Redacted arguments cannot faithfully reproduce a command and are rejected. Supply
a fresh command explicitly instead. Task files are input, not authorization.

The wrapper uses pipes, not a terminal emulator. TTY-dependent/full-screen apps
and terminal job control are not supported. Nested wrappers avoid duplicate tasks.

On 17 November 2026, 23 terminal and Developer Hub tests passed in 5.10 seconds.
Coverage includes large-output capture, timeouts, nested execution, reproduction,
and reviewed repair/rollback. Syntax, CLI help, and whitespace checks passed.
Tests used disposable local commands. The CLI uses current source immediately;
no system service was restarted for this increment.

## Review, apply, verify, and recover

Prepare a UTF-8 file containing the proposed replacement source, then generate a
diff without changing the source file:

```bash
scripts/jarvis-run --propose /path/to/diagnostic.json --target relative/source.py --replacement /path/to/proposed-source.txt
```

The target is resolved relative to the task's recorded workspace. Read the diff
and the recorded command before applying: verification reruns that command and
can have its normal side effects. This is an operator-supplied repair workflow,
not automatic AI patch generation.

```bash
scripts/jarvis-run --apply /path/to/diagnostic.json --confirm
scripts/jarvis-run --rollback /path/to/diagnostic.json
```

Source and replacement digests are recorded with the proposal. Apply refuses
source changes since proposal creation, changed replacement content, an existing
backup, or a target resolving outside the recorded workspace. Legacy proposals
without digests require a fresh proposal. Rollback refuses missing/changed backups
or source edits made after applying the repair. It returns a failure exit status
instead of pretending restoration succeeded. Checkpoints are retained on conflict.

Rollback metadata is saved before verification starts. If verification is
interrupted, the applied change remains marked unverified and can be rolled back.
Diagnostic metadata and patch files are replaced atomically with private file
permissions. These checks do not authenticate editable task files or provide a
transaction against other processes modifying source files at the same time.

`--task-dir` selects the task-record directory when using a task ID instead of a
full path. `--timeout` also sets the reproduction deadline. Conflicting action
flags and invalid timeouts are rejected before execution; missing files produce
a concise error and nonzero exit code.

The subsequent 17 November verification passed **173 selected Python tests and
27 frontend tests**. An actual shell-wrapper acceptance run in a disposable
workspace verified failure capture → proposal → denied unconfirmed apply →
confirmed apply with successful verification → rollback restoring original bytes.
