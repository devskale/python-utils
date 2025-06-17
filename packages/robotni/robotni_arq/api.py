from fastapi import FastAPI, Request # Removed Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from arq.connections import ArqRedis, create_pool
from arq.jobs import Job, JobStatus, JobDef, JobResult
from arq.constants import default_queue_name, result_key_prefix # Added result_key_prefix
from dotenv import load_dotenv
import os
import random
from redis.exceptions import ResponseError
from pydantic import BaseModel # Added import
from typing import Dict, Any # Added import

from robotni_arq.workers.worker import WorkerSettings

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List # Added List here as well for JobDetails

from arq import create_pool
from arq.connections import RedisSettings

load_dotenv()

app = FastAPI()

# Mount static files if you have any (e.g., CSS, JS)
# app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

REDIS_SETTINGS = WorkerSettings.redis_settings
redis_pool: ArqRedis = None

# --- Pydantic Models for API Specification ---
class JobBase(BaseModel):
    id: str
    type: str
    name: str
    status: str
    project: Optional[str] = None
    createdAt: datetime
    progress: int
    parameters: Dict[str, Any]

class JobDetails(JobBase):
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    duration: Optional[int] = None # in seconds
    result: Optional[Any] = None

class SuccessPostResponse(BaseModel):
    success: bool = True
    data: JobBase

class SuccessGetResponse(BaseModel):
    success: bool = True
    data: List[JobDetails]

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# --- End Pydantic Models ---

@app.on_event("startup")
async def startup_event():
    global redis_pool
    redis_pool = await create_pool(REDIS_SETTINGS)

@app.on_event("shutdown")
async def shutdown_event():
    if redis_pool:
        await redis_pool.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Optionally, you could fetch job statuses here to display on the page
    return templates.TemplateResponse("index.html", {"request": request})

# Define Pydantic model for the request body
class JobEnqueueRequest(BaseModel):
    type: str
    name: str
    project: Optional[str] = None
    parameters: Dict[str, Any]

@app.post("/api/worker/jobs", response_model=SuccessPostResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def enqueue_job_endpoint(request_body: JobEnqueueRequest):
    if not redis_pool:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="Redis connection not available").dict()
        )

    job_function_name = request_body.type
    job_parameters = request_body.parameters
    job_id_placeholder = f"job_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{random.randint(10000, 99999):x}"

    try:
        # Pass parameters as a dictionary
        arq_job: Optional[Job] = await redis_pool.enqueue_job(job_function_name, job_parameters)
        
        if not arq_job:
            # This case should ideally not happen if enqueue_job doesn't raise an error but returns None
            print(f"Failed to enqueue job {job_function_name} with params {job_parameters} - arq_job is None")
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error=f"Failed to enqueue job of type '{job_function_name}'.",
                    details="Arq pool returned None without raising an exception."
                ).dict()
            )

        created_job_data = JobBase(
            id=arq_job.job_id,
            type=job_function_name,
            name=request_body.name,
            status="pending", # Arq job status will update once picked by worker
            project=request_body.project,
            createdAt=datetime.now(timezone.utc), # Actual enqueue time from arq_job.info() might be slightly different
            progress=0,
            parameters=job_parameters
        )
        print(f"Enqueued job: {arq_job.job_id} for function {job_function_name} with parameters {job_parameters}")
        return SuccessPostResponse(data=created_job_data)

    except Exception as e:
        print(f"Error enqueueing job {job_function_name} with params {job_parameters}: {e}")
        # Check if it's a Zod-like validation error (though Pydantic handles it before this point)
        # For now, general error for enqueueing issues.
        return JSONResponse(
            status_code=400, # Or 500 depending on error type
            content=ErrorResponse(
                error=f"Failed to enqueue job of type '{job_function_name}'.",
                details=str(e)
            ).dict()
        )

