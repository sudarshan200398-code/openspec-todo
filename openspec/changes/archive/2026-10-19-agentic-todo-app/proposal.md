# Proposal

## Why

A lightweight to-do app should make ordinary task tracking fast while allowing users to express task changes naturally instead of translating every request into form fields. A local SQLite-backed service with a clear agent boundary provides durable task operations, useful planning and summaries, and a reliable experience even when an LLM key is unavailable.

## What Changes

- Introduce a FastAPI application with a `main.py` app object, a single HTML page served at `/`, and plain REST endpoints for task CRUD.
- Persist tasks in SQLite and require all agent data access to go through `TaskRepository` in `tools/repository.py`.
- Add an Orchestrator agent that interprets natural-language requests and delegates task mutations, prioritization/planning, and daily summaries to agents in an `agents/` folder.
- Support OpenAI through `OPENAI_API_KEY` with a rule-based fallback when the key is absent, so core assistant behavior remains available without external LLM configuration.
- Provide a task list and assistant input in the UI, with “Suggest next” and “Daily summary” actions.
- Add pytest coverage, dependency requirements, ignore rules, and a deployment-compatible Uvicorn start command using `$PORT`.

## Capabilities

### New Capabilities
- `todo-task-management`: Persistent task lifecycle, REST CRUD API, and task-list interface.
- `agentic-task-assistance`: Natural-language orchestration, specialized task/planner/summary agents, LLM and fallback behavior, and assistant UI actions.

### Modified Capabilities
- None.

## Impact

- New FastAPI application and static HTML UI; SQLite persistence via a repository abstraction.
- New agent modules and supporting tools, with OpenAI integration configured through an environment variable and deterministic local fallback.
- New pytest tests, `requirements.txt`, and `.gitignore`; runtime entry point `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- No existing app implementation or tests were present in the repository at planning time.
