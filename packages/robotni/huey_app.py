from huey import FileHuey
from workers.taskFakejob import taskFakejob as original_taskFakejob # Import original

# Use file-based Huey (tasks and results stored in ./huey-data/)
huey = FileHuey('my-app', path='./huey-data')

@huey.task()
def add(x, y):
    return x + y

@huey.task()
def run_fake_job():
    return original_taskFakejob() # Call the original function
