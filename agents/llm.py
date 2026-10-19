"""Optional OpenAI request interpreter with no-key-safe configuration."""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from typing import Any

logger = logging.getLogger("uvicorn.error")


class OpenAIInterpreter:
    """Interpret messages as a small validated action payload."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def interpret(self, message: str, tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not self.api_key:
            return None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, timeout=12.0, max_retries=2)
            response = client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Classify a todo request. Return JSON with keys action (create, update, complete, "
                            "delete, suggest, summary, prioritize, unknown), title, details, due_date (ISO date or null), "
                            "priority (low/medium/high), task_id (only if uniquely matched from supplied tasks), "
                            "and response. Never invent an id; ask for clarification in response when a destructive "
                            "target is ambiguous. Words such as urgent, asap, important or critical mean priority high; "
                            "no rush, whenever or someday mean priority low. Keep the title short, without the "
                            "date or priority words."
                        ),
                    },
                    {"role": "user", "content": json.dumps({"message": message, "tasks": tasks})},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                return None
            result = json.loads(content)
            if isinstance(result, dict) and result.get("priority") == "normal":
                result["priority"] = "medium"
            if not isinstance(result, dict) or result.get("action") not in {
                "create", "update", "complete", "delete", "suggest", "summary", "prioritize", "unknown"
            }:
                return None
            if result.get("priority") is not None and result["priority"] not in {"low", "medium", "high"}:
                return None
            if result.get("due_date"):
                try:
                    date.fromisoformat(result["due_date"])
                except (TypeError, ValueError):
                    return None
            if result.get("action") == "create" and not str(result.get("title") or "").strip():
                return None
            if result.get("action") in {"update", "complete", "delete"}:
                known_ids = {str(task.get("id")) for task in tasks}
                if result.get("task_id") not in known_ids:
                    return None
            return result
        except Exception as error:
            # Model, network, and malformed output failures use the deterministic fallback.
            logger.warning("LLM intent extraction failed, using fallback: %s: %s", type(error).__name__, error)
            return None
