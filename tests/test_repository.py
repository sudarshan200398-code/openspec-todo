from tools.repository import TaskRepository


def test_repository_persists_task_lifecycle(tmp_path) -> None:
    database = tmp_path / "tasks.sqlite3"
    repository = TaskRepository(database)
    task = repository.create_task(
        "Buy milk", details="Oat milk", due_date="2026-10-20", priority="high"
    )

    reopened = TaskRepository(database)
    assert reopened.get_task(task["id"])["title"] == "Buy milk"
    assert reopened.update_task(task["id"], title="Buy almond milk")["title"] == "Buy almond milk"
    assert reopened.complete_task(task["id"])["completed"] is True
    assert reopened.delete_task(task["id"]) is True
    assert reopened.get_task(task["id"]) is None


def test_repository_lists_only_incomplete_tasks_when_requested(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "tasks.sqlite3")
    first = repository.create_task("Open task")
    completed = repository.create_task("Done task")
    repository.complete_task(completed["id"])

    assert [task["id"] for task in repository.list_tasks(include_completed=False)] == [first["id"]]
