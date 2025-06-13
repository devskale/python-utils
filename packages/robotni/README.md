# Project: RobotNI - Product Requirements Document

**Package Name**: `robotni`

## 1. Overview

**Objective**: A minimal, file-based task scheduler to run Python jobs from a web app, with async task queuing and status polling.

RobotNI is a Python package designed to provide a lightweight, file-based task scheduling system. It enables the execution of Python jobs, managed via a FastAPI web application, with tasks queued and processed asynchronously using Huey. The system is intended for scenarios where a simple, single-machine task execution and monitoring solution is required, without the overhead of more complex distributed task queues.

## 2. Table of Contents

1. [Overview](#1-overview)
2. [Table of Contents](#2-table-of-contents)
3. [Technical Stack](#3-technical-stack)
4. [Features (Core Requirements)](#4-features-core-requirements)
   - [4.1 Task Execution](#41-task-execution)
   - [4.2 Web App Integration & API Routes](#42-web-app-integration--api-routes)
   - [4.3 Worker Setup](#43-worker-setup)
   - [4.4 Periodic Tasks](#44-periodic-tasks)
   - [4.5 Extensibility and Modularity](#45-extensibility-and-modularity)
   - [4.6 Future Features (Post-Initial Version)](#46-future-features-post-initial-version)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Out of Scope (for initial version)](#6-out-of-scope-for-initial-version)
7. [Success Metrics & Implementation Path](#7-success-metrics--implementation-path)
   - [7.1 Key Performance Indicators](#71-key-performance-indicators)
   - [7.2 Implementation Path](#72-implementation-path)
   - [7.3 Long-Term Success](#73-long-term-success)
8. [Project Structure](#8-project-structure)
9. [License](#9-license)
10. [Approval](#10-approval)

## 3. Technical Stack

- **Python 3.8+**
- **FastAPI** (REST API framework)
- **Huey** (task queue, using `SqliteHuey` for file-based storage)
- **Subprocess** (for job isolation and execution, potentially in separate virtual environments)
- **Uvicorn** (ASGI server for FastAPI)

## 4. Features (Core Requirements)

### 4.1 Task Execution

- **Trigger**: FastAPI endpoint accepts job requests (e.g., script path, parameters, and optionally a `.venv` directory for Python virtual environment if implementing venv isolation).
- **Queue**: `SqliteHuey` for task storage (file-based).
- **Isolation**: Each task can be designed to run in its own specified `.venv` via the `subprocess` module to ensure dependency isolation.

### 4.2 Web App Integration & API Routes

- **API Routes for Worker Management**:
  - `POST /api/worker/jobs`: Create and start a new job (returns `jobId`).
  - `GET /api/worker/jobs`: List all jobs (supports filtering by type, status, project).
  - `GET /api/worker/jobs/{jobId}`: Get specific job details and status.
  - `DELETE /api/worker/jobs/{jobId}`: Cancel/stop a specific job.

- **Worker System Routes**:
  - `GET /api/worker/status`: Get overall worker system status.
  - `GET /api/worker/types`: List all available worker types and capabilities (initially, this might be a single "python-script" type).

- **Example Response for Job Status**:
  ```json
  {
    "jobId": "abc123",
    "status": "running", // e.g., pending, running, completed, failed, cancelled
    "output": null, // Or combined stdout/stderr if completed/failed
    "type": "python-script", // Example type
    "project": "demo", // Example project context
    "timestamp": "2024-02-20T12:00:00Z" // ISO 8601 format
  }
  ```

### 4.3 Worker Setup

- **Concurrency**: Configurable number of workers (e.g., default 4 workers via `huey_consumer.py -w 4`).
- **Idle Behavior**: Workers could be configured to exit after a certain period of inactivity (e.g., 5 minutes), though this might require custom logic around the Huey consumer.
- **Timeouts**: Tasks should have configurable timeouts to prevent them from running indefinitely (e.g., kill tasks exceeding 1 hour using `@huey.task(expires=3600)`).

### 4.4 Periodic Tasks

- Support for periodic tasks, e.g., daily cleanup, using Huey's periodic task capabilities (`@huey.periodic_task(crontab(minute=0, hour=0))`).

### 4.5 Extensibility and Modularity

The package is designed with extensibility in mind. Future versions will include:

-   Support for multiple, configurable jobs.
-   Integration with actual robotic hardware.
-   Advanced logging and monitoring features.
-   A more sophisticated user interface for job management.

### 4.6 Future Features (Post-Initial Version)

Post-initial version development may include:

-   A web-based dashboard for monitoring and controlling jobs.
-   Integration with popular RPA tools and frameworks.
-   Enhanced error handling and recovery mechanisms.
-   Support for job scheduling and automation.

## 5. Non-Functional Requirements

- **Storage**: Primarily SQLite for Huey's task queue (no external Redis dependency for the core functionality).
- **Scale**: Designed for single-machine deployment (not aiming for distributed workers in the initial version).
- **Latency**: API polling interval for job status updates is acceptable at ≥5 seconds (no hard real-time updates required for status checking via API).

## 6. Out of Scope (for initial version)

- User authentication and authorization for API endpoints.
- Complex job dependency chains or workflows.
- Priority queues for tasks.
- Dynamic scaling of workers based on load.
- Graphical User Interface (GUI) beyond API interactions.

## 7. Success Metrics & Implementation Path

### 7.1 Key Performance Indicators
- **Task Completion Rate**: 95% of tasks complete successfully or are terminated within their defined timeout.
- **API Responsiveness**: Average API response time for status and listing endpoints <500 ms under typical load.
- Successful execution of various Python scripts as jobs.
- Accurate and timely logging of job status messages and errors.

### 7.2 Implementation Path

- [ ] Set up project structure and dependencies (`pyproject.toml`, basic directories).
- [ ] Implement FastAPI app skeleton with basic API documentation (Swagger/ReDoc).
- [ ] Define job/task data models (Pydantic models for requests/responses).
- [ ] Integrate Huey with `SqliteHuey` backend.
- [ ] Implement job submission endpoint (`POST /api/worker/jobs`) to enqueue tasks.
- [ ] Develop the core task execution logic using `subprocess` (initially for a generic Python script).
- [ ] Implement job status polling endpoint (`GET /api/worker/jobs/{jobId}`).
- [ ] Implement job listing endpoint (`GET /api/worker/jobs`).
- [ ] Implement job cancellation mechanism (`DELETE /api/worker/jobs/{jobId}`).
- [ ] Implement worker system status (`GET /api/worker/status`) and types (`GET /api/worker/types`) endpoints.
- [ ] Add basic periodic task example (e.g., cleanup).
- [ ] Write unit and integration tests for API endpoints and task execution.
- [ ] Create example jobs and document usage.
- [ ] Refine error handling and logging throughout the application.

### 7.3 Long-Term Success

Long-term success will be evaluated based on:

-   The robustness and reliability of the package in real-world RPA scenarios.
-   The flexibility and ease of configuring and extending the package for new tasks and robotic hardware.
-   The quality and clarity of documentation and user support resources.
-   The growth of a user community and ecosystem around the RobotNI package.

## 8. Project Structure

(Illustrative - to be refined during development)
```
./robotni/
├── robotni/                  # Main package source
│   ├── api/                  # FastAPI application, endpoints
│   ├── tasks/                # Huey task definitions
│   ├── workers/              # Core worker logic, subprocess execution
│   ├── models/               # Pydantic models
│   ├── core/                 # Core configuration, Huey setup
│   └── main.py               # FastAPI application entry point
├── tests/                    # Unit and integration tests
│   ├── integration/
│   └── unit/
├── examples/                 # Example scripts to be run as jobs
├── .venv/                    # Example virtual environment for a job (if used)
├── pyproject.toml
└── README.md                 # This document
```

## 9. License

This project is licensed under the terms of the MIT license. See the [LICENSE](LICENSE) file for details.

## 10. Approval

Ready for implementation. Stakeholders: Dev team.