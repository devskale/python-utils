# Credgoo

A Python package for securely retrieving API keys from Google Sheets with local caching.

## Overview

Credgoo provides a secure way to manage API keys by retrieving them from Google Sheets and implementing local caching for better performance. This approach allows teams to centrally manage API credentials while providing secure access to individual developers.

## Features

- **Secure Key Retrieval**: Fetch encrypted API keys from Google Sheets
- **Decryption**: Built-in decryption with custom encryption keys
- **Local Caching**: Store retrieved keys locally to reduce API calls
- **Command-line Interface**: Easy-to-use CLI for key retrieval
- **Secure Storage**: Cached keys are stored with restrictive permissions (0600)

## Installation

```bash
pip install credgoo
```

## Usage

### Command Line Interface

```bash
credgoo SERVICE_NAME --token BEARER_TOKEN --key ENCRYPTION_KEY
```

Optional arguments:

- `--url`: Custom Google Apps Script URL (defaults to built-in URL)
- `--cache-dir`: Custom cache directory (defaults to ~/.config/api_keys)
- `--no-cache`: Bypass cache and force retrieval from Google Sheets

### Python API

```python
from credgoo import get_api_key

# Basic usage
# uses cached keys if available
api_key = get_api_key("service_name")

# With custom cache directory
api_key = get_api_key("service_name",
                      bearer_token="your_token",
                      encryption_key="your_key",
                      cache_dir="/path/to/cache")

# Force fresh retrieval (bypass cache)
api_key = get_api_key("service_name",
                      bearer_token="your_token",
                      encryption_key="your_key",
                      no_cache=True)
```

### Credential Storage

Credentials can be stored securely for future use:

```python
from credgoo import store_credentials
from pathlib import Path

store_credentials("your_token", "your_key", "optional_url", Path("~/.config/api_keys/credgoo.txt"))
```

### Caching Behavior

By default, retrieved keys are cached in `~/.config/api_keys/api_keys.json`. The cache:

- Is automatically used for subsequent requests
- Can be bypassed with `--no-cache` flag
- Stores keys with restrictive permissions (0600)
- Includes timestamp of when each key was retrieved

## Security Notes

- Always protect your encryption key and bearer token
- Recommended to store credentials in secure locations
- Cache files have restrictive permissions (0600)
- Consider rotating credentials periodically
