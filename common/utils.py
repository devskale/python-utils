"""
Common utility functions shared across packages.
"""


def get_package_version(package_name):
    """
    Get the version of a package dynamically.
    
    Args:
        package_name (str): The name of the package
        
    Returns:
        str: The version string, or "unknown" if not found
    """
    try:
        module = __import__(package_name)
        return getattr(module, "__version__", "unknown")
    except ImportError:
        return "unknown"
