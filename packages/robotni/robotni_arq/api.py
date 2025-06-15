from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse # Modified
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from arq.connections import ArqRedis, create_pool
from arq.jobs import Job
from arq.constants import default_queue_name # Added import
from dotenv import load_dotenv
import os
import random
from redis.exceptions import ResponseError # Added import

from robotni_arq.workers.worker import WorkerSettings # Import worker settings to access Redis settings

load_dotenv()

app = FastAPI()

# Mount static files if you have any (e.g., CSS, JS)
# app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

REDIS_SETTINGS = WorkerSettings.redis_settings
redis_pool: ArqRedis = None

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
    return templates.TemplateResponse("index.html", {"request": request}) # Removed tasks_running

@app.post("/enqueue_task", response_class=JSONResponse) # Changed response_class
async def enqueue_task_endpoint(request: Request, task_type: str = Form(...)): # task_type can be used if UI sends it
    if not redis_pool:
        return JSONResponse({"error": "Redis connection not available"}, status_code=500)

    job = None
    job_function_name = "" # To store the actual function name for the response

    # For now, let's assume the "+" button always triggers 'fake_task'
    # If you enhance the UI to select tasks, this logic can be expanded.
    if task_type == "fake_task": # We'll make the UI send this
        duration = random.randint(5, 15)
        task_name_param = f"WebTask-{random.randint(100, 999)}"
        job_function_name = "fake_task"
        job = await redis_pool.enqueue_job(job_function_name, duration, task_name_param)
    elif task_type == "another_fake_task": # Keeping this for potential future use
        message = f"Hello from WebUI-{random.randint(100,999)}"
        job_function_name = "another_fake_task"
        job = await redis_pool.enqueue_job(job_function_name, message)
    elif task_type == "task_uname":
        job_function_name = "task_uname"
        job = await redis_pool.enqueue_job(job_function_name)
    elif task_type == "task_ping":
        job_function_name = "task_ping"
        job = await redis_pool.enqueue_job(job_function_name)
    elif task_type == "task_uberlama":
        job_function_name = "task_uberlama"
        job = await redis_pool.enqueue_job(job_function_name)
    # Add more task types here if needed

    if job:
        print(f"Enqueued job: {job.job_id} for function {job_function_name}")
        return JSONResponse({"job_id": job.job_id, "function": job_function_name})
    else:
        print(f"Could not enqueue task of type: {task_type}")
        return JSONResponse({"error": f"Unknown or failed to enqueue task_type: {task_type}"}, status_code=400)

