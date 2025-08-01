# Hello World

A simple demonstration package showcasing the repository structure.

## Installation

```bash
pip install git+https://github.com/yourusername/python-utils.git#subdirectory=packages/hello_world
```

## Usage

```python
from hello_world import greeter

# Print a simple greeting
greeter.say_hello()

# Print a personalized greeting
greeter.say_hello("World")
```

## Examples

See the [examples directory](examples) for more usage examples.

## Scaffolding

The `scaffolding` directory provides a structured starting point for extending the Hello World package. It includes:

- `__init__.py`: Marks the directory as a Python package.
- `template.py`: Contains a simple `greet` function to demonstrate basic functionality.
- `utils.py`: Utility functions for loading and saving configurations.
- `config.json`: A sample configuration file with default values.
- `README.md`: Documentation for the scaffolding directory.
- `tests/`: Unit tests for the scaffolding modules.
  - `test_template.py`: Tests for the `template.py` module.
  - `test_utils.py`: Tests for the `utils.py` module.

### Example Usage

#### Greeting Function

```python
from scaffolding.template import greet

print(greet("Alice"))  # Output: Hello, Alice!
```

#### Configuration Utilities

```python
from scaffolding.utils import load_config, save_config

# Save a configuration
config = {"key": "value"}
save_config("config.json", config)

# Load the configuration
loaded_config = load_config("config.json")
print(loaded_config)  # Output: {'key': 'value'}
```

## Best Practices

### Setting Up a Virtual Environment

It is recommended to use a virtual environment for isolating dependencies. To create a virtual environment in the `hello_world` directory:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

- On macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```
- On Windows:
  ```bash
  .venv\Scripts\activate
  ```

Install dependencies:

```bash
pip install -r requirements.txt
```

## License

This package is part of the Python Utilities collection and is licensed under the MIT License.
