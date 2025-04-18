from setuptools import setup, find_packages

setup(
    name="uniinfer",
    version="0.1.3",
    description="Unified Inference API for LLM chat completions",
    author="Han Woo",
    author_email="dev@skale.dev",
    packages=find_packages(where='.', include=['uniinfer*']),
    install_requires=[
        "requests>=2.25.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'uniinfer=uniinfer.cli:main'
        ],
    },
)
