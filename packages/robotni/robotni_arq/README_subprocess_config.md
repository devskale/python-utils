# Subprocess Configuration System

This document describes the YAML-based subprocess configuration system for robotni-arq tasks.

## Overview

The subprocess configuration system allows you to define and manage external command executions through a centralized YAML configuration file (`subprocess_config.yaml`). This approach provides several benefits:

- **Centralized Configuration**: All subprocess commands are defined in one place
- **Parameter Substitution**: Support for dynamic parameter injection using `${param}` syntax
- **Reusability**: Common command patterns can be easily reused
- **Maintainability**: Easy to modify commands without changing Python code
- **Timeout Management**: Configurable timeouts for each command

## Configuration File Structure

The `subprocess_config.yaml` file has the following structure:

```yaml
subprocess_commands:
  task_name:
    description: "Human-readable description of the task"
    command: ["command", "arg1", "arg2", "${param}"]
    capture_output: true  # Optional, defaults to true
    text: true           # Optional, defaults to true
    timeout: 30          # Optional, defaults to 30 seconds
    default_params:      # Optional default parameters
      param: "default_value"
```

## Parameter Substitution

Commands can include parameter placeholders using the `${parameter_name}` syntax. These will be substituted at runtime with values from:

1. Parameters passed to the task function
2. Default parameters defined in the configuration
3. Task-specific parameters

Example:
```yaml
task_custom_ping:
  command: ["ping", "-c", "4", "${target}"]
  default_params:
    target: "google.com"
```

## Usage in Python Code

### Basic Usage

```python
async def my_task(ctx, params: dict = None):
    """
    Simple task that uses YAML configuration.
    """
    return await run_subprocess_from_config('task_name', params)
```

### With Parameters

```python
async def ping_custom_host(ctx, params: dict = None):
    """
    Ping a custom host specified in params.
    """
    # params can contain {'target': 'example.com'}
    return await run_subprocess_from_config('task_custom_ping', params)
```

## Adding New Tasks

1. **Add configuration to YAML file**:
   ```yaml
   subprocess_commands:
     my_new_task:
       description: "My new subprocess task"
       command: ["my_command", "--option", "${value}"]
       timeout: 60
       default_params:
         value: "default"
   ```

2. **Create Python task function**:
   ```python
   async def my_new_task(ctx, params: dict = None):
       """
       My new task description.
       """
       return await run_subprocess_from_config('my_new_task', params)
   ```

3. **Register the task** in your task queue system.

## Configuration Examples

### Simple Command
```yaml
task_uname:
  description: "System information using uname command"
  command: ["uname", "-a"]
  timeout: 30
```

### Parameterized Command
```yaml
task_custom_ping:
  description: "Custom ping with configurable target"
  command: ["ping", "-c", "4", "${target}"]
  default_params:
    target: "google.com"
```

### Complex Command with Multiple Parameters
```yaml
task_curl:
  description: "HTTP request using curl"
  command: ["curl", "-X", "${method}", "${url}", "-H", "Content-Type: application/json"]
  timeout: 30
  default_params:
    method: "GET"
    url: "https://httpbin.org/get"
```

### Python Script Execution
```yaml
task_uberlama:
  description: "AI Model Query to uberlama"
  command: 
    - "/path/to/python"
    - "/path/to/script.py"
    - "-t"
    - "${prompt}"
  timeout: 60
  default_params:
    prompt: "default prompt"
```

## Error Handling

The system provides comprehensive error handling:

- **Configuration Errors**: Missing YAML file or invalid syntax
- **Parameter Errors**: Missing required parameters for substitution
- **Execution Errors**: Command failures, timeouts, or exceptions
- **Return Code Handling**: Non-zero return codes are treated as errors

## Migration from Hardcoded Commands

Existing tasks with hardcoded subprocess calls can be easily migrated:

**Before**:
```python
async def task_ping(ctx, params: dict = None):
    result = await loop.run_in_executor(
        None, 
        lambda: subprocess.run(['ping', '-c', '4', 'google.com'], 
                              capture_output=True, text=True)
    )
    # ... error handling ...
```

**After**:
1. Add to YAML:
   ```yaml
   task_ping:
     command: ["ping", "-c", "4", "google.com"]
   ```

2. Simplify Python:
   ```python
   async def task_ping(ctx, params: dict = None):
       return await run_subprocess_from_config('task_ping', params)
   ```

## Benefits

- **Reduced Code Duplication**: Common subprocess patterns are centralized
- **Easier Testing**: Commands can be modified without code changes
- **Better Configuration Management**: All external dependencies in one place
- **Improved Security**: Centralized validation and parameter handling
- **Enhanced Monitoring**: Consistent logging and error handling