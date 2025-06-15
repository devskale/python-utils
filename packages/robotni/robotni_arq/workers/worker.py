from arq import connections
from dotenv import load_dotenv
import os

from arq import connections
from robotni_arq.tasks import fake_task, another_fake_task, task_uname, task_ping, task_uberlama

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

async def startup(ctx):
    print("Worker starting up...")

async def shutdown(ctx):
    print("Worker shutting down...")

class WorkerSettings:
    functions = [fake_task, another_fake_task, task_uname, task_ping, task_uberlama]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = connections.RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    max_jobs = 1  # Only run one job at a time
    # You can add other settings like:
    # job_timeout = 60  # seconds
    # health_check_interval = 60 # seconds
