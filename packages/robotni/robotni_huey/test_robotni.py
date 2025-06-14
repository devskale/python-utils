import pytest
from fastapi.testclient import TestClient
from main import app
from huey_app import huey

@pytest.fixture(autouse=True)
def huey_immediate_mode():
    original_immediate_mode = huey.immediate
    huey.immediate = True
    try:
        yield
    finally:
        huey.immediate = original_immediate_mode

def test_add_and_result():
    client = TestClient(app)
    response = client.post("/add/", json={"x": 2, "y": 3})
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    result_resp = client.get(f"/result/{task_id}")
    assert result_resp.status_code == 200
    result_data = result_resp.json()
    assert result_data["status"] == "done"
    assert result_data["result"] == 5

def test_task_fakejob_api():
    client = TestClient(app)
    response = client.post("/fakejob/")
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    result_resp = client.get(f"/result/{task_id}")
    assert result_resp.status_code == 200
    result_data = result_resp.json()
    assert result_data["status"] == "done"
    assert result_data["result"] == "Fake job completed"

def test_task_fakejob_direct_call(capsys):
    from workers.taskFakejob import taskFakejob as original_task_fakejob_direct
    original_task_fakejob_direct()
    captured = capsys.readouterr()
    assert "Fake job completed" in captured.out
