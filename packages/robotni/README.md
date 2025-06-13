# robotni

**robotni** is a minimal, file-based task scheduler for running Python jobs from a web app, featuring async task queuing and status polling.

## Project Structure

```
./packages/robotni/
            ├── .pytest_cache/         # Pytest cache files (can be ignored)
            ├── robotni/               # Main package source
            │   ├── tests/             # Unit and integration tests
            │   ├── workers/           # Worker/task definitions
            │   └── __pycache__/       # Python bytecode cache
            └── robotni.egg-info/      # Packaging metadata
```

## Features

- Submit Python jobs via a web API
- Async task queuing and execution
- File-based job storage and status tracking
- Poll job status from clients

## Usage

1. Install the package.
2. Start the web server.
3. Submit jobs and poll their status via the API.

See `tests/` for usage examples.
