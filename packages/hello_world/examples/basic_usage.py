#!/usr/bin/env python3
"""
Basic usage example for the hello_world package.
"""

from hello_world import greeter


def main():
    """Demonstrate the basic functionality of the hello_world package."""
    print("Basic greeting:")
    greeter.say_hello()
    
    print("\nCustom greeting:")
    greeter.say_hello("Python")
    
    names = ["Alice", "Bob", "Charlie"]
    print("\nMultiple greetings:")
    for name in names:
        greeter.say_hello(name)


if __name__ == "__main__":
    main()
