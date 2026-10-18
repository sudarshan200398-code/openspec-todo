# Design

## Context

The repository has OpenSpec configuration but no application source, tests, or established implementation conventions. This is a greenfield, single-process web application. The behavior contract is defined in `specs/todo-task-management/spec.md` and `specs/agentic-task-assistance/spec.md`; motivation is in `proposal.md`.

## Goals / Non-Goals

**Goals:**
- Keep persistence and agent behavior behind small, testable boundaries.
- Preserve core assistant functionality when model configuration is absent or the model service fails.
- Keep the UI to one served HTML document while using REST endpoints for all application data operations.
- Support local startup and deployment environments that provide a `PORT` variable.

**Non-Goals:**
- Multi-user accounts, authentication, remote synchronization, or collaborative task sharing.
- A frontend framework, separate frontend build pipeline, or multi-page application.
- Autonomous background scheduling, notifications, or external calendar integration.
- Requiring an LLM key for tests, startup, or core task operations.

## Decisions

1. **Use FastAPI as the application and HTTP boundary.** `main.py` exports `app`, serves the one-page interface at `/`, and exposes JSON endpoints for task CRUD and assistant actions. This supports the requested ASGI launch contract with minimal infrastructure. Alternatives considered: a separate frontend/backend stack adds build and deployment complexity without a requirement for it; a lower-level ASGI implementation would duplicate request validation and routing support.

2. **Use SQLite through a single `TaskRepository` boundary.** `tools/repository.py` owns task persistence and queries; REST handlers and every agent call repository methods instead of executing SQL or opening the database directly. Store fields for a stable identifier, title, optional details and due date, priority, completion state, and timestamps. Initialize the database safely on application startup and make the database path configurable for tests and deployment. SQLite is selected for persistent, dependency-light local operation; an in-memory-only store would lose data across restarts, while a remote database is outside the requested scope.

3. **Separate orchestration from specialized agent behavior.** Modules under `agents/` implement the Orchestrator, Task Agent, Planner Agent, and Summary Agent. The Orchestrator classifies requests and delegates; it does not directly access the repository. The Task Agent owns lifecycle actions, the Planner Agent returns priority-aware suggestions, and the Summary Agent derives a daily view. This keeps permission to read or mutate task state constrained by the repository-mediated agent boundary and makes fallback behavior testable without network calls.

4. **Make model use optional and keep fallback deterministic.** An LLM adapter reads `OPENAI_API_KEY` from the environment and is used for natural-language interpretation and response formulation when configured. Rule-based parsing handles the supported request patterns when no key is configured or model interaction fails. The fallback should support common add/update/complete/delete intents, relative date phrases such as “tomorrow,” and priority words; unsupported or ambiguous requests should ask for clarification rather than mutate data. Alternatives considered: requiring a key would block local use and tests; attempting to implement unrestricted natural-language understanding in rules would create misleading expectations.

5. **Use explicit REST resource and assistant-action routes.** CRUD operations are exposed as ordinary JSON REST endpoints (collection and task-id routes, with completion represented in task state); assistant requests and the two UI actions use narrowly scoped endpoints. Request validation errors use client-error responses, missing task IDs use not-found responses, and unexpected model-service failures are absorbed by fallback behavior when possible. The concrete route names and response envelope should be consistent and documented by tests.

6. **Keep the browser client framework-free.** The single `index.html` includes task rendering, assistant input, and Suggest next / Daily summary buttons, and calls the JSON API with browser `fetch`. This satisfies the single-file UI constraint and avoids a dependency/build pipeline; richer client-side routing is not needed.

7. **Test behavior with pytest and isolated databases.** Tests use a temporary SQLite database and exercise repository persistence, CRUD status/error behavior, agent delegation, rule-based fallback, optional LLM selection, and key UI/API integration points. External model calls are mocked; the default test path must not depend on `OPENAI_API_KEY` or network access. Declare runtime and test dependencies in `requirements.txt`; exclude virtual environments, Python caches, pytest cache, and SQLite database files in `.gitignore`.

## Risks / Trade-offs

- [Rule-based parsing covers fewer phrasings than a language model] → Define the supported common intents, provide clarification for unsupported inputs, and test representative natural-language examples.
- [LLM output may be malformed or imply an unintended mutation] → Validate model results against typed task operations, require explicit task identification for destructive changes, and route all mutations through Task Agent and repository methods.
- [SQLite has limited suitability for concurrent multi-instance deployment] → Keep access transactional and the database path configurable; document that this initial deployment target is a single SQLite-backed instance.
- [Date-only phrases can be ambiguous across time zones and locale] → Use the server's local date as the initial interpretation of “today” and relative dates, with a consistent ISO date representation.
- [Serving HTML and API from one process couples presentation to the backend] → Keep the page static and data access exclusively API-based so the presentation can be replaced later without changing persistence or agent boundaries.

## Migration Plan

No existing application data or service is present, so no migration is required. On first startup, create the SQLite schema if absent. Launch with `uvicorn main:app --host 0.0.0.0 --port $PORT`; for local development, set `PORT` or use the conventional development port. Rollback consists of stopping the process and removing the newly created SQLite database if its data is not needed; no external infrastructure is changed.
