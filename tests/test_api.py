from fastapi.testclient import TestClient

import main
from tools.repository import TaskRepository


def client_for(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(main, "repository", TaskRepository(tmp_path / "api.sqlite3"))
    return TestClient(main.app)


def test_task_crud_and_not_found(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    created = client.post(
        "/api/tasks",
        json={"title": "Buy milk", "due_date": "2026-10-20", "priority": "high"},
    )
    assert created.status_code == 201
    task = created.json()
    task_id = task["id"]
    assert task["due_date"] == "2026-10-20"
    assert client.get(f"/api/tasks/{task_id}").json()["title"] == "Buy milk"
    assert client.get("/api/tasks").json()[0]["id"] == task_id

    updated = client.patch(f"/api/tasks/{task_id}", json={"title": "Buy oat milk"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "Buy oat milk"
    completed = client.post(f"/api/tasks/{task_id}/complete")
    assert completed.json()["completed"] is True
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


def test_task_validation_and_missing_delete(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422
    assert client.post("/api/tasks", json={"title": "   "}).status_code == 422
    assert client.post("/api/tasks", json={"title": "Nope", "priority": "urgent"}).status_code == 422
    assert client.patch("/api/tasks/missing", json={"title": "Change"}).status_code == 404
    task = client.post("/api/tasks", json={"title": "Keep title"}).json()
    assert client.patch(f"/api/tasks/{task['id']}", json={"title": None}).status_code == 422
    assert client.delete("/api/tasks/missing").status_code == 404


def test_assistant_actions_and_task_mutation(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    added = client.post("/api/assistant", json={"message": "add call the dentist high priority"})
    assert added.status_code == 200
    assert added.json()["task_changed"] is True
    assert added.json()["task"]["priority"] == "high"
    assert client.post("/api/assistant/suggest", json={}).json()["task"]
    assert client.post("/api/assistant/summary", json={}).json()["outstanding"] == 1


def test_assistant_rejects_empty_message(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    assert client.post("/api/assistant", json={"message": " "}).status_code == 422
