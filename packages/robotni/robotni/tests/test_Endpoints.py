# test robotni endpoints

from fastapi.testclient import TestClient
from robotni.main import app

client = TestClient(app)


def test_submit_job():
    response = client.post(
        "/api/worker/jobs",
        json={"name": "example_task", "params": {"x": 3, "y": 4}}
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "submitted"
    job_id = data["job_id"]
    print(
        f"PASSED: job_id={job_id} status=submitted")
