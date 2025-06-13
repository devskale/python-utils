### **Robotni Lightweight Python Task Scheduler (Huey + FastAPI)**

**Package Name**: `robotni`

**Objective**: A minimal, file-based task scheduler to run Python jobs from a web app, with async task queuing and status polling.

---

### **Core Requirements**

#### 1. **Task Execution**

- **Trigger**: FastAPI endpoint accepts job requests (script path + `.venv` directory for Python virtual environment).
- **Queue**: `SqliteHuey` for task storage (file-based).
- **Isolation**: Each task runs in its own `.venv` via subprocess.

#### 2. **Web App Integration**

- **Endpoints**:
  - `POST /tasks`: Enqueue a task (returns `task_id`).
  - `GET /tasks/{task_id}`: Poll status (`queued`/`running`/`success`/`failed`).
- **Response**:
  ```json
  {
    "status": "running",
    "output": null, // Or combined stdout/stderr if completed
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

Let me know if you'd like to adjust concurrency/timeout defaults or add retry logic!
