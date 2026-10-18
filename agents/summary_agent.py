"""Daily task progress summaries."""

from datetime import date

from tools.repository import TaskRepository


class SummaryAgent:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def daily_summary(self, today: date | None = None) -> dict[str, object]:
        current_day = (today or date.today()).isoformat()
        tasks = self.repository.list_tasks()
        completed = [task for task in tasks if task["completed"]]
        outstanding = [task for task in tasks if not task["completed"]]
        due_today = [task for task in outstanding if task["due_date"] == current_day]
        overdue = [task for task in outstanding if task["due_date"] and task["due_date"] < current_day]
        message = (
            f"Today: {len(completed)} of {len(tasks)} tasks complete; "
            f"{len(outstanding)} still outstanding, {len(due_today)} due today, and {len(overdue)} overdue."
        )
        return {
            "response": message,
            "total": len(tasks),
            "completed": len(completed),
            "outstanding": len(outstanding),
            "due_today": due_today,
            "overdue": overdue,
        }
