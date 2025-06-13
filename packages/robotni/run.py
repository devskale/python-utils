from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import random
import uuid
import time
import threading
import uvicorn
from robotni.workers.fakeJob import run_fakejob


app = FastAPI()

# In-memory job queue and storage
job_queue = []
jobs: Dict[str, Dict[str, Any]] = {}


class JobRequest(BaseModel):
    type: str
    params: Optional[Dict[str, Any]] = {}


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
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


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
