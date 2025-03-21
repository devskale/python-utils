#!/usr/bin/env python3
"""
Development setup script for the Python Utilities collection.
Installs all packages in development mode.
"""

import os
import subprocess
import sys
from pathlib import Path


def setup_dev_environment():
    """Install all packages in development mode."""
    root_dir = Path(__file__).parent.parent
    packages_dir = root_dir / "packages"
    
    # Install root package
    print("Installing root package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(root_dir)])
    
    # Install all individual packages
    for package_dir in packages_dir.iterdir():
        if package_dir.is_dir() and (package_dir / "setup.py").exists():
            print(f"Installing {package_dir.name}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-e", str(package_dir)
            ])
    
    print("\nDevelopment setup completed successfully!")


if __name__ == "__main__":
    setup_dev_environment()