@app.get("/api/worker/jobs", response_model=SuccessGetResponse, responses={500: {"model": ErrorResponse}})
async def get_all_jobs_endpoint():
    if not redis_pool:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="Redis connection not available").dict()
        )

    all_jobs_details: List[JobDetails] = []

    try:
        # 1. Get Queued/Active Jobs from default_queue_name (Arq's main queue)
        # Arq stores job IDs in a ZSET (newer versions) or LIST (older versions)
        queued_job_ids = []
        if await redis_pool.exists(default_queue_name):
            key_type = await redis_pool.type(default_queue_name)
            if key_type == b'zset':
                raw_job_ids = await redis_pool.zrange(default_queue_name, 0, -1, withscores=False)
                queued_job_ids = [job_id.decode() for job_id in raw_job_ids if job_id]
            elif key_type == b'list':
                raw_job_ids = await redis_pool.lrange(default_queue_name, 0, -1)
                queued_job_ids = [job_id.decode() for job_id in raw_job_ids if job_id]
            else:
                # Log this unexpected scenario but try to continue if possible
                print(f"Warning: Unexpected key type for {default_queue_name}: {key_type.decode()}")

        # 2. Get Completed/Failed Jobs from result keys (arq:result:*)
        # Corrected the way to get result keys prefix
        result_keys_raw = await redis_pool.keys(f"{result_key_prefix}*") 
        result_job_ids = [key.decode().split(':')[-1] for key in result_keys_raw]
        
        # Combine and deduplicate job IDs
        # A job ID might appear in queue and then in results if processing is fast
        # or if there's overlap in fetching.
        unique_job_ids = sorted(list(set(queued_job_ids + result_job_ids)))

        for job_id in unique_job_ids:
            try:
                job_instance = Job(job_id, redis_pool)
                info: Optional[JobDef] = await job_instance.info()
                status_str: str = await job_instance.status()
                result_data: Optional[Any] = None
                progress_val = 0

                if status_str == 'complete': # Use string literal 'complete'
                    result_data = await job_instance.result(timeout=1) # Add a small timeout
                    progress_val = 100
                elif status_str == 'failed': # Use string literal 'failed'
                    # Attempt to get result, which might contain error details for failed jobs
                    try:
                        result_data = await job_instance.result(timeout=1)
                    except Exception as e_res:
                        result_data = {"error_fetching_result": str(e_res)}
                    progress_val = 100 # Or some other indicator for failed
                elif status_str in ['in_progress', 'deferred']: # Use string literals
                    # For in-progress, progress might be dynamically updated by the task itself.
                    # Here, we'll set a placeholder or could try to fetch from a custom progress key if implemented.
                    progress_val = 50 # Placeholder for in-progress
                # For 'queued' and 'deferred', progress is 0 by default.

                if info: # job.info() can return None if job details are gone (e.g., expired)
                    # Attempt to get project and name from kwargs if they were stored there
                    # This depends on how jobs are enqueued. If 'name' and 'project' are not part of
                    # the task's actual parameters, they won't be in info.kwargs directly.
                    # The POST endpoint now returns these from the request body, but they are not
                    # inherently part of the arq JobDef unless passed as task args.
                    # For now, we'll use placeholders or assume they might be in kwargs.
                    job_name = info.kwargs.get('name', 'N/A') 
                    job_project = info.kwargs.get('project', 'N/A')
                    
                    # If 'name' and 'project' were part of the original JobEnqueueRequest but not passed to the task,
                    # we'd need a separate mechanism to store/retrieve them per job_id.
                    # For this example, we'll assume they might be in task params or use placeholders.

                    all_jobs_details.append(
                        JobDetails(
                            id=job_id,
                            type=info.function,
                            name=job_name, # Placeholder, ideally from a persistent store or task args
                            status=status_str,
                            project=job_project, # Placeholder
                            createdAt=getattr(info, 'enqueue_time', datetime.now(timezone.utc)).astimezone(timezone.utc) if getattr(info, 'enqueue_time', None) else datetime.now(timezone.utc),
                            startedAt=getattr(info, 'start_time', None).astimezone(timezone.utc) if getattr(info, 'start_time', None) else None,
                            completedAt=getattr(info, 'finish_time', None).astimezone(timezone.utc) if getattr(info, 'finish_time', None) else None,
                            duration=int((finish_time_val - start_time_val).total_seconds()) if (start_time_val := getattr(info, 'start_time', None)) and (finish_time_val := getattr(info, 'finish_time', None)) else None,
                            progress=progress_val,
                            result=result_data,
                            parameters=info.kwargs # Parameters are now directly in kwargs
                        )
                    )
                else:
                    # Job info might be missing if it expired or was cleaned up
                    # Try to provide minimal info if status is known
                    # Use getattr for potentially missing attributes even in this fallback
                    current_time_utc = datetime.now(timezone.utc)
                    all_jobs_details.append(
                        JobDetails(
                            id=job_id,
                            type=getattr(info, 'function', 'unknown_type') if info else 'unknown_type',
                            name=getattr(info, 'kwargs', {}).get('name', 'unknown_name') if info else 'unknown_name',
                            status=status_str if status_str else "unknown_status",
                            project=getattr(info, 'kwargs', {}).get('project', 'unknown_project') if info else 'unknown_project',
                            createdAt=current_time_utc, # Fallback, as enqueue_time might not be available
                            startedAt=None,
                            completedAt=None,
                            duration=None,
                            progress=0,
                            result=None,
                            parameters=getattr(info, 'kwargs', {}) if info else {}
                        )
                    )
            except Exception as e_job:
                print(f"Error fetching details for job {job_id}: {e_job}")
                # Add a basic entry for jobs that error during detail fetching
                all_jobs_details.append(
                    JobDetails(
                        id=job_id,
                        type="error_fetching",
                        name="error_fetching",
                        status="error",
                        createdAt=datetime.now(timezone.utc),
                        progress=0,
                        parameters={"error_details": str(e_job)}
                    )
                )

        # Sort by createdAt, newest first
        # Handle potential type mismatches in createdAt field
        all_jobs_details.sort(key=lambda j: j.createdAt if isinstance(j.createdAt, datetime) else datetime.now(timezone.utc), reverse=True)
        return SuccessGetResponse(data=all_jobs_details)

    except ResponseError as e_redis:
        # Handle specific Redis errors like WRONGTYPE more gracefully if needed
        print(f"Redis ResponseError while fetching all jobs: {e_redis}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="A Redis error occurred while fetching job list.", details=str(e_redis)).dict()
        )
    except Exception as e_main:
        print(f"Unexpected error in get_all_jobs_endpoint: {e_main}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error="An unexpected error occurred while fetching all jobs.", details=str(e_main)).dict()
        )

