import subprocess
import sys
from urllib.request import urlopen

from setuptools import setup, find_packages


REMOTE_REQUIREMENTS = [
    "https://skale.dev/credgoo",
    "https://skale.dev/uniinfer",
    "https://skale.dev/pdf2md",
]


def get_remote_requirements() -> list[str]:
    """Fetch and parse remote requirements files."""
    requirements = []
    for url in REMOTE_REQUIREMENTS:
        try:
            with urlopen(url) as response:
                content = response.read().decode('utf-8')
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('git+'):
                        requirements.append(line)
        except Exception as e:
            print(f"Warning: Could not fetch requirements from {url}: {e}")
    return requirements


# Get all requirements
all_requirements = get_remote_requirements() + [
    "requests",
    "json-repair",
]


def install_remote_requirements() -> None:
    """Install external requirement bundles for installs."""
    if not {"install", "develop"} & set(sys.argv) or "bdist_wheel" in sys.argv:
        return

    for url in REMOTE_REQUIREMENTS:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", url])
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not install requirements from {url}: {e}")


install_remote_requirements()

setup(
    name="strukt2meta",
    version="0.0.6",
    description="Generate metadata from structured data that needs no further postprocessing using AI.",
    author="Ha Wa",
    author_email="dev@skale.dev",
    url="https://github.com/yourusername/python-utils",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=all_requirements,
    entry_points={
        'console_scripts': [
            'strukt2meta=strukt2meta.main:main',
        ],
    },
)
