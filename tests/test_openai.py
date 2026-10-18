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
