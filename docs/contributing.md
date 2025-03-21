# Contributing Guidelines

Thank you for your interest in contributing to the Python Utilities collection! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## How to Contribute

1. **Fork the Repository**
   
   Start by forking the repository to your GitHub account.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/yourusername/python-utils.git
   cd python-utils
   ```

3. **Create a New Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Your Changes**

   Implement your changes, following the coding standards described below.

5. **Run Tests**

   ```bash
   pytest tests/
   ```

6. **Commit Your Changes**

   ```bash
   git commit -m "Add feature: your feature description"
   ```

7. **Push to GitHub**

   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**

   Open a pull request from your fork to the main repository.

## Adding a New Package

To add a new package to the collection:

1. Create a new directory under `packages/` with your package name
2. Follow the existing package structure (README.md, setup.py, etc.)
3. Add tests in the `tests/` directory
4. Add documentation in the `docs/packages/` directory
5. Update the main README.md to include your package

## Coding Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions, classes, and modules
- Include tests for all new functionality

## Pull Request Process

1. Update the README.md and documentation with details of changes
2. Update the version number in your package's setup.py
3. The PR will be merged once it passes all tests and receives approval

## Questions?

If you have any questions, please open an issue in the repository.
