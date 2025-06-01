from setuptools import setup, find_packages

setup(
    name="uniinfer",
    version="0.1.7",
    url="https://github.com/skale-dev/uniinfer",
    description="Unified Inference API for LLM chat completions",
    author="Han Woo",
    author_email="dev@skale.dev",
    packages=find_packages(where='.', include=['uniinfer*']),
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=1.0.0",
        "openai"
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
    extras_require={
        'gemini': ['google-generativeai>=0.4.0'],
        'api': [
            'fastapi>=0.100.0',
            'uvicorn[standard]>=0.23.0',
        ],
    },
    package_data={
        'uniinfer': ['examples/*.py', 'examples/webdemo/*'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'uniinfer=uniinfer.examples.uniinfer_example:main',
            'uniioai-proxy=uniinfer.uniioai_proxy:main',  # <-- Add this line

        ],
    },
)
