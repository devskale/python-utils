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

import subprocess
import asyncio

async def task_uname(ctx):
    """
    A task that runs the 'uname -a' CLI command to display system information.
    Returns the output of the command as a string.
    """
    print("Starting task_uname to fetch system information")
    try:
        # Use run_in_executor to run the blocking subprocess call in a separate thread
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: subprocess.run(['uname', '-a'], capture_output=True, text=True))
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"System information: {output}")
            return output
        else:
            error = result.stderr.strip()
            print(f"Error fetching system information: {error}")
            return f"Error: {error}"
    except Exception as e:
        error_msg = f"Exception occurred while running uname -a: {str(e)}"
        print(error_msg)
        return error_msg
