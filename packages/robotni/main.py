from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from huey_app import huey, add

app = FastAPI()

class AddRequest(BaseModel):
    x: int
    y: int

@app.post("/add/")
def enqueue_add(req: AddRequest):
    task = add(req.x, req.y)  # Changed from add.schedule((req.x, req.y))
    return {"task_id": task.id}

@app.get("/result/{task_id}")
def get_result(task_id: str):
    result = huey.result(task_id)
    if result is None:
        return {"status": "pending"}
    return {"status": "done", "result": result}
