# Tasks

## 1. Application foundation

- [x] 1.1 Create the FastAPI entry point, application lifecycle, single-page `/` route, and initial project layout; verify the app imports as `main:app` and the root returns HTML using a smoke test.
- [x] 1.2 Add runtime and pytest dependencies to `requirements.txt` and the requested virtual-environment/cache/SQLite patterns to `.gitignore`; verify dependency installation succeeds and ignore rules match the specified paths.
- [x] 1.3 Add configurable SQLite initialization and `TaskRepository` in `tools/repository.py` with task create/read/update/complete/delete operations; add pytest coverage using a temporary database and verify persistence across repository instances.

## 2. REST task management and interface

- [x] 2.1 Implement JSON REST endpoints for listing, retrieving, creating, updating, completing, and deleting tasks through the repository; add API tests for successful operations, validation errors, missing identifiers, and persisted results.
- [x] 2.2 Build the single `index.html` task-list interface with create/edit/complete/delete interactions using the REST API; verify rendered task fields and list refresh behavior with an application-level test or browser test.

## 3. Agentic task assistance

- [x] 3.1 Implement the Task Agent and Orchestrator in `agents/`, with clear delegation for natural-language task mutations and clarification on unsupported or ambiguous requests; add tests for create/update/complete/delete delegation and confirm all data access uses `TaskRepository`.
- [x] 3.2 Implement the Planner Agent and Summary Agent for priority/due-date-aware next-task suggestions and daily summaries; add tests for recommendation ordering, completed/empty task lists, and daily summary content.
- [x] 3.3 Add an OpenAI adapter configured by `OPENAI_API_KEY` plus deterministic rule-based fallback for absent keys and model errors; add tests with mocked model calls proving common requests work without network access and fallback does not corrupt data.
- [x] 3.4 Add assistant request, Suggest next, and Daily summary API actions and connect them to the assistant box and buttons in `index.html`; add integration tests that exercise each UI action through its API response and verify task-list updates after mutations.

## 4. Runtime and end-to-end verification

- [x] 4.1 Add an integration test covering app startup, SQLite persistence, REST CRUD, agent-mediated task creation, and summary/suggestion actions using an isolated database; verify the complete pytest suite passes without `OPENAI_API_KEY`.
- [x] 4.2 Verify the documented deployment invocation `uvicorn main:app --host 0.0.0.0 --port $PORT` starts the app on the supplied port and serves the page and API; record any platform-specific invocation notes in the project documentation if required for reliable use.
