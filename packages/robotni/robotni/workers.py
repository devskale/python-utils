import asyncio
import random
from arq import Worker

async def process_fakejob(ctx, job_id, params):
    """
    Process a fake job that simulates work by waiting for a random duration.
    
    Args:
        ctx: ARQ context
        job_id: Unique identifier for the job
        params: Dictionary of parameters, expected to contain 'delay_seconds' (default 5)
    
    Returns:
        Dictionary with the duration waited
    """
    delay_seconds = params.get('delay_seconds', 5)
    wait_time = random.uniform(1, delay_seconds)
    await asyncio.sleep(wait_time)
    return {"waited": wait_time}

class WorkerSettings:
    """
    Configuration for the ARQ worker.
    Defines the functions available for job processing.
    """
    functions = [process_fakejob]
    redis_settings = {'host': 'localhost', 'port': 6379}
