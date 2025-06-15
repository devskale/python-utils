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

#### 1. Start the Redis Server

Ensure your Redis server is running. If using Docker, you can start it with:

```bash
docker run --name some-redis -p 6379:6379 -d redis
```

On MACOS

```bash
container run --detach my-redis
container start my-redis
container list --all
```

#### 2. Start the ARQ Worker

Open a terminal in the parent directory (`/Users/johannwaldherr/code/python-utils/packages/robotni/`) and run the ARQ worker:

```bash
arq robotni_arq.workers.worker.WorkerSettings
```

This worker will pick up and execute tasks from the Redis queue.

#### 3. Start the FastAPI Application

Open another terminal in the parent directory (`/Users/johannwaldherr/code/python-utils/packages/robotni/`) and run the FastAPI application using Uvicorn:

```bash
uvicorn robotni_arq.api:app --reload
```

This will start the API server, typically accessible at `http://127.0.0.1:8000`.

## Project Structure

```
robotni_arq/
├── __init__.py
├── api.py              # FastAPI application, Redis connection setup
├── tasks.py            # Defines ARQ tasks (e.g., long_running_task, cpu_bound_task)
├── requirements.txt    # Project dependencies
├── README.md           # This file
├── container/          # Container configuration files (redis.conf)
├── webdemo/            # (Future) Web interface for monitoring
└── workers/
    └── worker.py       # ARQ worker configuration
```

## Container

Mac: Apples container usage

```bash
container run -d --name my-redis docker.io/library/redis:latest
container run -d --name my-redis \
 --memory 512M \
 --cpus 2 \
 docker.io/library/redis:latest
container list --all
```

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

    You can enqueue your new task by making a request to the FastAPI application's `/enqueue` endpoint, specifying the task name and any necessary arguments.

    Example using `curl`:

    ```bash
    curl -X POST "http://127.0.0.1:8000/enqueue" \
         -H "Content-Type: application/json" \
         -d '{
               "function_name": "my_new_worker_task",
               "args": {"message": "Hello from new task!"}
             }'
    ```

    The `function_name` should match the name of your asynchronous function defined in `tasks.py`.

By following these steps, you can easily extend `robotni_arq` to handle a variety of background processing needs.

## Contributing

Contributions are welcome! Please refer to the `README.md` in the root of the `robotni` project for general contribution guidelines.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
