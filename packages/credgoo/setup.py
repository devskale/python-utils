from setuptools import setup, find_packages
import os

setup(
    name="credgoo",
    version="0.1.3",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    author="Han Woo",
    author_email="dev@skale.dev",
    description="A package for securely retrieving API keys from Google Sheets",
    long_description=open("README.md", "r", encoding="utf-8").read(
    ) if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/devskale/python-utils/tree/master/packages/credgoo",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "credgoo=credgoo.credgoo:main",
        ],
    },
)
