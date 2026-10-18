from pathlib import Path
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agents.orchestrator import Orchestrator
from tools.repository import TaskRepository


BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"

app = FastAPI(title="Agentic Todo", version="1.0.0")
repository = TaskRepository()


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    details: str | None = Field(default=None, max_length=5000)
    due_date: date | None = None
    priority: Literal["low", "medium", "high"] = "medium"

    @field_validator("title")
    @classmethod
    def title_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be blank")
        return value


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=300)
    details: str | None = Field(default=None, max_length=5000)
    due_date: date | None = None
    priority: Literal["low", "medium", "high"] | None = None
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def title_must_contain_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be blank")
        return value

    @model_validator(mode="after")
    def reject_null_non_nullable_fields(self) -> "TaskUpdate":
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("Title cannot be null")
        if "priority" in self.model_fields_set and self.priority is None:
            raise ValueError("Priority cannot be null")
        if "completed" in self.model_fields_set and self.completed is None:
            raise ValueError("Completed cannot be null")
        return self


class AssistantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def message_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank")
        return value


def _require_task(task_id: str) -> dict:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    """Serve the single-page task interface."""
    return HTMLResponse(INDEX_FILE.read_text(encoding="utf-8"))


@app.get("/api/tasks")
def list_tasks() -> list[dict]:
    return repository.list_tasks()


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskInput) -> dict:
    return repository.create_task(
        title=task.title,
        details=task.details,
        due_date=task.due_date,
        priority=task.priority,
    )


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    return _require_task(task_id)


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: str, changes: TaskUpdate) -> dict:
    _require_task(task_id)
    updated = repository.update_task(task_id, **changes.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: str) -> dict:
    completed = repository.complete_task(task_id)
    if completed is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return completed


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: str) -> None:
    if not repository.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/assistant")
def assistant_request(request: AssistantInput) -> dict:
    # Use the current repository instance so tests and deployments can inject
    # their own persistent store without agents opening the database directly.
    return Orchestrator(repository).handle(request.message)


@app.post("/api/assistant/suggest")
def suggest_next() -> dict:
    return Orchestrator(repository).planner_agent.suggest_next()


@app.post("/api/assistant/summary")
def daily_summary() -> dict:
    return Orchestrator(repository).summary_agent.daily_summary()
