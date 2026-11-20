"""Unit tests for Hybrid JARVIS Developer API and Orchestrator endpoints."""
import pytest
from fastapi.testclient import TestClient
from apps.core.app_factory import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_orchestrator.sqlite3"
    monkeypatch.setattr("apps.api.hybrid_developer_api.DB_PATH", test_db)
    monkeypatch.setattr("apps.api.hybrid_developer_api._orchestrator", None)
    app = create_app()
    return TestClient(app)


def test_developer_status_endpoint(client):
    res = client.get("/api/developer/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "git" in data
    assert "branch" in data["git"]
    assert "worktrees" in data
    assert "providers" in data
    assert "agents" in data
    assert data["agents"]["registered_count"] >= 5


def test_developer_agents_endpoint(client):
    res = client.get("/api/developer/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    agent_ids = [a["agent_id"] for a in data["agents"]]
    assert "antigravity" in agent_ids
    assert "codex" in agent_ids
    assert "claude" in agent_ids
    assert "ollama" in agent_ids
    assert "openrouter" in agent_ids
    assert "cline" in agent_ids
    assert "copilot" in agent_ids
    assert "simulated" in agent_ids


def test_developer_task_lifecycle(client):
    # 1. Create a valid task
    create_res = client.post(
        "/api/developer/tasks",
        json={
            "prompt": "Verify system security hardening",
            "capabilities": ["code"],
            "dependencies": [],
            "timeout": 15.0,
        },
    )
    assert create_res.status_code == 200
    task_data = create_res.json()
    task_id = task_data["task_id"]
    assert task_data["state"] == "pending"

    # 2. List tasks
    list_res = client.get("/api/developer/tasks")
    assert list_res.status_code == 200
    tasks = list_res.json()["tasks"]
    assert any(t["task_id"] == task_id for t in tasks)

    # 3. Run the task
    run_res = client.post(f"/api/developer/tasks/{task_id}/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["state"] == "succeeded"
    assert run_data["result"] is not None

    # 4. Create another task and cancel it
    c_res = client.post(
        "/api/developer/tasks",
        json={"prompt": "Task to be cancelled", "capabilities": ["test"]},
    )
    c_id = c_res.json()["task_id"]
    cancel_res = client.post(f"/api/developer/tasks/{c_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["cancelled"] is True


def test_developer_invalid_task_rejected(client):
    res = client.post("/api/developer/tasks", json={"prompt": "   "})
    assert res.status_code in {400, 422}


def test_developer_worktrees_endpoint(client):
    res = client.get("/api/developer/worktrees")
    assert res.status_code == 200
    data = res.json()
    assert "worktrees" in data
    assert "conflicts" in data


def test_developer_tests_endpoint(client):
    res = client.get("/api/developer/tests")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert len(data["suites"]) >= 5
    assert data["gate_status"] == "READY_FOR_HUMAN_REVIEW"


def test_developer_isolated_worktree_lifecycle_and_propose(client, tmp_path, monkeypatch):
    """Verify that isolated worktree execution checkpoints diffs and moves to awaiting_human_review."""
    import subprocess
    from pathlib import Path
    from apps.api.hybrid_developer_api import WorktreeManager

    # Mock git repository for isolated test
    test_repo = tmp_path / "mock_repo"
    test_repo.mkdir()
    subprocess.run(["git", "init", "-q", str(test_repo)], check=True)
    subprocess.run(["git", "-C", str(test_repo), "-c", "user.name=Test", "-c", "user.email=t@local", "commit", "--allow-empty", "-qm", "init"], check=True)

    test_wt_root = tmp_path / "mock_worktrees"
    test_wt_root.mkdir()

    mock_wt_mgr = WorktreeManager(repository=test_repo, worktree_root=test_wt_root)
    monkeypatch.setattr("apps.api.hybrid_developer_api._worktree_mgr", mock_wt_mgr)

    # 1. Create task with isolated worktree
    create_res = client.post(
        "/api/developer/tasks",
        json={
            "prompt": "Synthesize security test cases in worktree",
            "capabilities": ["code"],
            "agent_id": "simulated",
            "isolated_worktree": True,
        },
    )
    assert create_res.status_code == 200
    task_info = create_res.json()
    task_id = task_info["task_id"]
    worktree_path = task_info["worktree"]
    assert worktree_path is not None
    assert Path(worktree_path).exists()

    # 2. Run the task
    run_res = client.post(f"/api/developer/tasks/{task_id}/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["state"] == "succeeded"
    assert run_data["checkpoint"] is not None
    assert "SIMULATED_" in run_data["checkpoint"]

    # 3. Propose for review gate
    propose_res = client.post(f"/api/developer/tasks/{task_id}/propose", json={"gate_type": "tests"})
    assert propose_res.status_code == 200
    p_data = propose_res.json()
    assert p_data["status"] == "ok"
    assert p_data["proposal"]["status"] == "awaiting_human_review"
    assert p_data["proposal"]["branch"] == task_info["branch"]

    # Main repository remains clean (never auto-merged)
    main_status = subprocess.run(["git", "-C", str(test_repo), "status", "--porcelain"], capture_output=True, text=True).stdout
    assert main_status == ""

    # 4. Safely cleanup worktree
    del_res = client.delete(f"/api/developer/tasks/{task_id}/worktree")
    assert del_res.status_code == 200
    assert not Path(worktree_path).exists()


def test_codex_cli_adapter_contract():
    """Verify CodexCliAdapter properties and command specification."""
    from apps.api.hybrid_developer_api import CodexCliAdapter, Task

    adapter = CodexCliAdapter(executable="/home/roshan/.local/bin/codex")
    assert adapter.is_available() is True
    assert adapter.integration_type == "real_cli"
    assert "ChatGPT Plus" in adapter.detail
