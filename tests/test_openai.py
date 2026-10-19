from agents.llm import OpenAIInterpreter


def test_interpreter_does_not_require_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert OpenAIInterpreter().interpret("add a task", []) is None


def test_interpreter_uses_openai_when_key_is_configured(monkeypatch) -> None:
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)

            class Message:
                content = '{"action":"create","title":"Buy milk","priority":"high"}'

            class Choice:
                message = Message()

            class Response:
                choices = [Choice()]

            return Response()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("openai.OpenAI", FakeClient)
    result = OpenAIInterpreter().interpret("add buy milk, high priority", [])

    assert result["title"] == "Buy milk"
    assert calls[0]["model"] == "gpt-4o-mini"


def test_interpreter_falls_back_on_openai_error(monkeypatch) -> None:
    class FailingClient:
        def __init__(self, **kwargs):
            raise RuntimeError("unavailable")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("openai.OpenAI", FailingClient)
    assert OpenAIInterpreter().interpret("add buy milk", []) is None


def test_interpreter_rejects_invented_task_ids(monkeypatch) -> None:
    class FakeCompletions:
        def create(self, **kwargs):
            class Message:
                content = '{"action":"delete","task_id":"not-a-real-id"}'

            class Choice:
                message = Message()

            class Response:
                choices = [Choice()]

            return Response()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("openai.OpenAI", FakeClient)
    assert OpenAIInterpreter().interpret("delete the report", [{"id": "known-task"}]) is None


def _fake_llm(monkeypatch, content: str) -> None:
    class FakeCompletions:
        def create(self, **kwargs):
            message = type("Message", (), {"content": content})()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("openai.OpenAI", FakeClient)


def test_urgent_wording_sets_high_priority_when_llm_omits_it(tmp_path, monkeypatch) -> None:
    from agents.orchestrator import Orchestrator
    from tools.repository import TaskRepository

    _fake_llm(monkeypatch, '{"action":"create","title":"call mom","due_date":"2026-10-24","priority":null}')
    repository = TaskRepository(tmp_path / "llm.sqlite3")
    result = Orchestrator(repository).handle("remind me to call mom before the weekend, it's urgent")
    assert result["task"]["title"] == "call mom"
    assert result["task"]["priority"] == "high"


def test_llm_normal_priority_is_accepted_as_medium(monkeypatch) -> None:
    _fake_llm(monkeypatch, '{"action":"create","title":"Read","priority":"normal"}')
    assert OpenAIInterpreter().interpret("add read", [])["priority"] == "medium"


def test_rule_fallback_detects_bare_urgent(tmp_path, monkeypatch) -> None:
    from agents.orchestrator import Orchestrator
    from tools.repository import TaskRepository

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    repository = TaskRepository(tmp_path / "rules.sqlite3")
    result = Orchestrator(repository).handle("remind me to call mom before the weekend, it's urgent")
    assert result["task"]["priority"] == "high"
    assert result["task"]["title"] == "call mom before the weekend"
