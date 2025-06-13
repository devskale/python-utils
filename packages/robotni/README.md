# **Robotni**

_A Scalable Python Worker Management System_  
Robotni is a worker management solution designed to automate and track the execution of Python commands. It receives worker action requests from a remote web application, queues these requests, performs the specified work by running available Python commands, and tracks the status of each task.

## **Overview**

Robotni is a backend service that:

1. **Queues** Python-based jobs (e.g., document parsing, AI analysis).
2. **Executes** them in isolated workers.
3. **Tracks** status/results via a polling API.

Built for reliability, scalability, and simple integration.

---

## **Getting Started**

### **Installation**

Robotni is currently a minimal implementation that can be run locally. Follow these steps to set it up:

1. Ensure you have Python 3.6+ installed.
2. Install the required dependencies:
   ```bash
   cd packages/robotni
   pip install fastapi uvicorn
   ```
3. Run the application:

   ```bash
   python run.py
   ```

   The server will start on `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

   > **Note:** The default `run.py` starts Uvicorn in development mode with `reload=True`. For production, remove the `reload` flag.

### **Current Implementation**

This version of Robotni is a super-simple setup focused on the `fakejob` worker type for testing purposes. It includes:

- **API Server**: Built with FastAPI, providing endpoints for job management.
- **Job Queue**: An in-memory queue for pending jobs.
- **Worker**: A single-threaded worker processing the `fakejob` type, which simulates work by waiting a random time between 1 second and a specified parameter.
- **Status Storage**: Job status and results are stored in `jobs.json`.

---

## **API Schema**

### **Authentication**

- Currently, no authentication is implemented in this minimal version. Future updates may include Bearer Token support.

### **Endpoints**

#### **Job Management**

| Method | Endpoint                   | Description                                                 |
| ------ | -------------------------- | ----------------------------------------------------------- |
| `POST` | `/api/worker/jobs`         | Submit a job. Returns `job_id`. (Body: `type`, `params`)    |
| `GET`  | `/api/worker/jobs/{jobId}` | Get job details (status, results). Supports `ETag` caching. |
| `GET`  | `/api/worker/status`       | System health (queue depth, active workers).                |
| `GET`  | `/api/worker/types`        | List available worker types and their input schemas.        |

---

## **Worker Types**

| Type      | Description                       | Example `params`                                |
| --------- | --------------------------------- | ----------------------------------------------- |
| `fakejob` | Test worker (random 1-10s delay). | `{ "delay_seconds": 5 }` (optional, default: 5) |

---

## **Workflow Example**

1. **Submit a Job**

   ```bash
   curl -X POST http://localhost:8000/api/worker/jobs -H "Content-Type: application/json" -d '{"type": "fakejob", "params": {"delay_seconds": 10}}'
   ```

   → Returns `{ "job_id": "uuid-string", "status": "queued" }`

2. **Poll for Status**
   ```bash
   curl http://localhost:8000/api/worker/jobs/{job_id}
   ```
   → Returns job status, e.g., `{ "id": "uuid-string", "status": "done", "result": {"waited": 7}, "error": null }`

---

## **Key Features**

✅ **Minimal Setup**

- Simple architecture with FastAPI, in-memory queue, and JSON storage for easy deployment.

✅ **Efficient Polling**

- `ETag` headers reduce unnecessary data transfer during status checks.

---

## **Potential Extensions**

- **Authentication**: Add Bearer Token support for secure API access.
- **More Worker Types**: Implement additional workers like `parsing`, `anonymization`, and `analysis`.
- **Scalability**: Upgrade to a robust queue (e.g., Redis) and database (e.g., PostgreSQL) for larger workloads.
- **Rate Limiting**: Per-client API quotas.
- **Priority Queues**: Urgent vs. batch jobs.
- **Scheduled Jobs**: Deferred execution.
- **Arq & Redis Integration**: Use [Arq](https://arq-docs.helpmanual.io/) (a Python job queue) with Redis for distributed scheduling, background processing, and scalable job management.

---
