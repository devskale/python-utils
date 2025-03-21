from setuptools import setup, find_packages

setup(
    name="credgoo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A package for securely retrieving API keys from Google Sheets",
    long_description=open("README.md", "r").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/credgoo",
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