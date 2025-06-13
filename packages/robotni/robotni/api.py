# DEPRECATED: All API logic has been consolidated into run.py.
# This file is kept for reference only.

from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response, Request
import uuid
from typing import Dict, Any
from arq import create_pool
from arq.connections import RedisSettings
import subprocess

app = FastAPI(title="Robotni API",
              description="A simple worker management system")

# Redis settings for arq
REDIS_SETTINGS = RedisSettings(host='localhost', port=6379)

# Global Redis pool and worker process status
redis_pool = None
worker_process = None
worker_active = False
worker_start_time = None
job_enqueue_times = {}  # Dictionary to store enqueue times for jobs

# Startup event to create Redis pool


@app.on_event("startup")
async def startup_event():
    global redis_pool, worker_process, worker_active, worker_start_time
    redis_pool = await create_pool(REDIS_SETTINGS)
    worker_process = None
    worker_active = False
    worker_start_time = None
    print("[API] Redis pool created.")

# Shutdown event to close Redis pool and stop worker if running


@app.on_event("shutdown")
async def shutdown_event():
    global worker_process, worker_active, worker_start_time
    if redis_pool:
        await redis_pool.close()
        print("[API] Redis pool closed.")
    if worker_process and worker_active:
        worker_process.terminate()
        worker_active = False
        worker_start_time = None
        print("[API] Worker process terminated on shutdown.")

# Pydantic model for job submission


class JobSubmission(BaseModel):
    type: str
    params: Dict[str, Any] = {}

# Endpoint to submit a job and start worker if not running


@app.post("/api/worker/jobs")
async def submit_job(job: JobSubmission):
    global worker_process, worker_active, job_enqueue_times
    if job.type != "fakejob":
        raise HTTPException(
            status_code=400, detail=f"Unknown job type: {job.type}")

    job_id = str(uuid.uuid4())
    try:
        # Start worker if not already running
        if not worker_active:
            try:
                # Adjust the worker settings path to match your project structure
                worker_process = subprocess.Popen(
                    ["arq", "robotni.workers.WorkerSettings"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                worker_active = True
                import time
                global worker_start_time
                worker_start_time = time.time()
                print("[API] Started worker process to handle jobs.")
                # Start a background task to monitor idle timeout
                from fastapi import BackgroundTasks
                background_tasks = BackgroundTasks()
                background_tasks.add_task(monitor_worker_idle_timeout)
            except Exception as e:
                print(f"[API] Failed to start worker process: {str(e)}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to start worker: {str(e)}")

        # Enqueue the job using arq
        job_instance = await redis_pool.enqueue_job(
            'process_fakejob',
            job_id,
            job.params,
            _job_id=job_id  # Use job_id as arq's internal job ID
        )
        import time
        job_enqueue_times[job_id] = time.time()
        print(
            f"[API] Enqueued job with ID: {job_id}, Instance: {job_instance}")
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        print(
            f"[API] Failed to enqueue job with ID: {job_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to enqueue job: {str(e)}")

# Endpoint to get job status/details


@app.get("/api/worker/jobs/{job_id}")
async def get_job_status(job_id: str, response: Response, request: Request):
    if not redis_pool:
        raise HTTPException(
            status_code=503, detail="Redis pool not initialized.")

    try:
        # timeout=0 means don't wait
        job_result = await redis_pool._get_job_result(job_id)
    except AttributeError:
        job_result = None  # Fallback if decode error occurs
    # Since direct job status retrieval methods are not available, infer status from result availability
    display_status = 'queued'  # Default status
    if job_result is not None:
        display_status = 'done'  # If result is available, assume job is done
        print(f"[API] Job {job_id} assumed done based on result availability")
    else:
        # Check if worker is active, which might indicate jobs are running
        if worker_active:
            display_status = 'running (assumed)'
        print(
            f"[API] Job {job_id} assumed {display_status} as no result is available yet")

    import time
    elapsed_time = int(time.time() - job_enqueue_times.get(job_id,
                       time.time())) if job_id in job_enqueue_times else 0
    job_data = {
        "id": job_id,
        "status": display_status,
        "elapsed_time_seconds": elapsed_time,
        "result": None,
        "error": None
    }

    if display_status == 'done':
        job_data["result"] = job_result
    elif display_status == 'failed':
        # arq returns the exception object for failed jobs
        job_data["error"] = str(job_result) if job_result else "Unknown error"

    # Simple ETag based on job status and result/error
    etag = f"{job_data['status']}-{job_data.get('result', '')}-{job_data.get('error', '')}"
    response.headers['ETag'] = etag

    if "If-None-Match" in request.headers and request.headers["If-None-Match"] == etag:
        response.status_code = 304  # Not Modified
        return None

    return job_data

# Endpoint for system status


@app.get("/api/worker/status")
async def get_system_status():
    global worker_active, worker_start_time
    import time
    running_time = 0
    if worker_active and worker_start_time is not None:
        running_time = int(time.time() - worker_start_time)
    # arq doesn't directly expose queue depth easily without iterating or specific commands
    # For simplicity, we'll return a placeholder or implement more complex Redis queries if needed.
    return {
        "queue_depth": "N/A (arq manages queue)",
        "active_workers": "Yes" if worker_active else "No",
        "worker_running_time_seconds": running_time if worker_active else 0,
        "status": "running"
    }

# Background task to monitor worker idle timeout


async def monitor_worker_idle_timeout():
    global worker_process, worker_active, worker_start_time
    import asyncio
    IDLE_TIMEOUT = 300  # 5 minutes idle timeout
    last_activity_time = asyncio.get_event_loop().time()
    print("[API] Starting worker idle timeout monitor.")
    while worker_active:
        await asyncio.sleep(60)  # Check every minute
        current_time = asyncio.get_event_loop().time()
        if current_time - last_activity_time > IDLE_TIMEOUT:
            if worker_process:
                worker_process.terminate()
                worker_active = False
                worker_start_time = None
                print("[API] Worker process terminated due to idle timeout.")
                break
        # Update last activity time if there are active jobs (simplified check)
        # In a real implementation, you might query Redis for active jobs
        # For now, we assume activity on job enqueue (updated in submit_job)
        # This is a placeholder for actual job activity monitoring

# Endpoint to list available worker types (static for now)


@app.get("/api/worker/types")
async def get_worker_types():
    return {
        "fakejob": {
            "description": "Test worker with random delay between 1s and specified seconds",
            "params": {
                "delay_seconds": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum delay in seconds (random between 1 and this value)"
                }
            }
        }
    }
