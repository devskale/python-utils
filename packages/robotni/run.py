from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response, Request
import random
import uuid
import time
import threading
import uvicorn
from robotni.workers.fakeJob import run_fakejob


app = FastAPI(title="Robotni API",
              description="A simple worker management system")

# In-memory job queue and storage
job_queue = []
jobs: Dict[str, Dict[str, Any]] = {}


class JobRequest(BaseModel):
    type: str
    params: Optional[Dict[str, Any]] = {}


@app.get("/api/worker/types")
def get_worker_types():
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


@app.post("/api/worker/jobs")
def submit_job(job: JobRequest):
    if job.type != "fakejob":
        raise HTTPException(status_code=400, detail="Unsupported job type")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "type": job.type,
        "params": job.params,
        "status": "queued",
        "result": None,
        "error": None,
    }
    job_queue.append(job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/worker/jobs/{job_id}")
def get_job(job_id: str, response: Response, request: Request):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # ETag support
    etag = f"{job['status']}-{job.get('result', '')}-{job.get('error', '')}"
    response.headers['ETag'] = etag
    if "if-none-match" in request.headers and request.headers["if-none-match"] == etag:
        response.status_code = 304
        return None
    return job


@app.get("/api/worker/status")
def get_system_status():
    # Count jobs that are waiting in the queue (status == "queued")
    waiting = sum(1 for job in jobs.values() if job["status"] == "queued")
    # Count jobs that are currently running
    running = sum(1 for job in jobs.values() if job["status"] == "running")
    # System is "running" if any jobs are queued or running, else "idle"
    system_status = "running" if (waiting > 0 or running > 0) else "idle"
    return {
        "queue_depth": waiting,
        "active_workers": running,
        "status": system_status
    }


def fakejob_worker():
    while True:
        if job_queue:
            job_id = job_queue.pop(0)
            job = jobs[job_id]
            job["status"] = "running"
            try:
                delay = job["params"].get("delay_seconds", 5)
                # Call external script's function
                result = run_fakejob(delay)
                job["status"] = "done"
                job["result"] = result
            except Exception as e:
                job["status"] = "failed"
                job["error"] = str(e)
        else:
            time.sleep(0.2)


# Start worker thread
worker_thread = threading.Thread(target=fakejob_worker, daemon=True)
worker_thread.start()

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True)