@app.get("/list_jobs", response_class=JSONResponse)
async def list_jobs_endpoint():
    if not redis_pool:
        return JSONResponse({"error": "Redis connection not available"}, status_code=500)

    queued_job_ids = []
    try:
        # Check if the queue key exists and what type it is
        key_exists = await redis_pool.exists(default_queue_name)
        if not key_exists:
            # No jobs queued
            pass
        else:
            key_type = await redis_pool.type(default_queue_name)
            if key_type == b'zset':
                # arq uses sorted sets in newer versions
                raw_job_ids = await redis_pool.zrange(default_queue_name, 0, -1)
                queued_job_ids = [job_id.decode() for job_id in raw_job_ids if job_id]
            elif key_type == b'list':
                # Fallback for older arq versions that use lists
                raw_job_ids = await redis_pool.lrange(default_queue_name, 0, -1)
                queued_job_ids = [job_id.decode() for job_id in raw_job_ids if job_id]
            else:
                print(f"Unexpected key type for {default_queue_name}: {key_type}")
                return JSONResponse({"error": f"Queue key has unexpected type: {key_type.decode()}"}, status_code=500)
    except ResponseError as e:
        if "WRONGTYPE" in str(e):
            error_message = (
                f"Redis key '{default_queue_name}' is not a list. "
                "This can happen if the key was modified externally. "
                f"Try deleting the key in Redis (e.g., 'DEL {default_queue_name}' via redis-cli) "
                "and restarting the arq worker and FastAPI app. "
                "This will clear the existing (malformed) queue."
            )
            print(f"WRONGTYPE error accessing {default_queue_name}: {e}")
            return JSONResponse({"error": error_message, "details": str(e)}, status_code=500)
        else:
            print(f"Redis ResponseError while fetching job list: {e}")
            return JSONResponse({"error": "A Redis error occurred while fetching job list.", "details": str(e)}, status_code=500)
    except Exception as e:
        print(f"Unexpected error in list_jobs_endpoint while fetching job IDs: {e}")
        return JSONResponse({"error": "An unexpected error occurred while fetching job IDs.", "details": str(e)}, status_code=500)

    jobs_details = []
    for job_id in queued_job_ids: # Iterate over decoded job IDs
        try:
            job_instance = Job(job_id, redis_pool)
            info = await job_instance.info()
            status = await job_instance.status()
            if info: # job.info() can return None if job details are gone
                 jobs_details.append({
                    "job_id": job_id,
                    "function": info.function,
                    "args": info.args,
                    "kwargs": info.kwargs,
                    "enqueue_time": info.enqueue_time.isoformat() if info.enqueue_time else None,
                    "status": status
                })
            else:
                # This case might happen if the job was processed and its info cleaned up
                # but somehow its ID was still in a list (less common for default queue)
                jobs_details.append({
                    "job_id": job_id,
                    "function": "N/A (info not found or job processed)",
                    "status": status # status might still be 'complete' or 'not_found'
                })
        except Exception as e:
            print(f"Error fetching info for job {job_id}: {e}")
            jobs_details.append({"job_id": job_id, "error": str(e), "status": "error_fetching_info"})
    
    return JSONResponse({"jobs": jobs_details})

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    if not redis_pool:
        return {"error": "Redis connection not available"}
    job = Job(job_id, redis_pool)
    status = await job.status()
    info = await job.info()
    return {"job_id": job_id, "status": status, "info": info}

@app.get("/completed_jobs", response_class=JSONResponse)
async def get_completed_jobs():
    if not redis_pool:
        return JSONResponse({"error": "Redis connection not available"}, status_code=500)
    
    try:
        # Get all result keys (completed jobs)
        result_keys = await redis_pool.keys("arq:result:*")
        
        completed_jobs = []
        for key in result_keys:
            try:
                job_id = key.decode().split(":")[-1]  # Extract job ID from arq:result:job_id
                job_instance = Job(job_id, redis_pool)
                info = await job_instance.info()
                status = await job_instance.status()
                
                if info and status in ['complete', 'failed']:
                    # Get the result if available
                    result = await job_instance.result()
                    completed_jobs.append({
                        "job_id": job_id,
                        "function": info.function,
                        "args": info.args,
                        "kwargs": info.kwargs,
                        "enqueue_time": info.enqueue_time.isoformat() if info.enqueue_time else None,
                        "start_time": info.start_time.isoformat() if info.start_time else None,
                        "finish_time": info.finish_time.isoformat() if info.finish_time else None,
                        "status": status,
                        "result": str(result) if result else None
                    })
            except Exception as e:
                print(f"Error fetching completed job info for {key}: {e}")
                continue
        
        # Sort by finish_time (most recent first) and take last 3
        # Use actual datetime objects for proper sorting, fallback to a very old date for None values
        from datetime import datetime
        completed_jobs.sort(
            key=lambda x: datetime.fromisoformat(x['finish_time'].replace('Z', '+00:00')) if x['finish_time'] else datetime.min, 
            reverse=True
        )
        return JSONResponse({"completed_jobs": completed_jobs[:3]})
        
    except Exception as e:
        print(f"Error fetching completed jobs: {e}")
        return JSONResponse({"error": "Failed to fetch completed jobs", "details": str(e)}, status_code=500)

# To run this app:
# 1. Start Redis: redis-server
# 2. Start the arq worker: arq app.worker.WorkerSettings
# 3. Start FastAPI: uvicorn app.main:app --reload
