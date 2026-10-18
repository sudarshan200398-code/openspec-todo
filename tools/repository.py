"""SQLite-backed task repository used by API handlers and agents."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "tasks.sqlite3"


class TaskNotFoundError(LookupError):
    """Raised when a requested task does not exist."""


class TaskRepository:
    """Own all task storage access through SQLite."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or os.getenv("TODO_DATABASE", DEFAULT_DB_PATH))
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.db_path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    details TEXT,
                    due_date TEXT,
                    priority TEXT NOT NULL DEFAULT 'medium'
                        CHECK (priority IN ('low', 'medium', 'high')),
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    @staticmethod
    def _serialize(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        task = dict(row)
        task["completed"] = bool(task["completed"])
        return task

    def list_tasks(self, *, include_completed: bool = True) -> list[dict[str, Any]]:
        query = "SELECT * FROM tasks"
        if not include_completed:
            query += " WHERE completed = 0"
        query += " ORDER BY completed ASC, due_date IS NULL ASC, due_date ASC, created_at ASC"
        with self._connection() as connection:
            rows = connection.execute(query).fetchall()
        return [self._serialize(row) for row in rows if row is not None]

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._serialize(row)

    def create_task(
        self,
        title: str,
        details: str | None = None,
        due_date: date | str | None = None,
        priority: str = "medium",
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        task_id = str(uuid4())
        due_value = due_date.isoformat() if isinstance(due_date, date) else due_date
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO tasks (id, title, details, due_date, priority, completed, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
                (task_id, title.strip(), details, due_value, priority, now, now),
            )
        return self.get_task(task_id)  # type: ignore[return-value]

    def update_task(self, task_id: str, **changes: Any) -> dict[str, Any] | None:
        allowed = {"title", "details", "due_date", "priority", "completed"}
        updates = {key: value for key, value in changes.items() if key in allowed}
        if "due_date" in updates and isinstance(updates["due_date"], date):
            updates["due_date"] = updates["due_date"].isoformat()
        if "completed" in updates:
            updates["completed"] = int(bool(updates["completed"]))
        if "title" in updates and updates["title"] is not None:
            updates["title"] = updates["title"].strip()
        if not updates:
            return self.get_task(task_id)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        assignments = ", ".join(f"{column} = ?" for column in updates)
        with self._connection() as connection:
            cursor = connection.execute(
                f"UPDATE tasks SET {assignments} WHERE id = ?",
                (*updates.values(), task_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_task(task_id)

    def complete_task(self, task_id: str) -> dict[str, Any] | None:
        return self.update_task(task_id, completed=True)

    def delete_task(self, task_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0