#!/usr/bin/env python3
"""
Example script showing how to add new subprocess-based tasks using the YAML configuration system.

To add a new subprocess task:
1. Add the task configuration to subprocess_config.yaml
2. Create a simple task function that calls run_subprocess_from_config
3. Register the task in your task queue system
"""

import asyncio
from tasks import run_subprocess_from_config


async def task_custom_ping(ctx, params: dict = None):
    """
    Example of a custom ping task that uses parameters from the YAML config.
    This demonstrates how to create parameterized subprocess tasks.
    
    Args:
        ctx: Task context
        params: Dictionary that can contain 'target' parameter to override default
    """
    return await run_subprocess_from_config('task_custom_ping', params)


async def task_curl(ctx, params: dict = None):
    """
    Example of a curl task that can be configured via parameters.
    
    Args:
        ctx: Task context
        params: Dictionary that can contain 'method' and 'url' parameters
    """
    return await run_subprocess_from_config('task_curl', params)


async def main():
    """Example usage of the new tasks"""
    
    print("=== Testing custom ping task ===")
    # Use default target (google.com)
    result1 = await task_custom_ping(None, {})
    print(f"Default ping result: {result1[:100]}...")
    
    # Use custom target
    result2 = await task_custom_ping(None, {'target': 'github.com'})
    print(f"Custom ping result: {result2[:100]}...")
    
    print("\n=== Testing curl task ===")
    # Use default GET request
    result3 = await task_curl(None, {})
    print(f"Default curl result: {result3[:100]}...")
    
    # Use custom POST request
    result4 = await task_curl(None, {
        'method': 'POST',
        'url': 'https://httpbin.org/post'
    })
    print(f"Custom curl result: {result4[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())