# @app.get("/list_jobs", response_class=JSONResponse)
# async def list_jobs_endpoint():
#     if not redis_pool:
#         return JSONResponse({"error": "Redis connection not available"}, status_code=500)
# 
#     queued_job_ids = []
#     try:
#         # Check if the queue key exists and what type it is
#         key_exists = await redis_pool.exists(default_queue_name)
#         if not key_exists:
#             # No jobs queued
#             pass
#         else:
#             key_type = await redis_pool.type(default_queue_name)
#             if key_type == b'zset':
#                 # arq uses sorted sets in newer versions
#                 raw_job_ids = await redis_pool.zrange(default_queue_name, 0, -1)
#                 queued_job_ids = [job_id.decode() for job_id in raw_job_ids if job_id]
#             elif key_type == b'list':
#                 # Fallback for older arq versions that use lists
#                 raw_job_ids = await redis_pool.lrange(default_queue_name, 0, -1)
#                 queued_job_ids = [job_id.decode() for job_id in raw_job_ids if job_id]
#             else:
#                 print(f"Unexpected key type for {default_queue_name}: {key_type}")
#                 return JSONResponse({"error": f"Queue key has unexpected type: {key_type.decode()}"}, status_code=500)
#     except ResponseError as e:
#         if "WRONGTYPE" in str(e):
#             error_message = (
#                 f"Redis key '{default_queue_name}' is not a list. "
#                 "This can happen if the key was modified externally. "
#                 f"Try deleting the key in Redis (e.g., 'DEL {default_queue_name}' via redis-cli) "
#                 "and restarting the arq worker and FastAPI app. "
#                 "This will clear the existing (malformed) queue."
#             )
#             print(f"WRONGTYPE error accessing {default_queue_name}: {e}")
#             return JSONResponse({"error": error_message, "details": str(e)}, status_code=500)
#         else:
#             print(f"Redis ResponseError while fetching job list: {e}")
#             return JSONResponse({"error": "A Redis error occurred while fetching job list.", "details": str(e)}, status_code=500)
#     except Exception as e:
#         print(f"Unexpected error in list_jobs_endpoint while fetching job IDs: {e}")
#         return JSONResponse({"error": "An unexpected error occurred while fetching job IDs.", "details": str(e)}, status_code=500)
# 
#     jobs_details = []
#     for job_id in queued_job_ids: # Iterate over decoded job IDs
#         try:
#             job_instance = Job(job_id, redis_pool)
#             info = await job_instance.info()
#             status = await job_instance.status()
#             if info: # job.info() can return None if job details are gone
#                  jobs_details.append({
#                     "job_id": job_id,
#                     "function": info.function,
#                     "args": info.args,
#                     "kwargs": info.kwargs,
#                     "enqueue_time": info.enqueue_time.isoformat() if info.enqueue_time else None,
#                     "status": status
#                 })
#             else:
#                 # This case might happen if the job was processed and its info cleaned up
#                 # but somehow its ID was still in a list (less common for default queue)
#                 jobs_details.append({
#                     "job_id": job_id,
#                     "function": "N/A (info not found or job processed)",
#                     "status": status # status might still be 'complete' or 'not_found'
#                 })
#         except Exception as e:
#             print(f"Error fetching info for job {job_id}: {e}")
#             jobs_details.append({"job_id": job_id, "error": str(e), "status": "error_fetching_info"})
#     
#     return JSONResponse({"jobs": jobs_details})

