from setuptools import setup, find_packages

setup(
    name="hello_world",
    version="0.1.0",
    description="A simple demonstration package",
    author="Your Name",
    author_email="your.email@example.com",
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
    entry_points={
        'console_scripts': [
            'hello-world=hello_world.greeter:say_hello',
        ],
    },
)
