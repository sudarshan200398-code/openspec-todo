"""Task lifecycle operations delegated by the Orchestrator."""

from __future__ import annotations

from datetime import date
from typing import Any

from tools.repository import TaskRepository


class TaskAgent:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action == "create":
            title = str(payload.get("title") or "").strip()
            if not title:
                return {"response": "What task would you like me to add?", "task_changed": False}
            due = payload.get("due_date")
            if due and not isinstance(due, date):
                due = date.fromisoformat(str(due))
            task = self.repository.create_task(
                title=title,
                details=payload.get("details"),
                due_date=due,
                priority=payload.get("priority", "medium"),
            )
            return {"response": f"Added ‘{task['title']}’.", "task_changed": True, "task": task}

        task_id = payload.get("task_id")
        if action in {"update", "complete", "delete"} and not task_id:
            return {"response": "Which task should I change? Please include its title.", "task_changed": False}
        existing = self.repository.get_task(str(task_id)) if task_id else None
        if action in {"update", "complete", "delete"} and existing is None:
            return {"response": "I couldn’t find that task. Nothing was changed.", "task_changed": False}

        if action == "update":
            changes = {
                key: value
                for key, value in payload.items()
                if key in {"title", "details", "due_date", "priority"} and value is not None
            }
            if not changes:
                return {"response": "What would you like to update?", "task_changed": False}
            if "due_date" in changes and changes["due_date"]:
                changes["due_date"] = date.fromisoformat(str(changes["due_date"]))
            task = self.repository.update_task(str(task_id), **changes)
            return {"response": f"Updated ‘{task['title']}’.", "task_changed": True, "task": task}
        if action == "complete":
            task = self.repository.complete_task(str(task_id))
            return {"response": f"Marked ‘{task['title']}’ complete.", "task_changed": True, "task": task}
        if action == "delete":
            self.repository.delete_task(str(task_id))
            return {"response": f"Deleted ‘{existing['title']}’.", "task_changed": True}
        return {"response": "I’m not sure how to change that task. Could you rephrase?", "task_changed": False}
