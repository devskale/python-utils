import asyncio
import random

async def fake_task(ctx, duration: int, task_name: str):
    """
    A simple fake task that simulates work by sleeping.
    """
    print(f"Starting task: {task_name} (will run for {duration}s)")
    await asyncio.sleep(duration)
    result = f"Task '{task_name}' completed after {duration}s"
    print(result)
    return result

async def another_fake_task(ctx, message: str):
    """
    Another simple fake task.
    """
    print(f"Starting another_fake_task with message: {message}")
    await asyncio.sleep(random.randint(1, 5))
    result = f"Another_fake_task completed with message: '{message}'"
    print(result)
    return result
