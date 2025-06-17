import subprocess
import asyncio
import random
import re
import logging
import subprocess
import yaml
import os
from typing import Any, Dict, List, Optional
from string import Template


# Global variable to cache the subprocess configuration
_subprocess_config = None


def load_subprocess_config() -> Dict:
    """
    Load subprocess configuration from YAML file.
    Caches the configuration to avoid repeated file reads.
    """
    global _subprocess_config
    if _subprocess_config is None:
        config_path = os.path.join(os.path.dirname(__file__), 'subprocess_config.yaml')
        try:
            with open(config_path, 'r') as file:
                _subprocess_config = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: Subprocess config file not found at {config_path}")
            _subprocess_config = {'subprocess_commands': {}}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML config: {e}")
            _subprocess_config = {'subprocess_commands': {}}
    return _subprocess_config


def substitute_command_params(command: List[str], params: Dict) -> List[str]:
    """
    Substitute parameters in command using Template string substitution.
    When a parameter contains multiple arguments, they are properly split.
    
    Args:
        command: List of command parts that may contain ${param} placeholders
        params: Dictionary of parameters to substitute
        
    Returns:
        List of command parts with parameters substituted
    """
    import shlex
    
    substituted_command = []
    for part in command:
        if '${' in part:
            template = Template(part)
            try:
                substituted_part = template.substitute(params)
                # If the substituted part contains spaces, split it into separate arguments
                if ' ' in substituted_part and part == '${param}':
                    # Use shlex to properly parse shell arguments
                    parsed_args = shlex.split(substituted_part)
                    substituted_command.extend(parsed_args)
                else:
                    substituted_command.append(substituted_part)
            except KeyError as e:
                raise ValueError(f"Missing required parameter {e} for command substitution")
        else:
            substituted_command.append(part)
    return substituted_command


async def run_subprocess_from_config(task_name: str, params: Dict = None) -> str:
    """
    Execute a subprocess command based on configuration from YAML file.
    
    Args:
        task_name: Name of the task configuration to use
        params: Optional parameters for command substitution
        
    Returns:
        Command output as string or error message
    """
    config = load_subprocess_config()
    subprocess_commands = config.get('subprocess_commands', {})
    
    if task_name not in subprocess_commands:
        return f"Error: Task '{task_name}' not found in subprocess configuration"
    
    task_config = subprocess_commands[task_name]
    command = task_config.get('command', [])
    
    if not command:
        return f"Error: No command specified for task '{task_name}'"
    
    # Merge default params with provided params
    all_params = task_config.get('default_params', {}).copy()
    if params:
        all_params.update(params)
    
    # Substitute parameters in command
    try:
        final_command = substitute_command_params(command, all_params)
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Extract subprocess options
    capture_output = task_config.get('capture_output', True)
    text = task_config.get('text', True)
    timeout = task_config.get('timeout', 30)
    
    print(f"Starting {task_config.get('description', task_name)}")
    print(f"Executing command: {' '.join(final_command)}")
    
    try:
        # Use run_in_executor to run the blocking subprocess call in a separate thread
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: subprocess.run(
                final_command, 
                capture_output=capture_output, 
                text=text, 
                timeout=timeout
            )
        )
        
        if result.returncode == 0:
            output = result.stdout.strip() if result.stdout else "Command completed successfully"
            print(f"{task_name} result: {output}")
            return output
        else:
            error = result.stderr.strip() if result.stderr else f"Command failed with return code {result.returncode}"
            print(f"Error during {task_name}: {error}")
            return f"Error: {error}"
            
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        print(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Exception occurred while running {task_name}: {str(e)}"
        print(error_msg)
        return error_msg


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
    return await run_subprocess_from_config('task_uname', params)


async def task_ping(ctx, params: dict = None):
    """
    A task that runs the 'ping -c 4 google.com' CLI command to check network connectivity.
    Returns the output of the command as a string.
    Accepts parameters as a dictionary (unused for this task).
    """
    return await run_subprocess_from_config('task_ping', params)


async def task_uberlama(ctx, params: dict = None):
    """
    AI Model Query to uberlama
    Accepts parameters as a dictionary (unused for this task).
    """
    return await run_subprocess_from_config('task_uberlama', params)


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
