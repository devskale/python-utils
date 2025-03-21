"""
Greeter module for displaying hello messages.
"""


def say_hello(name=None):
    """
    Print a hello message to the console.

    Args:
        name (str, optional): The name to greet. If None, uses "friend" instead.

    Returns:
        None
    """
    if name is None:
        name = "friend"
    print(f"Hello, {name}!")
