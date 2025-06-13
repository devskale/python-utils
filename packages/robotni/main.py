from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from huey_app import huey, add, run_fake_job # Import run_fake_job

app = FastAPI()

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
