"""
Tests for Phase 6 Extra Apps APIs:
- Tools API (/api/tools)
- Automations / Scheduler API (/api/automations)
- Memory API (/api/memory)
- AI Studio Prompt Test (/api/chat/prompt_test)
"""
import pytest
from fastapi.testclient import TestClient
from apps.core.main import app

client = TestClient(app)


def test_tools_api_list_and_execute():
    # 1. List tools
    res = client.get("/api/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["total"] > 0
    assert any(t["name"] == "get_system_status" for t in data["tools"])

    # 2. Filter by category
    res_cat = client.get("/api/tools?category=A")
    assert res_cat.status_code == 200
    assert all(t["category"] == "A" for t in res_cat.json()["tools"])

    # 3. Execute a read-only tool
    res_exec = client.post("/api/tools/execute", json={
        "tool_name": "get_system_status",
        "arguments": {},
        "confirmed": True
    })
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["success"] is True


def test_automations_api_crud():
    # 1. Create a task
    res_create = client.post("/api/automations/tasks", json={
        "name": "unit_test_task",
        "schedule": "every 300s",
        "command": "system_diagnostics",
        "description": "Test automation task"
    })
    assert res_create.status_code == 200
    task_id = res_create.json()["task_id"]

    # 2. List tasks
    res_list = client.get("/api/automations/tasks")
    assert res_list.status_code == 200
    tasks = res_list.json()["tasks"]
    assert any(t["name"] == "unit_test_task" for t in tasks)

    # 3. Toggle task
    res_toggle = client.post(f"/api/automations/tasks/{task_id}/toggle?enable=false")
    assert res_toggle.status_code == 200
    assert res_toggle.json()["enabled"] is False

    # 4. Delete task
    res_del = client.delete(f"/api/automations/tasks/{task_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True


def test_memory_api_extensions():
    # 1. Categories
    res_cat = client.get("/api/memory/categories")
    assert res_cat.status_code == 200
    assert "USER" in res_cat.json()["categories"]

    # 2. Store memory
    res_store = client.post("/api/memory/store", json={
        "category": "USER",
        "content": "Operator prefers concise status reports.",
        "importance": 9
    })
    assert res_store.status_code == 200
    mem_id = res_store.json()["id"]

    # 3. Search memory
    res_search = client.get("/api/memory/search?query=concise")
    assert res_search.status_code == 200
    assert any(m["id"] == mem_id for m in res_search.json()["data"])

    # 4. Delete memory
    res_del = client.delete(f"/api/memory/{mem_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True


def test_ai_studio_prompt_test():
    res = client.post("/api/chat/prompt_test", json={
        "system_prompt": "You are a test assistant.",
        "user_message": "Respond with 'TEST_PONG'",
        "provider": "ollama",
        "model": "llama3.2:1b"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "response" in data
    assert "latency_ms" in data
