# Agentic Task Assistance Specification

## Purpose

Lets users manage and plan tasks through natural-language assistance, with specialized agent behaviors and dependable operation whether or not an external language model is configured.

## Requirements

### Requirement: Orchestrate natural-language task requests
The system SHALL accept natural-language task requests and have an Orchestrator interpret intent and delegate relevant work to specialized agents.

#### Scenario: Delegate task mutation
- **WHEN** a user asks the assistant to create, update, complete, or delete a task in natural language
- **THEN** the Orchestrator delegates the requested operation to the Task Agent and returns the operation result

#### Scenario: Delegate planning request
- **WHEN** a user requests prioritization, due-date planning, or a next-task suggestion
- **THEN** the Orchestrator delegates the request to the Planner Agent and returns its recommendation

#### Scenario: Delegate daily summary
- **WHEN** a user requests a daily summary
- **THEN** the Orchestrator delegates summary generation to the Summary Agent and returns the summary

#### Scenario: Handle unrecognized request
- **WHEN** the assistant cannot determine the requested action
- **THEN** it asks the user for clarification without changing task data

### Requirement: Perform task lifecycle operations through the Task Agent
The Task Agent SHALL create, update, complete, and delete tasks in response to delegated requests, and agents SHALL access persisted task data only through the task repository boundary.

#### Scenario: Create from natural language
- **WHEN** a user requests a task such as “add buy milk tomorrow, high priority”
- **THEN** the Task Agent creates a task with the interpreted title, due date, and priority and reports the result

#### Scenario: Request missing task details
- **WHEN** a delegated mutation lacks information required to safely identify or perform the operation
- **THEN** the Task Agent requests clarification and leaves task data unchanged

### Requirement: Plan and summarize tasks
The Planner Agent SHALL support prioritization, due-date planning, and next-task suggestions, and the Summary Agent SHALL produce a daily summary from current task data.

#### Scenario: Suggest the next task
- **WHEN** a user requests the next task suggestion
- **THEN** the Planner Agent returns a recommendation based on task priority, due date, and completion state

#### Scenario: Summarize today's tasks
- **WHEN** a user requests a daily summary
- **THEN** the Summary Agent reports relevant task progress and outstanding work for the current day

#### Scenario: No eligible next task
- **WHEN** all tasks are complete or no tasks exist
- **THEN** the Planner Agent reports that there is no outstanding task to suggest

### Requirement: Operate with an LLM or rule-based fallback
The assistant SHALL use an OpenAI language model when `OPENAI_API_KEY` is configured and SHALL provide rule-based task assistance when the key is absent or the model is unavailable.

#### Scenario: Use configured language model
- **WHEN** the application has a valid `OPENAI_API_KEY` and the model service is available
- **THEN** the assistant uses the configured model to interpret or formulate the requested assistance

#### Scenario: Fall back without a key
- **WHEN** `OPENAI_API_KEY` is not configured
- **THEN** the assistant handles supported requests with rule-based behavior without requiring external model access

#### Scenario: Fall back when the model is unavailable
- **WHEN** the configured model cannot be reached or returns an unusable response
- **THEN** the assistant uses rule-based behavior for supported requests and does not lose or corrupt task data

### Requirement: Expose assistant actions in the interface
The task interface SHALL provide a natural-language assistant input and controls for next-task suggestions and daily summaries.

#### Scenario: Submit an assistant request
- **WHEN** a user submits text through the assistant input
- **THEN** the system displays the assistant response and reflects any resulting task changes in the task list

#### Scenario: Request next-task suggestion
- **WHEN** a user selects “Suggest next”
- **THEN** the system displays a Planner Agent recommendation

#### Scenario: Request daily summary
- **WHEN** a user selects “Daily summary”
- **THEN** the system displays a Summary Agent daily summary
