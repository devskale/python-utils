import subprocess
import asyncio
import random
import re
import logging
import subprocess
from typing import Any # Add this import


async def fake_task(ctx, params: dict):
    """
    A simple fake task that simulates work by sleeping.
    Accepts parameters as a dictionary.
    """
    # Extract parameters from the params dictionary
    duration = params.get('duration', 5)
    task_name = params.get('task_name', 'Default Fake Task')
    
    print(f"Starting task: {task_name} (will run for {duration}s)")
    await asyncio.sleep(duration)
    result = f"Task '{task_name}' completed after {duration}s"
    print(result)
    return result


async def another_fake_task(ctx, params: dict):
    """
    Another simple fake task.
    Accepts parameters as a dictionary.
    """
    # Extract parameters from the params dictionary
    message = params.get('message', 'Default message')
    
    print(f"Starting another_fake_task with message: {message}")
    await asyncio.sleep(random.randint(1, 5))
    result = f"Another_fake_task completed with message: '{message}'"
    print(result)
    return result


async def task_uname(ctx, params: dict = None):
    """
    A task that runs the 'uname -a' CLI command to display system information.
    Returns the output of the command as a string.
    Accepts parameters as a dictionary (unused for this task).
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


async def task_ping(ctx, params: dict = None):
    """
    A task that runs the 'ping -c 4 google.com' CLI command to check network connectivity.
    Returns the output of the command as a string.
    Accepts parameters as a dictionary (unused for this task).
    """
    print("Starting task_ping to check network connectivity")
    try:
        # Use run_in_executor to run the blocking subprocess call in a separate thread
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: subprocess.run(['ping', '-c', '4', 'google.com'], capture_output=True, text=True))
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"Ping result: {output}")
            return output
        else:
            error = result.stderr.strip()
            print(f"Error during ping: {error}")
            return f"Error: {error}"
    except Exception as e:
        error_msg = f"Exception occurred while running ping: {str(e)}"
        print(error_msg)
        return error_msg


async def task_uberlama(ctx, params: dict = None):
    """
    AI Model Query to uberlama
    Accepts parameters as a dictionary (unused for this task).
    """
    print("Starting to query uberlama AI Model")
    try:
        # Use run_in_executor to run the blocking subprocess call in a separate thread
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: subprocess.run([
            '/Users/johannwaldherr/code/python-utils/packages/robotni/robotni_arq/.venv/bin/python',
            '/Users/johannwaldherr/code/python-utils/packages/robotni/robotni_arq/tasks/uberlama.py',
            '-t',
            'erzähle einen witz vom onkel fritz',
        ], capture_output=True, text=True))
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"Uberlama result: {output}")
            return output
        else:
            error = result.stderr.strip()
            print(f"Error during uberlama: {error}")
            return f"Error: {error}"
    except Exception as e:
        error_msg = f"Exception occurred while running uberlama: {str(e)}"
        print(error_msg)
        return error_msg


async def task_parse(ctx, params: dict):
    """
    A placeholder task that receives parameters for future implementation.
    Accepts parameters as a dictionary.

    Args:
        ctx: The context object
        params: Dictionary containing task parameters

    Returns:
        str: A message indicating the task was called with the given parameters
    """
    print(f"Starting task_parse with parameters: {params}")
    # Example: Access a specific parameter if needed
    # specific_param = params.get('my_param_key')
    # print(f"Specific param 'my_param_key': {specific_param}")
    result = f"task_parse called with parameters: {params}"
    print(result)
    return result


async def task_anonymize(ctx, params: dict):
    """
    Anonymizes text using a specified level (or 'basic' by default).
    """
    # Add missing imports
    # Initialize logger
    logger = logging.getLogger(__name__)
    
    # Extract parameters from the params dictionary
    text_to_anonymize = params.get('text_to_anonymize', 'No text provided')
    level = params.get('level', 'basic')
    
    logger.info(f"Executing task_anonymize with context: {ctx}, text: {text_to_anonymize}, level: {level}")
    if not text_to_anonymize or text_to_anonymize == 'No text provided':
        logger.error("task_anonymize: 'text_to_anonymize' not found in parameters")
        raise ValueError("'text_to_anonymize' is a required parameter")

    # Simulate anonymization based on level
    if level == 'basic':
        # Improved regex to handle word boundaries and punctuation better
        anonymized_text = re.sub(
            r'\b\w+\b', 
            lambda m: m.group(0)[0] + '*' * (len(m.group(0)) - 1) if len(m.group(0)) > 1 else m.group(0), 
            text_to_anonymize
        )
    elif level == 'full':
        anonymized_text = "[ANONYMIZED_FULL]"
    else:
        logger.warning(f"Unknown anonymization level: {level}")
        anonymized_text = f"[ANONYMIZED_UNKNOWN_LEVEL_{level}]"
    
    logger.info(f"Anonymized text (level: {level}): {anonymized_text}")
    return {
        "original_text": text_to_anonymize, 
        "anonymized_text": anonymized_text, 
        "level": level
    }
