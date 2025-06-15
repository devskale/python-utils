# Project: robotni - Minimal Task Scheduler

**Package Name**: `robotni_huey`

## 1. Overview

robotni is a minimal task scheduler that allows you to queue, manage, and monitor background jobs through a simple API. It is designed for running and tracking asynchronous or long-running tasks in a lightweight and efficient way.

## 2. Description

robotni provides an interface for submitting jobs that may take a long time to complete, such as data processing, file operations, or external command execution. It exposes endpoints to enqueue tasks, check their status, retrieve results, and manage the task queue. The system is suitable for both IO-bound and CPU-bound jobs, and can handle multiple jobs concurrently.

### Functions

- **Enqueue Tasks:** Submit jobs to be executed in the background, including custom or heavy jobs.
- **Check Status:** Query the status and result of submitted tasks using a unique task ID.
- **Manage Queue:** List pending, scheduled, and revoked tasks; revoke (cancel) tasks that have not started.
- **Flush Queue:** Clear all pending and scheduled tasks from the queue.
- **Web Demo:** Serve a web-based demo interface.

robotni is designed to be simple to use, with a clear API for integrating background job processing into your applications. It is suitable for scenarios where you need to offload work from the main application flow and track progress or results asynchronously.

## 3. Tech Stack

- Python
- [Huey](https://github.com/coleifer/huey) (task queue and job management)
- FastAPI (web API framework)

## 4. Installation

To install `robotni_huey`, navigate to the `robotni_huey` directory and install it using pip:

```bash
cd packages/robotni/robotni_huey
pip install -e .
```

This will install the package and its dependencies, including `huey` and `fastapi`.

## 5. Usage

### 5.1 Running the API and Huey Consumer

To run the FastAPI application and the Huey consumer, you need two separate terminal sessions. **Important:** Both the Uvicorn server and the Huey consumer must be started from the `robotni_huey` directory to ensure correct module imports and path resolution.

**Terminal 1: Run FastAPI with Uvicorn**

Navigate to the `robotni_huey` directory and start the Uvicorn server:

```bash
cd packages/robotni/robotni_huey
uvicorn main:app --reload
```

This will start the API server, typically accessible at `http://127.0.0.1:8000`.

**Terminal 2: Run Huey Consumer**

In a separate terminal, navigate to the `robotni_huey` directory and start the Huey consumer:

```bash
cd packages/robotni/robotni_huey
huey_consumer huey_app.huey
```

This consumer will process tasks enqueued by the FastAPI application.

### 5.2 Accessing the Web Demo

Once the FastAPI application is running, you can access the web demo by navigating your browser to:

`http://127.0.0.1:8000/webdemo`

This interface allows you to interact with the task queue, enqueue tasks, and view their status.

### 5.3 Example Usage (API Endpoints)

- **Enqueue an 'add' task:**
  `POST /add/` with JSON body: `{"x": 5, "y": 3}`

- **Enqueue a 'fakejob' task:**
  `POST /fakejob/`

- **Check task result:**
  `GET /result/{task_id}`

- **View queue status:**
  `GET /queue/`

- **Revoke a task:**
  `DELETE /queue/{task_id}`

- **Flush all tasks:**
  `POST /queue/flush/`

---

python Workers are in ./workers/

Docs
retrieve latest docs via context7 mcp server.
