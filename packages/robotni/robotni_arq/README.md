# Project: robotni - Minimal Task Scheduler

**Package Name**: `robotni_arq`

## Overview

robotni is a minimal task scheduler that allows you to queue, manage, and monitor background jobs through a simple API. It is designed for running and tracking asynchronous or long-running tasks in a lightweight and efficient way.

## Description

robotni provides an interface for submitting jobs that may take a long time to complete, such as data processing, file operations, or external command execution. It exposes endpoints to enqueue tasks, check their status, retrieve results, and manage the task queue. The system is suitable for both IO-bound and CPU-bound jobs, and can handle multiple jobs concurrently.

### Functions

- **Enqueue Tasks:** Submit jobs to be executed in the background, including custom or heavy jobs.
- **Check Status:** Query the status and result of submitted tasks using a unique task ID.
- **Manage Queue:** List pending, scheduled, and revoked tasks; revoke (cancel) tasks that have not started.
- **Flush Queue:** Clear all pending and scheduled tasks from the queue.
- **Web Demo:** Serve a web-based demo interface.

robotni is designed to be simple to use, with a clear API for integrating background job processing into your applications. It is suitable for scenarios where you need to offload work from the main application flow and track progress or results asynchronously.

## Tech Stack

- Python
- [arq](https://github.com/python-arq/arq) (task queue and job management)
- FastAPI (web API framework)

---

Python Workers are located in the `./workers/` directory and are responsible for executing the background tasks.

## Installation

1. **Clone the repository** (if you haven't already) and navigate to the `robotni_arq` directory:

   ```bash
   git clone https://github.com/yourusername/robotni.git
   cd robotni/packages/robotni/robotni_arq
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install the package in editable mode**:

   ```bash
   pip install -e .
   ```

   This command will install all necessary dependencies specified in `pyproject.toml` and link your local project files, allowing for direct execution and development.

## Usage

### Running the Application

The `robotni_arq.sh` script is provided to easily manage the FastAPI server and the Arq worker.

#### 1. Start the Redis Server

Ensure your Redis server is running. If using Docker, you can start it with:

```bash
docker run --name some-redis -p 6379:6379 -d redis
```

Or on macOS with the `container` command:
```bash
container run --detach my-redis
container start my-redis
```

#### 2. Manage the Services with `robotni_arq.sh`

The script provides `start`, `stop`, `restart`, and `status` commands to manage the application.

*   **To start the FastAPI server and Arq worker:**

    ```bash
    ./robotni_arq.sh start
    ```
    This will start both services in the background.

*   **To check the status of the services:**

    ```bash
    ./robotni_arq.sh status
    ```
    This will show whether the FastAPI server and Arq worker are running and list their PIDs.

*   **To stop the services:**

    ```bash
    ./robotni_arq.sh stop
    ```
    This command will find and terminate the running `uvicorn` and `arq` processes.

*   **To restart the services:**

    ```bash
    ./robotni_arq.sh restart
    ```
    This is a convenient way to stop and then immediately start the services again.

The server will be accessible at `http://127.0.0.1:8000`.

## API Endpoints

The application exposes the following API endpoints:

- **`GET /`**
  - **Description:** Serves the main HTML page for the web interface.
  - **Response:** HTML content.

- **`POST /api/worker/jobs`**
  - **Description:** Enqueues a new background task.
  - **Request Body (JSON):**
    ```json
    {
      "type": "string (task function name, e.g., fake_task)",
      "name": "string (user-defined name for the job)",
      "project": "string (optional, project identifier)",
      "parameters": {
        "param": "string (task-specific parameter, e.g., '5 \"My Custom Task\"' for fake_task, or 'some message' for another_fake_task)",
        "key1": "value1", // Other task-specific parameters
        "key2": "value2"
      }
    ```
  - **Note on `parameters`:** For `fake_task` and `another_fake_task`, a single `param` field can be used to pass arguments. For `fake_task`, the `param` string should be in the format `"<duration> \"<task_name>\""` (e.g., `"5 \"My Custom Task\""`). For `another_fake_task`, the `param` field can be any string message. If `param` is present, other keys in `parameters` might be ignored by these specific tasks for backward compatibility.
    }
    ```
  - **Response (JSON - Success):**
    ```json
    {
      "success": true,
      "data": {
        "id": "string (job_id)",
        "type": "string (task function name)",
        "name": "string (user-defined name)",
        "status": "string (e.g., pending)",
        "project": "string (optional)",
        "createdAt": "datetime (ISO 8601)",
        "progress": "integer (0-100)",
        "parameters": {}
      }
    }
    ```
  - **Response (JSON - Error):**
    ```json
    {
      "success": false,
      "error": "string (error message)",
      "details": "string (optional, error details)"
    }
    ```
  - **Example `curl`:**
     ```bash
     curl -X POST "http://127.0.0.1:8000/api/worker/jobs" \
          -H "Content-Type: application/json" \
          -d '{
            "type": "task_parse",
            "name": "My Parsing Job",
            "project": "Project Beta",
            "parameters": {
              "input_file": "/path/to/data.csv",
              "output_format": "json"
            }
          }'
     ```
   - **Example `curl` for `fake_task`:**
     ```bash
     curl -X POST "http://127.0.0.1:8000/api/worker/jobs" \
          -H "Content-Type: application/json" \
          -d '{
            "type": "fake_task",
            "name": "My Fake Task",
            "parameters": {
              "duration": 10,
              "task_name": "Custom Fake Task"
            }
          }'
     ```

- **`GET /api/worker/jobs`**
  - **Description:** Lists all jobs (queued, active, completed, failed).
  - **Response (JSON - Success):**
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "string (job_id)",
          "type": "string (task function name)",
          "name": "string (user-defined name)",
          "status": "string (e.g., complete, failed, in_progress, queued)",
          "project": "string (optional)",
          "createdAt": "datetime (ISO 8601, enqueue time)",
          "progress": "integer (0-100)",
          "parameters": {},
          "startedAt": "datetime (optional, ISO 8601)",
          "completedAt": "datetime (optional, ISO 8601)",
          "duration": "integer (optional, in seconds)",
          "result": "any (task result or error details for failed jobs)"
        }
        // ... more jobs
      ]
    }
    ```
  - **Response (JSON - Error):**
    ```json
    {
      "success": false,
      "error": "string (error message)",
      "details": "string (optional, error details)"
    }
    ```

