from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional, Dict, Any
from .workers import submit_job

app = FastAPI(
    title="robotni",
    description="A minimal, file-based task scheduler to run Python jobs from a web app, with async task queuing and status polling.",
    version="0.1.0",
)


class JobRequest(BaseModel):
    name: str
    params: Dict[str, Any] = {}


class JobResponse(BaseModel):
    job_id: str
    status: str


@app.get("/")
async def root():
    return {"message": "robotni API is running"}


@app.post("/api/worker/jobs", response_model=JobResponse)
async def create_job(job: JobRequest):
    job_id = str(uuid4())
    try:
        submit_job(job_id, job.name, job.params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JobResponse(job_id=job_id, status="submitted")
