### **Robotni Lightweight Python Task Scheduler (Huey + FastAPI)**

**Package Name**: `robotni`

**Objective**: A minimal, file-based task scheduler to run Python jobs from a web app, with async task queuing and status polling.

---

### **Tech Stack**

- **Python 3.8+**
- **FastAPI** (REST API framework)
- **Huey** (task queue, using SqliteHuey for file-based storage)
- **Subprocess** (job isolation and execution in separate virtual environments)
- **Uvicorn** (ASGI server for FastAPI)

---

### **Core Requirements**

#### 1. **Task Execution**

- **Trigger**: FastAPI endpoint accepts job requests (script path + `.venv` directory for Python virtual environment).
- **Queue**: `SqliteHuey` for task storage (file-based).
- **Isolation**: Each task runs in its own `.venv` via subprocess.

#### 2. **Web App Integration**

- **API Routes for Worker Management**:

  - `POST /api/worker/jobs`: Create and start a new job (returns `jobId`).
  - `GET /api/worker/jobs`: List all jobs (supports filtering by type, status, project).
  - `GET /api/worker/jobs/[jobId]`: Get specific job details and status.
  - `DELETE /api/worker/jobs/[jobId]`: Cancel/stop a specific job.

- **Worker System Routes**:

  - `GET /api/worker/status`: Get overall worker system status.
  - `GET /api/worker/types`: List all available worker types and capabilities.

- **Example Response for Job Status**:
  ```json
  {
    "jobId": "abc123",
    "status": "running",
    "output": null, // Or combined stdout/stderr if completed
    "type": "python-script",
    "project": "demo",
    "timestamp": "2024-02-20T12:00:00" // ISO 8601 format
  }
  ```

#### 3. **Worker Setup**

- **Concurrency**: 4 workers max (`huey_consumer.py -w 4`).
- **Idle**: Workers exit after 5 min inactivity (custom logic).
- **Timeouts**: Kill tasks exceeding 1 hr (`@huey.task(expires=3600)`).

#### 4. **Periodic Tasks**

- Example: Daily cleanup via `@huey.periodic_task(crontab(minute=0, hour=0))`.

---

### **Non-Functional Requirements**

- **Storage**: SQLite (no Redis).
- **Scale**: Single-machine (no distributed workers).
- **Latency**: Polling interval ≥5 sec (no real-time updates).

---

### **Out of Scope**

- Authentication, priority queues, or dynamic scaling.

---

### **Metrics**

- 95% of tasks complete within timeout.
- API response time <500 ms.

---

**Approval**: Ready for implementation. Stakeholders: Dev team.

---

Project Structure
./packages/robotni/
├── .pytest_cache/ # Pytest cache files (can be ignored)
├── robotni/ # Main package source
│ ├── tests/ # Unit and integration tests
│ ├── workers/ # Worker/task definitions
│ └── **pycache**/ # Python bytecode cache
└── robotni.egg-info/ # Packaging metadata

```

### **Implementation Path**

- [x] Set up project structure and dependencies
- [X] Implement FastAPI app skeleton
- [X] Define job/task data models
- [x] Integrate Huey with SqliteHuey backend
- [ ] Implement job submission endpoint (`POST /api/worker/jobs`)
- [ ] Implement job status and listing endpoints (`GET /api/worker/jobs`, `GET /api/worker/jobs/[jobId]`)
- [ ] Implement job cancellation endpoint (`DELETE /api/worker/jobs/[jobId]`)
- [ ] Implement worker system status/types endpoints
- [ ] Add subprocess-based job execution in isolated `.venv`
- [ ] Add periodic cleanup task
- [ ] Add tests and example jobs
- [ ] Documentation and usage examples

---

Let me know if you'd like to adjust concurrency/timeout defaults or add retry logic!
```
