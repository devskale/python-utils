# Hello World Package

A simple demonstration package that showcases the repository structure.

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

## API Reference

### greeter module

#### `say_hello(name=None)`

Prints a hello message to the console.

**Parameters:**
- `name` (str, optional): The name to greet. If None, uses "friend" instead.

**Returns:**
- None

**Example:**
```python
say_hello("John")  # Output: "Hello, John!"
say_hello()  # Output: "Hello, friend!"
```
