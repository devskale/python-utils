# Python Utilities Collection

A comprehensive collection of Python utility packages for various development needs.

## Overview

This repository contains a collection of Python utility packages designed to be reused across multiple projects. Each package is maintained within this repository but can be installed individually as needed.

## Available Packages

- **hello_world**: A simple demonstration package showing the repository structure
- **credgoo**: Store your APIKEYs in a google sheet and retrieve them securely with local caching
- **uniinfer**: a unified python interface for 15+ popular inferencing providers
- **pdf2md-skale**: A versatile PDF to Markdown converter with multiple extraction methods (pdfplumber, PyPDF2, PyMuPDF, OCR) and features like recursive processing, dry run mode, and metadata inclusion
- **md2blank**: A markdown to blank converter that removes all PII content while preserving structure
- **robotni**: A minimal, file-based task scheduler to run Python jobs from a web app, with async task queuing and status polling.
- **md2pdfs**: A Python package for generating beautiful PDFs from Markdown content.

## Installation

You can install individual packages directly from this repository:

```bash
# Install a specific package
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/hello_world
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/credgoo
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/uniinfer
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/pdf2md.skale
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/md2blank
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/md2pdfs
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/robotni
pip install git+https://github.com/devskale/python-utils.git#subdirectory=packages/strukt2meta
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
