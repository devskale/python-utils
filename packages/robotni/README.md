# Project: robotni - Minimal Task Scheduler

**Package Name**: `robotni`

## 1. Overview

**Objective**: A minimal, file-based task scheduler to run Python jobs from a web app, with async task queuing and status polling.

## 2. Features (Core Requirements)

### 2.1 Task Execution

- **Trigger**: FastAPI endpoint accepts job requests (e.g., script path, parameters, and optionally a `.venv` directory for Python virtual environment if implementing venv isolation).
- **Queue**: `SqliteHuey` for task storage (file-based).
- **Isolation**: Each task can be designed to run in its own specified `.venv` via the `subprocess` module to ensure dependency isolation.

### 2.2 Web App Integration & API Routes

- **API Routes for Worker Management**:

  - `POST /api/worker/jobs`: Create and start a new job (returns `jobId`).
  - `GET /api/worker/jobs`: List all jobs (supports filtering by type, status, project).
  - `GET /api/worker/jobs/{jobId}`: Get specific job details and status.
  - `DELETE /api/worker/jobs/{jobId}`: Cancel/stop a specific job.

- **Worker System Routes**:

  - `GET /api/worker/status`: Get overall worker system status.
  - `GET /api/worker/types`: List all available worker types and capabilities (initially, this might be a single "python-script" type).

### 2.3 Example Tasks

- **taskHelloworld.py**: A simple task that prints "Hello, World!".
- **taskFakejob.py**: A task that simulates a job with a delay and prints "Fake job completed".

## 3. Implementation Path

- [ ] Set up project structure and dependencies (`pyproject.toml`, basic directories).
- [ ] Implement FastAPI app skeleton with basic API documentation (Swagger/ReDoc).
- [ ] Define job/task data models (Pydantic models for requests/responses).
- [ ] Integrate Huey with `SqliteHuey` backend.
- [ ] Implement job submission endpoint (`POST /api/worker/jobs`) to enqueue tasks.
- [ ] Develop the core task execution logic using `subprocess` (initially for a generic Python script).
- [ ] Implement job status polling endpoint (`GET /api/worker/jobs/{jobId}`).
- [ ] Create example jobs (`taskHelloworld.py` and `taskFakejob.py`) and document usage.
- [ ] Write unit and integration tests for API endpoints and task execution (basic tests for core functionality).

## 4. Project Structure

```
./robotni/
├── robotni/                  # Main package sources
├── tests/                    # Unit and integration tests
├── examples/                 # Example scripts to be run as jobs
├── .venv/                    # Example virtual environment for a job (if used)
├── pyproject.toml
└── README.md                 # This document
```

## 5. License

This project is licensed under the terms of the MIT license. See the [LICENSE](LICENSE) file for details.