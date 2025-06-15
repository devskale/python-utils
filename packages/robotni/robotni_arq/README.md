# Project: robotni - Minimal Task Scheduler

**Package Name**: `robotni_arq`

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
- [arq](https://github.com/python-arq/arq) (task queue and job management)
- FastAPI (web API framework)

---

python Workers are located in the `./workers/` directory and are responsible for executing the background tasks.

## 4. Installation

(Add installation instructions here, e.g., `pip install robotni_arq` or cloning the repository and setting up the environment.)

## 5. Usage

(Add usage examples here, e.g., how to enqueue a task and check its status.)

# Robotni ARQ: Lightweight Python Task Scheduler

`robotni_arq` is a simple, yet powerful task scheduler built with `arq` for managing asynchronous and long-running jobs in Python applications, exposed via a `FastAPI` web API.

## Features

- **Task Queuing**: Efficiently queue and process background tasks.
- **Concurrency**: Supports concurrent execution for both I/O-bound and CPU-bound tasks.
- **Job Monitoring**: Simple API for submitting, monitoring, and revoking jobs.
- **Web Interface**: Basic web demo for visualization and testing (planned).

## Getting Started

### Prerequisites

- Python 3.8+
- Redis server running (e.g., via Docker or locally)

### Installation

1.  **Clone the repository** (if you haven't already) and navigate to the `robotni_arq` directory:
    ```bash
    git clone https://github.com/yourusername/robotni.git
    cd robotni/packages/robotni/robotni_arq
    ```

2.  **Install the package in editable mode**:
    ```bash
    pip install -e .
    ```

    This command will install all necessary dependencies specified in `pyproject.toml` and link your local project files, allowing for direct execution and development.

### Running the Application

#### 1. Start the Redis Server

Ensure your Redis server is running. If using Docker, you can start it with:

```bash
docker run --name some-redis -p 6379:6379 -d redis
```

#### 2. Start the ARQ Worker

To start the ARQ worker (from the `robotni_arq` directory):

```bash
arq workers.worker.WorkerSettings
```

This worker will pick up and execute tasks from the Redis queue.

#### 3. Start the FastAPI Application

Open another terminal, navigate to the `robotni_arq` directory, and run the FastAPI application using Uvicorn:

```bash
uvicorn robotni_arq.main:app --reload
```

This will start the API server, typically accessible at `http://127.0.0.1:8000`.

#### 4. Enqueue Tasks (Client Example)

To enqueue tasks, you can run the `client.py` script. In a new terminal:

```bash
python3 client.py
```

This will add sample `long_running_task` and `cpu_bound_task` jobs to the Redis queue, which the ARQ worker will then process. Observe the output in the ARQ worker's terminal.

## Project Structure

```
robotni_arq/
├── __init__.py
├── main.py             # FastAPI application, Redis connection setup
├── tasks.py            # Defines ARQ tasks (e.g., long_running_task, cpu_bound_task)
├── client.py           # Example script to enqueue tasks
├── requirements.txt    # Project dependencies
├── README.md           # This file
├── container/          # Container configuration files (redis.conf)
├── webdemo/            # (Future) Web interface for monitoring
└── workers/
    └── worker.py       # ARQ worker configuration
```

## Container

Mac: Apples container usage

.venvjohannwaldherr@jMacAir robotni % container run -d --name my-redis docker.io/library/redis:latest
my-redis

container run -d --name my-redis \
 --memory 512M \
 --cpus 2 \
 docker.io/library/redis:latest

.venvjohannwaldherr@jMacAir robotni % container list --all  
ID IMAGE OS ARCH STATE ADDR
my-redis docker.io/library/redis:latest linux arm64 running 192.168.64.2

test it with
.venvjohannwaldherr@jMacAir container % printf "PING\r\n" | nc 192.168.64.2 6379
+PONG

## Contributing

Contributions are welcome! Please refer to the `README.md` in the root of the `robotni` project for general contribution guidelines.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
