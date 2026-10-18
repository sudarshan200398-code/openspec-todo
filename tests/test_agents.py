from datetime import date, timedelta

from agents.orchestrator import Orchestrator
from agents.planner_agent import PlannerAgent
from agents.summary_agent import SummaryAgent
from tools.repository import TaskRepository


class NoKeyInterpreter:
    api_key = None

    def interpret(self, message, tasks):
        raise AssertionError("No-key mode must not call the model")


def test_orchestrator_rule_fallback_creates_with_date_and_priority(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "agents.sqlite3")
    agent = Orchestrator(repository, interpreter=NoKeyInterpreter())

    result = agent.handle("add buy milk tomorrow, high priority")

    assert result["task_changed"] is True
    assert result["task"]["title"] == "buy milk"
    assert result["task"]["due_date"] == (date.today() + timedelta(days=1)).isoformat()
    assert result["task"]["priority"] == "high"


def test_orchestrator_task_mutations_use_repository(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "agents.sqlite3")
    agent = Orchestrator(repository, interpreter=NoKeyInterpreter())
    created = agent.handle("add write report")
    task_id = created["task"]["id"]

    renamed = agent.handle("update write report to prepare quarterly report")
    assert renamed["task"]["id"] == task_id
    assert renamed["task"]["title"] == "prepare quarterly report"

    completed = agent.handle("complete quarterly report")
    assert completed["task"]["id"] == task_id
    assert repository.get_task(task_id)["completed"] is True

    deleted = agent.handle("delete quarterly report")
    assert deleted["task_changed"] is True
    assert repository.get_task(task_id) is None


def test_ambiguous_or_unknown_request_does_not_mutate(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "agents.sqlite3")
    repository.create_task("Buy milk")
    repository.create_task("Buy milk tomorrow")
    result = Orchestrator(repository, interpreter=NoKeyInterpreter()).handle("complete buy milk")

    assert result["task_changed"] is False
    assert sum(task["completed"] for task in repository.list_tasks()) == 0


def test_planner_sorts_by_overdue_priority_due_date(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "agents.sqlite3")
    later_high = repository.create_task("High later", due_date=date.today() + timedelta(days=3), priority="high")
    overdue_low = repository.create_task("Overdue", due_date=date.today() - timedelta(days=1), priority="low")
    result = PlannerAgent(repository).suggest_next()
    assert result["task"]["id"] == overdue_low["id"]

    repository.complete_task(overdue_low["id"])
    result = PlannerAgent(repository).suggest_next()
    assert result["task"]["id"] == later_high["id"]


def test_planner_handles_no_outstanding_tasks_and_summary(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "agents.sqlite3")
    planner = PlannerAgent(repository)
    assert planner.suggest_next()["task"] is None

    task = repository.create_task("Prepare slides", due_date=date.today())
    summary = SummaryAgent(repository).daily_summary(date.today())
    assert summary["due_today"][0]["id"] == task["id"]
    assert summary["outstanding"] == 1
    repository.complete_task(task["id"])
    assert PlannerAgent(repository).suggest_next()["task"] is None
    assert SummaryAgent(repository).daily_summary(date.today())["completed"] == 1


def test_orchestrator_routes_planning_and_summary_requests(tmp_path) -> None:
    repository = TaskRepository(tmp_path / "agents.sqlite3")
    repository.create_task("Prepare slides")
    agent = Orchestrator(repository, interpreter=NoKeyInterpreter())
    assert "tackle" in agent.handle("what should I do next")["response"]
    assert "outstanding" in agent.handle("daily summary")["response"]
    assert "ordered" in agent.handle("prioritize my tasks")["response"]