@app.get("/job/{job_id}") # Will be removed or adapted if needed later
async def get_job_status(job_id: str):
    if not redis_pool:
        return {"error": "Redis connection not available"}
    job = Job(job_id, redis_pool)
    status = await job.status()
    info = await job.info()
    return {"job_id": job_id, "status": status, "info": info}

# @app.get("/completed_jobs", response_class=JSONResponse)
# async def get_completed_jobs():
#     if not redis_pool:
#         return JSONResponse({"error": "Redis connection not available"}, status_code=500)
#     
#     try:
#         # Get all result keys (completed jobs)
#         result_keys = await redis_pool.keys("arq:result:*")
#         
#         completed_jobs = []
#         for key in result_keys:
#             try:
#                 job_id = key.decode().split(":")[-1]  # Extract job ID from arq:result:job_id
#                 job_instance = Job(job_id, redis_pool)
#                 info = await job_instance.info()
#                 status = await job_instance.status()
#                 
#                 if info and status in ['complete', 'failed']:
#                     # Get the result if available
#                     result = await job_instance.result()
#                     completed_jobs.append({
#                         "job_id": job_id,
#                         "function": info.function,
#                         "args": info.args,
#                         "kwargs": info.kwargs,
#                         "enqueue_time": info.enqueue_time.isoformat() if info.enqueue_time else None,
#                         "start_time": info.start_time.isoformat() if info.start_time else None,
#                         "finish_time": info.finish_time.isoformat() if info.finish_time else None,
#                         "status": status,
#                         "result": str(result) if result else None
#                     })
#             except Exception as e:
#                 print(f"Error fetching completed job info for {key}: {e}")
#                 continue
#         
#         # Sort by finish_time (most recent first) and take last 3
#         # Use actual datetime objects for proper sorting, fallback to a very old date for None values
#         from datetime import datetime
#         completed_jobs.sort(
#             key=lambda x: datetime.fromisoformat(x['finish_time'].replace('Z', '+00:00')) if x['finish_time'] else datetime.min, 
#             reverse=True
#         )
#         return JSONResponse({"completed_jobs": completed_jobs[:3]})
#         
#     except Exception as e:
#         print(f"Error fetching completed jobs: {e}")
#         return JSONResponse({"error": "Failed to fetch completed jobs", "details": str(e)}, status_code=500)

# To run this app:
# 1. Start Redis: redis-server
# 2. Start the arq worker: arq robotni_arq.workers.worker.WorkerSettings
# 3. Start FastAPI: uvicorn robotni_arq.api:app --reload
