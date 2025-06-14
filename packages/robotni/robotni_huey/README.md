# Project: robotni - Minimal Task Scheduler

**Package Name**: `robotni`

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

---

python Workers are in ./workers/

Docs
retrieve latest docs via context7 mcp server.
