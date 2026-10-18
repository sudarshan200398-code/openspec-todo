# Todo Task Management Specification

## Purpose

Provides durable task management through a simple web interface and REST API, so users can create, inspect, update, complete, and remove tasks reliably.

## Requirements

### Requirement: Persist and retrieve tasks
The system SHALL persist task records and expose task collection and individual-task retrieval through REST endpoints.

#### Scenario: List tasks
- **WHEN** a client requests the task collection
- **THEN** the system returns the persisted tasks with their task fields

#### Scenario: Retrieve a task
- **WHEN** a client requests an existing task by identifier
- **THEN** the system returns that task

#### Scenario: Retrieve a missing task
- **WHEN** a client requests a task identifier that does not exist
- **THEN** the system returns a not-found response

### Requirement: Create and update tasks
The system SHALL allow clients to create tasks and update their title, details, due date, and priority through REST endpoints.

#### Scenario: Create a task
- **WHEN** a client submits a valid new task
- **THEN** the system persists it and returns the created task with an identifier

#### Scenario: Reject invalid task input
- **WHEN** a client submits a task with invalid or missing required fields
- **THEN** the system returns a validation error and does not persist the invalid task

#### Scenario: Update an existing task
- **WHEN** a client submits valid changes for an existing task
- **THEN** the system persists and returns the updated task

### Requirement: Complete and delete tasks
The system SHALL allow clients to mark a task complete and permanently delete a task through REST endpoints.

#### Scenario: Complete a task
- **WHEN** a client marks an existing task complete
- **THEN** the task is persisted with its completed state and returned to the client

#### Scenario: Delete a task
- **WHEN** a client deletes an existing task
- **THEN** the task is removed from persistence and the system confirms deletion

### Requirement: Serve the task interface
The system SHALL serve a single-page task interface at the root URL that displays tasks and supports task-list refresh after changes.

#### Scenario: Open the application
- **WHEN** a user navigates to the root URL
- **THEN** the system serves the task interface with the current task list

#### Scenario: Reflect a task change
- **WHEN** a task is created, updated, completed, or deleted through the interface
- **THEN** the displayed task list reflects the persisted result
