"""
Entry point for running OFS as a module.

This allows the package to be executed with: python -m ofs
"""

from .cli import main

if __name__ == '__main__':
    main()