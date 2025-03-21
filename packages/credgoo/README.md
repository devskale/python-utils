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
