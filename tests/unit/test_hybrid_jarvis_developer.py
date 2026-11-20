import importlib.util

from pathlib import Path
import pytest

ROOT = Path(__file__).parents[2] / "tools" / "hybrid-jarvis-developer"
spec = importlib.util.spec_from_file_location("hybrid", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
hybrid = importlib.util.module_from_spec(spec)
import sys
sys.modules["hybrid"] = hybrid
spec.loader.exec_module(hybrid)
from hybrid.models import Agent, Capability, Task, TaskState
from hybrid.simulated import SimulatedAgent
from hybrid.worktrees import WorktreeManager
import subprocess
import threading
import time

def setup(tmp_path, adapter=None):
    orch = hybrid.Orchestrator(tmp_path / "orchestration.db")
    orch.register(Agent("mock", (Capability("code", "mock coding"),), adapter or SimulatedAgent()))
    return orch

def test_task_execution_registration_and_restart(tmp_path):
    orch = setup(tmp_path)
    task = orch.create_task(Task("hello", ("code",)))
    assert orch.run(task.task_id).state is TaskState.SUCCEEDED
    assert hybrid.Orchestrator(tmp_path / "orchestration.db").get_task(task.task_id).result == "simulated result"

def test_failures_and_retry_limit(tmp_path):
    orch = setup(tmp_path, SimulatedAgent(fail_times=3))
    task = orch.create_task(Task("hello", ("code",), max_retries=1))
    result = orch.run(task.task_id)
    assert result.state is TaskState.FAILED and result.attempts == 2

def test_dependencies_and_invalid_tasks(tmp_path):
    orch = setup(tmp_path)
    first = orch.create_task(Task("first", ("code",)))
    second = orch.create_task(Task("second", ("code",), dependencies=(first.task_id,)))
    with pytest.raises(RuntimeError): orch.run(second.task_id)
    orch.run(first.task_id)
    assert orch.run(second.task_id).state is TaskState.SUCCEEDED
    with pytest.raises(ValueError): orch.create_task(Task(" "))

def test_agent_registration_and_cancel(tmp_path):
    orch = setup(tmp_path)
    with pytest.raises(ValueError): orch.register(Agent("mock", (), SimulatedAgent()))
    task = orch.create_task(Task("cancel me"))
    assert orch.cancel(task.task_id)
    assert orch.get_task(task.task_id).state is TaskState.CANCELLED

def test_worktree_isolation_and_review_gate(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@local", "commit", "--allow-empty", "-qm", "base"], check=True)
    orch = setup(tmp_path / "db")
    task = orch.create_task(Task("isolated"))
    manager = WorktreeManager(repo, tmp_path / "trees")
    path = manager.prepare(task)
    (path / "change.txt").write_text("mock change")
    assert "?? change.txt" in manager.checkpoint(task)
    task.state = TaskState.SUCCEEDED
    assert manager.propose(task, lambda _: False)["status"] == "blocked"
    assert manager.propose(task, lambda _: True)["status"] == "awaiting_human_review"
    assert subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout == ""

def test_conflict_detection_and_three_parallel_mock_jobs(tmp_path):
    manager = WorktreeManager.__new__(WorktreeManager)
    assert manager.detect_conflicts({"a": ["ai/a.py"], "b": ["ai/b.py"], "c": ["docs/c.md"]}) == set()
    assert manager.detect_conflicts({"a": ["ai/api.py"], "b": ["ai/api.py"]}) == {"a", "b"}
    active = 0; maximum = 0; lock = threading.Lock()
    class ConcurrentMock:
        def execute(self, task):
            nonlocal active, maximum
            with lock: active += 1; maximum = max(maximum, active)
            time.sleep(.05)
            with lock: active -= 1
            return "done"
    orch = hybrid.Orchestrator(tmp_path / "parallel.db", max_concurrency=3)
    orch.register(Agent("parallel", (Capability("code", "mock"),), ConcurrentMock()))
    tasks = [orch.create_task(Task(str(i), ("code",))) for i in range(3)]
    with __import__("concurrent.futures").futures.ThreadPoolExecutor(3) as pool:
        list(pool.map(lambda task: orch.run(task.task_id), tasks))
    assert maximum == 3

def test_unavailable_agent_and_recovery(tmp_path):
    path = tmp_path / "recover.db"
    orch = hybrid.Orchestrator(path)
    task = orch.create_task(Task("recover"))
    try: orch.run(task.task_id)
    except RuntimeError: pass
    recovered = hybrid.Orchestrator(path).get_task(task.task_id)
    assert recovered.state is TaskState.PENDING
    orch.register(Agent("available", (), SimulatedAgent()))
    assert orch.run(task.task_id).state is TaskState.SUCCEEDED


def test_unexpected_exit_and_invalid_output_fail_safely(tmp_path):
    class ExitingAgent:
        def execute(self, task):
            raise RuntimeError("agent exited unexpectedly")

    class InvalidAgent:
        def execute(self, task):
            return {"unexpected": "shape"}

    orch = hybrid.Orchestrator(tmp_path / "failures.db")
    orch.register(Agent("exit", (Capability("code", "exit"),), ExitingAgent()))
    exited = orch.create_task(Task("exit", ("code",)))
    assert orch.run(exited.task_id).state is TaskState.FAILED
    assert "unexpectedly" in orch.get_task(exited.task_id).error

    invalid_orch = hybrid.Orchestrator(tmp_path / "invalid.db")
    invalid_orch.register(Agent("invalid", (Capability("code", "invalid"),), InvalidAgent()))
    invalid = invalid_orch.create_task(Task("invalid", ("code",)))
    result = invalid_orch.run(invalid.task_id)
    assert result.state is TaskState.FAILED
    assert "invalid or empty output" in result.error


def test_timeout_returns_without_waiting_for_worker(tmp_path):
    class SlowAgent:
        def execute(self, task):
            time.sleep(0.25)
            return "late"

    orch = hybrid.Orchestrator(tmp_path / "timeout.db")
    orch.register(Agent("slow", (Capability("code", "slow"),), SlowAgent()))
    task = orch.create_task(Task("timeout", ("code",), timeout=0.01))

    started = time.monotonic()
    result = orch.run(task.task_id)
    elapsed = time.monotonic() - started

    assert result.state is TaskState.FAILED
    assert "timeout" in result.error
    assert elapsed < 0.15


def test_cancellation_wins_over_in_flight_execution(tmp_path):
    started = threading.Event()
    release = threading.Event()

    class CancellableAgent:
        def __init__(self):
            self.cancelled = False

        def execute(self, task):
            started.set()
            release.wait(1)
            return "completed"

        def cancel(self):
            self.cancelled = True
            release.set()

    adapter = CancellableAgent()
    orch = hybrid.Orchestrator(tmp_path / "cancel.db")
    orch.register(Agent("cancel", (Capability("code", "cancel"),), adapter))
    task = orch.create_task(Task("cancel", ("code",), timeout=1))
    runner = threading.Thread(target=lambda: orch.run(task.task_id))
    runner.start()
    assert started.wait(1)
    assert orch.cancel(task.task_id) is True
    runner.join(1)

    assert adapter.cancelled is True
    assert orch.get_task(task.task_id).state is TaskState.CANCELLED


def test_authentication_and_workspace_failures_are_not_success(tmp_path):
    class AuthFailure:
        def execute(self, task):
            return {"status": "error", "message": "authentication failed"}

    class WorkspaceFailure:
        def execute(self, task):
            raise PermissionError("workspace unavailable")

    auth_orch = hybrid.Orchestrator(tmp_path / "auth.db")
    auth_orch.register(Agent("auth", (Capability("code", "auth"),), AuthFailure()))
    auth_task = auth_orch.create_task(Task("auth", ("code",)))
    assert auth_orch.run(auth_task.task_id).state is TaskState.FAILED

    workspace_orch = hybrid.Orchestrator(tmp_path / "workspace.db")
    workspace_orch.register(Agent("workspace", (Capability("code", "workspace"),), WorkspaceFailure()))
    workspace_task = workspace_orch.create_task(Task("workspace", ("code",)))
    result = workspace_orch.run(workspace_task.task_id)
    assert result.state is TaskState.FAILED
    assert "workspace unavailable" in result.error


def test_unauthorized_paths_and_conflicting_tasks_are_rejected(tmp_path):
    orch = setup(tmp_path / "conflicts")
    with pytest.raises(ValueError, match="safe relative"):
        orch.create_task(Task("unsafe", ("code",), owned_paths=("../secret.py",)))

    first = orch.create_task(Task("first", ("code",), owned_paths=("src/app.py",)))
    with pytest.raises(ValueError, match="conflict"):
        orch.create_task(Task("second", ("code",), owned_paths=("src",)))
    assert orch.get_task(first.task_id).state is TaskState.PENDING


def test_duplicate_execution_is_prevented(tmp_path):
    adapter = SimulatedAgent()
    orch = hybrid.Orchestrator(tmp_path / "duplicate.db")
    orch.register(Agent("once", (Capability("code", "once"),), adapter))
    task = orch.create_task(Task("once", ("code",)))

    assert orch.run(task.task_id).state is TaskState.SUCCEEDED
    assert orch.run(task.task_id).state is TaskState.SUCCEEDED
    assert adapter.calls == 1


def test_no_changes_and_failed_gate_are_blocked_without_stable_mutation(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@local",
         "commit", "--allow-empty", "-qm", "base"],
        check=True,
    )
    manager = WorktreeManager(repo, tmp_path / "trees")
    orch = setup(tmp_path / "orchestrator")

    no_change = orch.create_task(Task("no change"))
    no_change_path = manager.prepare(no_change)
    no_change.state = TaskState.SUCCEEDED
    assert manager.propose(no_change, lambda _: True)["reason"] == "no code changes"

    failed_gate = orch.create_task(Task("failed gate"))
    failed_path = manager.prepare(failed_gate)
    (failed_path / "broken.py").write_text("this is not valid python\n")
    failed_gate.state = TaskState.SUCCEEDED
    assert manager.propose(failed_gate, lambda _: False)["status"] == "blocked"
    assert subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout == ""


def test_checkpoint_survives_orchestrator_restart(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@local",
         "commit", "--allow-empty", "-qm", "base"],
        check=True,
    )
    manager = WorktreeManager(repo, tmp_path / "trees")
    db = tmp_path / "checkpoint.db"
    orch = hybrid.Orchestrator(db)
    orch.register(Agent("mock", (Capability("code", "mock coding"),), SimulatedAgent()))
    task = orch.create_task(Task("checkpoint"))
    path = manager.prepare(task)
    (path / "change.txt").write_text("checkpoint")
    manager.checkpoint(task)
    with __import__("sqlite3").connect(orch.database) as connection:
        orch._save(connection, task, "checkpoint")

    resumed = hybrid.Orchestrator(db).get_task(task.task_id)
    assert resumed is not None
    assert resumed.worktree == str(path)
    assert "?? change.txt" in resumed.checkpoint


def test_interrupted_execution_is_recorded_as_failure(tmp_path):
    class InterruptedAgent:
        def execute(self, task):
            raise KeyboardInterrupt()

    orch = hybrid.Orchestrator(tmp_path / "interrupt.db")
    orch.register(Agent("interrupt", (Capability("code", "interrupt"),), InterruptedAgent()))
    task = orch.create_task(Task("interrupt", ("code",)))
    result = orch.run(task.task_id)
    assert result.state is TaskState.FAILED
    assert "interrupted" in result.error
