import os
import shutil # Add this import
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from huey_app import huey # Import only huey instance
from tasks import add, run_fake_job # Import tasks from new tasks.py
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from huey.api import Result

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # or ["*"] for all origins (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AddRequest(BaseModel):
    x: int
    y: int

@app.post("/add/")
def enqueue_add(req: AddRequest):
    task = add(req.x, req.y)  # Changed from add.schedule((req.x, req.y))
    return {"task_id": task.id}

@app.post("/fakejob/")
def enqueue_fake_job():
    task = run_fake_job()
    return {"task_id": task.id, "message": "Fake job enqueued"}

@app.get("/result/{task_id}")
def get_result(task_id: str):
    result = huey.result(task_id)
    if result is None:
        return {"status": "pending"}
    return {"status": "done", "result": result}

@app.get("/queue/")
def get_queue():
    # Get all tasks from Huey's pending and scheduled lists (raw)
    raw_pending_tasks = list(huey.pending(None))  # Get all, including those that might be revoked
    raw_scheduled_tasks = list(huey.scheduled(None)) # Get all, including those that might be revoked

    # Filter for display: active pending and scheduled tasks
    active_pending = [t for t in raw_pending_tasks if not Result(huey, t).is_revoked()]
    active_scheduled = [t for t in raw_scheduled_tasks if not Result(huey, t).is_revoked()]

    # Count revoked tasks from the raw lists
    # Combine raw lists (tasks could theoretically be in both if state changes rapidly, but typically distinct)
    # To avoid double counting if a task somehow appeared in both raw lists with the same ID:
    all_known_task_ids = set()
    all_distinct_tasks = []
    for task_list in [raw_pending_tasks, raw_scheduled_tasks]:
        for task in task_list:
            if task.id not in all_known_task_ids:
                all_distinct_tasks.append(task)
                all_known_task_ids.add(task.id)
    
    revoked_count = sum(1 for t in all_distinct_tasks if Result(huey, t).is_revoked())

    # Each item is a Huey Task object; extract relevant info
    def task_info(task):
        return {
            "id": task.id,
            "name": task.name,
            "args": task.args,
            "kwargs": task.kwargs,
            "retries": task.retries,
            "eta": str(task.eta) if hasattr(task, "eta") else None,
        }
    return {
        "pending": [task_info(t) for t in active_pending],
        "scheduled": [task_info(t) for t in active_scheduled],
        "revoked_count": revoked_count  # Add revoked count here
    }

@app.delete("/queue/{task_id}")
def delete_task(task_id: str):
    # find the task in pending or scheduled and revoke it
    for task in list(huey.pending()) + list(huey.scheduled()):
        if task.id == task_id:
            # revoke this specific task instance using Result API
            Result(huey, task).revoke()
            return {"status": "revoked", "task_id": task_id}
    # If not found in pending or scheduled, clarify possible reasons
    raise HTTPException(
        status_code=404,
        detail="Task not found, already started, finished, or cannot be revoked. Only pending or scheduled tasks can be revoked."
    )

@app.post("/queue/flush/")
def flush_queue():
    # Remove all files in the FileHuey data directory
    storage_path = huey.storage.path
    try:
        if os.path.isdir(storage_path):
            for item_name in os.listdir(storage_path):
                item_path = os.path.join(storage_path, item_name)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path) # Use shutil.rmtree for directories
        return {"status": "flushed"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

app.mount("/webdemo", StaticFiles(directory="webdemo"), name="webdemo")
