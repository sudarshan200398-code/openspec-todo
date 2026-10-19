"""Natural-language router that delegates to specialized agents."""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from agents.llm import OpenAIInterpreter
from agents.planner_agent import PlannerAgent
from agents.summary_agent import SummaryAgent
from agents.task_agent import TaskAgent
from tools.repository import TaskRepository


class Orchestrator:
    def __init__(
        self,
        repository: TaskRepository,
        interpreter: OpenAIInterpreter | None = None,
    ) -> None:
        self.repository = repository
        self.interpreter = interpreter or OpenAIInterpreter()
        self.task_agent = TaskAgent(repository)
        self.planner_agent = PlannerAgent(repository)
        self.summary_agent = SummaryAgent(repository)

    @staticmethod
    def _fallback(message: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        text = message.strip()
        normalized = text.casefold()
        if any(word in normalized for word in ("daily summary", "summary", "what did i", "how am i doing")):
            return {"action": "summary"}
        if any(word in normalized for word in ("suggest next", "what should i do", "next task", "what's next", "what is next")):
            return {"action": "suggest"}
        if re.search(r"\bprioritize\b|\bprioritise\b|\bplan my\b", normalized):
            return {"action": "prioritize"}

        action = None
        if re.match(r"^(add|create|new|remind me to|remember to)\b", normalized):
            action = "create"
        elif re.match(r"^(complete|finish|mark done|done with)\b", normalized):
            action = "complete"
        elif re.match(r"^(delete|remove)\b", normalized):
            action = "delete"
        elif re.match(r"^(update|rename|change)\b", normalized):
            action = "update"
        if action is None:
            return {"action": "unknown", "no_command": True}

        match_text = re.sub(r"^(add|create|new|remind me to|remember to|complete|finish|mark done|done with|delete|remove|update|rename|change)\s*", "", text, flags=re.I).strip()
        due_date = None
        today = date.today()
        for phrase, value in (("tomorrow", today + timedelta(days=1)), ("today", today), ("next week", today + timedelta(days=7))):
            if re.search(rf"\b{re.escape(phrase)}\b", match_text, flags=re.I):
                due_date = value.isoformat()
                match_text = re.sub(rf"\b{re.escape(phrase)}\b", "", match_text, flags=re.I)
                break
        if due_date is None:
            absolute = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", match_text)
            if absolute:
                try:
                    due_date = date.fromisoformat(absolute.group(1)).isoformat()
                except ValueError:
                    return {"action": "unknown"}
                match_text = match_text.replace(absolute.group(1), "")

        priority = None
        for level in ("high", "low", "medium"):
            if re.search(rf"\b{level}\s+priority\b|\bpriority\s+{level}\b", match_text, flags=re.I):
                priority = level
                match_text = re.sub(rf"\b{level}\s+priority\b|\bpriority\s+{level}\b", "", match_text, flags=re.I)
                break
        match_text = re.sub(r"\b(by|on|for)\s*$", "", match_text.strip(" ,.-"), flags=re.I).strip()

        payload: dict[str, Any] = {"action": action}
        if action == "create":
            payload.update({"title": match_text, "due_date": due_date, "priority": priority or "medium"})
            return payload

        new_title = None
        existing_title = match_text
        if action == "update" and re.search(r"\s+to\s+", match_text, flags=re.I):
            existing_title, new_title = re.split(r"\s+to\s+", match_text, maxsplit=1, flags=re.I)
            existing_title = existing_title.strip()
            new_title = new_title.strip()
        candidates = [task for task in tasks if existing_title.casefold() and existing_title.casefold() in task["title"].casefold()]
        if len(candidates) != 1:
            return {"action": "unknown"}
        payload["task_id"] = candidates[0]["id"]
        if action == "update":
            if new_title:
                payload["title"] = new_title
            if due_date is not None:
                payload["due_date"] = due_date
            if priority is not None:
                payload["priority"] = priority
            return payload
        return payload

    def handle(self, message: str) -> dict[str, Any]:
        if not message.strip():
            return {"response": "Tell me what you’d like help with.", "task_changed": False}
        tasks = self.repository.list_tasks()
        intent = self.interpreter.interpret(message, tasks) if self.interpreter.api_key else None
        if not intent:
            intent = self._fallback(message, tasks)

        action = intent.get("action", "unknown")
        if action in {"create", "update", "complete", "delete"}:
            payload = {key: value for key, value in intent.items() if key != "action"}
            try:
                return self.task_agent.execute(action, payload)
            except (ValueError, TypeError):
                fallback = self._fallback(message, tasks)
                if fallback.get("action") != action or fallback == intent:
                    return {"response": "I couldn’t safely interpret that request. Could you rephrase it?", "task_changed": False, "needs_clarification": True, "can_add_as_task": False}
                payload = {key: value for key, value in fallback.items() if key != "action"}
                return self.task_agent.execute(action, payload)
        if action == "suggest":
            return self.planner_agent.suggest_next()
        if action == "prioritize":
            return self.planner_agent.prioritize()
        if action == "summary":
            return self.summary_agent.daily_summary()
        if intent.get("no_command"):
            return {
                "response": "I didn’t recognise a command. Start with add, complete, update or delete, ask for a summary or the next task, or add your text as a new task.",
                "task_changed": False,
                "needs_clarification": True,
                "can_add_as_task": True,
            }
        return {
            "response": intent.get("response") or "I’m not sure what you’d like me to do. Could you rephrase?",
            "task_changed": False,
            "needs_clarification": True,
            "can_add_as_task": False,
        }