- **`GET /api/worker/jobs/{job_id}`
  - **Description:** Retrieves the status and information for a specific job.
  - **Path Parameter:**
    - `job_id` (string, required): The ID of the job to query.
  - **Example `curl`:**
    ```bash
    curl http://127.0.0.1:8000/api/worker/jobs/job_1678886400000_abcde
    ```
  - **Response (JSON):**
    ```json
    {
      "job_id": "string",
      "status": "string (current job status)",
      "info": { // Arq JobDef object, structure may vary
        "function": "string",
        "args": [],
        "kwargs": {},
        "enqueue_time": "datetime",
        // ... other JobDef fields
      }
    }
```

- **`GET /api/worker/list/`
  - **Description:** Lists all available task names dynamically discovered from `tasks.py` and `subprocess_config.yaml`.
  - **Example `curl`:**
    ```bash
    curl http://127.0.0.1:8000/api/worker/list/
    ```
  - **Response (JSON):
    ```json
    {
      "tasks": [
        {"id": "string (task_name)"},
        {"id": "string (another_task_name)"}
        // ... more tasks
      ]
    }
    ```


- **`POST /api/worker/jobs/flush`
  - **Description:** Flushes (deletes) all queued, active, and completed/failed jobs and their associated data from Redis.
  - **Example `curl`:**
    ```bash
    curl -X POST http://127.0.0.1:8000/api/worker/jobs/flush
    ```
  - **Response (JSON - Success):
    ```json
    {
      "success": true,
      "message": "string (confirmation message)",
      "deleted_keys_count": "integer (number of keys deleted)"
    }
    ```
  - **Response (JSON - Error):
    ```json
    {
      "success": false,
      "error": "string (error message)",
      "details": "string (optional, error details)"
    }
```

## Project Structure

````

## Container

Mac: Apples container usage

```bash
container run -d --name my-redis docker.io/library/redis:latest
container run -d --name my-redis \
 --memory 512M \
 --cpus 2 \
 docker.io/library/redis:latest
container list --all
````

Test it with:

```bash
printf "PING\r\n" | nc 192.168.64.2 6379
```

## Adding Worker Functions

To add new worker functions that can be processed by `robotni_arq`, follow these steps:

1. **Define your task in `tasks.py`**:

   Create an asynchronous function in `robotni_arq/tasks.py` that performs the desired work. This function will be the task that `arq` workers execute.

   ```python
   # robotni_arq/tasks.py

   import asyncio

   async def my_new_worker_task(ctx, data: dict):
       """An example of a new worker task."""
       print(f"Received data: {data}")
       await asyncio.sleep(2) # Simulate some work
       return {"status": "completed", "data_processed": data}
   ```

2. **Ensure the worker can discover your task**:

   The `arq` worker automatically discovers functions defined in `tasks.py`. No additional configuration is typically needed here, as long as your task is defined in `tasks.py` and the worker is configured to load tasks from this module.

3. **Enqueue your task via the API**:

   You can enqueue your new task by making a request to the FastAPI application's `/enqueue_task` endpoint, specifying the task type.

   Example using `curl`:

   ```bash
   curl -X POST "http://127.0.0.1:8000/enqueue_task" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "task_type=fake_task"
   ```

   The `task_type` should correspond to a task type handled by the API, such as `fake_task`.

By following these steps, you can easily extend `robotni_arq` to handle a variety of background processing needs.

## Contributing

Contributions are welcome! Please refer to the `README.md` in the root of the `robotni` project for general contribution guidelines.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
