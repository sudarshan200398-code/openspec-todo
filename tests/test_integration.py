from datetime import date

from fastapi.testclient import TestClient

import main
from tools.repository import TaskRepository


def test_application_end_to_end_with_isolated_sqlite(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(main, "repository", TaskRepository(tmp_path / "e2e.sqlite3"))
    client = TestClient(main.app)

    assert client.get("/").status_code == 200
    created = client.post(
        "/api/tasks",
        json={"title": "Prepare demo", "due_date": date.today().isoformat(), "priority": "high"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert client.get(f"/api/tasks/{task_id}").json()["priority"] == "high"

    assistant = client.post("/api/assistant", json={"message": "add buy milk tomorrow, high priority"})
    assert assistant.status_code == 200
    assert assistant.json()["task"]["due_date"]
    assert client.post("/api/assistant/suggest", json={}).json()["task"]
    summary = client.post("/api/assistant/summary", json={}).json()
    assert summary["outstanding"] == 2

    assert client.post(f"/api/tasks/{task_id}/complete").json()["completed"] is True
    assert client.patch(f"/api/tasks/{task_id}", json={"title": "Prepare product demo"}).json()["title"] == "Prepare product demo"
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
