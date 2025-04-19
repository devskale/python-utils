# Credgoo

A Python package for securely retrieving API keys from Google Sheets with local caching.

## Overview

Credgoo provides a secure way to manage API keys by retrieving them from Google Sheets and implementing local caching for better performance. This approach allows teams to centrally manage API credentials while providing secure access to individual developers.

Credgoo combines the convenience of centralized credential management with the security of local storage and encryption.

## Features

- **Secure Key Retrieval**: Fetch encrypted API keys from Google Sheets
- **Decryption**: Built-in decryption with custom encryption keys
- **Local Caching**: Store retrieved keys locally to reduce API calls
- **Command-line Interface**: Easy-to-use CLI for key retrieval
- **Secure Storage**: Cached keys are stored with restrictive permissions (0600)
- **Centralized Management**: Update keys in one place (your spreadsheet)
- **Encrypted Transmission**: Keys are encrypted before network transmission

## Installation

```bash
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/credgoo
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

By default, retrieved keys are cached in `~/.config/api_keys/api_keys.json` with restrictive permissions (0600). The cache:

- Is automatically used for subsequent requests
- Can be bypassed with `--no-cache` flag
- Stores keys with restrictive permissions (0600)
- Includes timestamp of when each key was retrieved

## Security Notes

- Always protect your encryption key and bearer token
- Recommended to store credentials in secure locations
- Cache files have restrictive permissions (0600)
- Consider rotating credentials periodically

## Why Credgoo is Great

Credgoo provides a secure and convenient way to manage your API keys:

🔒 **Personal Secure Storage**

- Your keys are stored in your personal Google Sheet, not on some third-party server
- Only you have access to your spreadsheet (Google account protected)

🔑 **Double-Layer Security**

- Protected by both a SECRET_TOKEN (authentication)
- And an ENCRYPTION_KEY (data security)
- Both are required to access your credentials

🛡️ **Encrypted Transmission**

- Keys are encrypted before being sent over the network
- Uses robust encryption with unique initialization vectors

💻 **CLI Integration**

- Easy to use from command line with automatic decryption
- No keys stored in plaintext in your local environment

🔁 **Centralized Management**

- Update keys in one place (your spreadsheet)
- Changes are immediately available everywhere
- No need to update multiple config files
