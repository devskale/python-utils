from fastapi import FastAPI, HTTPException

from .models import JobCreate
from .tasks import example_task, huey

app = FastAPI(
    title="robotni",
    description="A minimal, file-based task scheduler to run Python jobs from a web app, with async task queuing and status polling.",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "robotni API is running"}


@app.post("/api/worker/jobs")
async def submit_job(job: JobCreate):
    # For demonstration, submit the example_task with dummy params
    try:
        # You can map job.name to actual tasks in a real implementation
        task = example_task(job.params.get("x", 1), job.params.get("y", 2))
        return {"job_id": str(task.id), "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
