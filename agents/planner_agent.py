"""Priority- and due-date-aware task planning."""

from __future__ import annotations

from datetime import date

from tools.repository import TaskRepository


class PlannerAgent:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def suggest_next(self) -> dict[str, object]:
        tasks = self.repository.list_tasks(include_completed=False)
        if not tasks:
            return {"response": "You’re all caught up—there are no outstanding tasks.", "task": None}
        today = date.today().isoformat()
        tasks.sort(
            key=lambda task: (
                0 if task["due_date"] and task["due_date"] < today else 1,
                self.PRIORITY_ORDER.get(task["priority"], 1),
                task["due_date"] or "9999-12-31",
                task["created_at"],
            )
        )
        task = tasks[0]
        return {"response": f"I’d tackle ‘{task['title']}’ next ({task['priority']} priority).", "task": task}

    def prioritize(self) -> dict[str, object]:
        tasks = self.repository.list_tasks(include_completed=False)
        ordered = sorted(
            tasks,
            key=lambda task: (
                0 if task["due_date"] and task["due_date"] < date.today().isoformat() else 1,
                self.PRIORITY_ORDER.get(task["priority"], 1),
                task["due_date"] or "9999-12-31",
            ),
        )
        return {"tasks": ordered, "response": "Tasks are ordered by overdue date, priority, and due date."}
