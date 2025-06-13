from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
import queue
import threading
import json
import os
import uuid
from typing import Dict, Any
from workers import process_fakejob

app = FastAPI(title="Robotni API", description="A simple worker management system")

# In-memory queue for jobs
job_queue = queue.Queue()

# Path to status storage file
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.json")

# Load jobs from file (if exists)
def load_jobs() -> Dict[str, Dict[str, Any]]:
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# Save jobs to file
def save_jobs(jobs: Dict[str, Dict[str, Any]]):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

# Worker thread function to process jobs from the queue
def worker_thread():
    jobs = load_jobs()
    print("[Worker] Worker thread started, waiting for jobs...")
    while True:
        try:
            # Get a job from the queue (blocking)
            job = job_queue.get()
            job_id = job["id"]
            job_type = job["type"]
            params = job.get("params", {})
            print(f"[Worker] Processing job {job_id} of type {job_type}")
            
            # Define a status update function for use during processing
            def update_status(jid, status):
                # Reload jobs to ensure we have the latest state before updating
                current_jobs = load_jobs()
                if jid in current_jobs:
                    current_jobs[jid]["status"] = status
                    save_jobs(current_jobs)
                    print(f"[Worker] Updated status for job {jid} to {status}")
                else:
                    print(f"[Worker] Job {jid} not found in current jobs, cannot update status to {status}")
            
            # Process based on job type
            if job_type == "fakejob":
                result, error = process_fakejob(params, job_id, update_status)
                if error:
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error"] = error
                    print(f"[Worker] Job {job_id} failed: {error}")
                else:
                    jobs[job_id]["status"] = "done"
                    jobs[job_id]["result"] = result
                    print(f"[Worker] Job {job_id} completed successfully")
            else:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = f"Unknown job type: {job_type}"
                print(f"[Worker] Job {job_id} failed: Unknown job type {job_type}")
            
            save_jobs(jobs)
            job_queue.task_done()
            print(f"[Worker] Job {job_id} processing complete, queue size: {job_queue.qsize()}")
        except Exception as e:
            if job_id in jobs:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(e)
                save_jobs(jobs)
                print(f"[Worker] Error processing job {job_id}: {str(e)}")
            else:
                print(f"[Worker] Unexpected error: {str(e)}")

# Start the worker thread on startup
@app.on_event("startup")
async def startup_event():
    worker = threading.Thread(target=worker_thread, daemon=True)
    worker.start()

# Pydantic model for job submission
class JobSubmission(BaseModel):
    type: str
    params: Dict[str, Any] = {}

# Endpoint to submit a job
@app.post("/api/worker/jobs")
async def submit_job(job: JobSubmission):
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "type": job.type,
        "params": job.params,
        "status": "queued",
        "result": None,
        "error": None
    }
    
    # Save to storage
    jobs = load_jobs()
    jobs[job_id] = job_data
    save_jobs(jobs)
    
    # Add to queue
    job_queue.put(job_data)
    
    return {"job_id": job_id, "status": "queued"}

# Endpoint to get job status/details
@app.get("/api/worker/jobs/{job_id}")
async def get_job_status(job_id: str, response: Response, request: Request):
    jobs = load_jobs()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    # Simple ETag based on job status and result/error
    etag = f"{job['status']}-{job.get('result', '')}-{job.get('error', '')}"
    response.headers['ETag'] = etag
    
    if "If-None-Match" in request.headers and request.headers["If-None-Match"] == etag:
        response.status_code = 304  # Not Modified
        return None
    
    return job

# Endpoint for system status
@app.get("/api/worker/status")
async def get_system_status():
    return {
        "queue_depth": job_queue.qsize(),
        "active_workers": 1,  # Simplified to 1 for now
        "status": "running"
    }

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
