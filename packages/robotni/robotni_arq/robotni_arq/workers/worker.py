from arq import connections
from dotenv import load_dotenv
import os
import logging

from arq import connections
from robotni_arq.tasks import fake_task, another_fake_task, task_uname, task_ping, task_uberlama, task_parse, task_anonymize

load_dotenv()

# Configure logging for the worker
log_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'worker.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler() # Also log to console
    ]
)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

async def startup(ctx):
    logger.info("Worker starting up...")

async def shutdown(ctx):
    logger.info("Worker shutting down...")

class WorkerSettings:
    functions = [fake_task, another_fake_task, task_uname, task_ping, task_uberlama, task_parse, task_anonymize]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = connections.RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    max_jobs = 1  # Only run one job at a time
    # You can add other settings like:
    # job_timeout = 60  # seconds
    # health_check_interval = 60 # seconds
