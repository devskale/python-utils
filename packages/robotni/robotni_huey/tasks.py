from .huey_app import huey
from workers.taskFakejob import taskFakejob as original_taskFakejob

@huey.task()
def add(x, y):
    return x + y

@huey.task()
def run_fake_job():
    return original_taskFakejob()
