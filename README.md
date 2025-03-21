# Python Utilities Collection

A comprehensive collection of Python utility packages for various development needs.

## Overview

This repository contains a collection of Python utility packages designed to be reused across multiple projects. Each package is maintained within this repository but can be installed individually as needed.

## Available Packages

- **hello_world**: A simple demonstration package showing the repository structure
- **file_analyzer**: (Coming soon) Utility for analyzing file content and suggesting metadata
- **secure_config**: (Coming soon) Secure storage and management of API keys and credentials

## Installation

You can install individual packages directly from this repository:

```bash
# Install a specific package
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/hello_world
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/credgoo
```

## Development Setup

To set up the repository for development:

```bash
# Clone the repository
git clone https://github.com/devskale/python-utils.git
cd python-utils

# Install development dependencies
pip install -e .
```

## Contributing

Contributions are welcome! Please see the [contributing guidelines](docs/contributing.md) for more information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
