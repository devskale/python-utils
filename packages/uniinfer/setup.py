from setuptools import setup, find_packages

setup(
    name="uniinfer",
    version="0.2.3",
    url="https://github.com/skale-dev/uniinfer",
    description="Unified Inference API for LLM chat completions across 15+ providers with streaming, fallback strategies, and secure API key management",
    long_description="UniInfer provides a unified interface for LLM inference across 15+ providers including OpenAI, Anthropic, Google Gemini, Mistral, and more. Features include real-time streaming, automatic fallback strategies, secure API key management via credgoo, and OpenAI-compatible proxy server.",
    long_description_content_type="text/plain",
    author="Han Woo",
    author_email="dev@skale.dev",
    keywords="llm, ai, inference, openai, anthropic, gemini, mistral, chat, completion, streaming, api",
    packages=find_packages(where='.', include=['uniinfer*']),
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=1.0.0",
        "openai"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
    extras_require={
        'gemini': ['google-genai>=1.38.0'],
        'anthropic': ['anthropic>=0.25.0'],
        'mistral': ['mistralai>=0.4.0'],
        'cohere': ['cohere>=4.0.0'],
        'huggingface': ['huggingface-hub>=0.20.0'],
        'api': [
            'fastapi>=0.100.0',
            'uvicorn[standard]>=0.23.0',
        ],
        'all': [
            'google-genai>=1.38.0',
            'anthropic>=0.25.0',
            'mistralai>=0.4.0',
            'cohere>=4.0.0',
            'huggingface-hub>=0.20.0',
        ],
    },
    package_data={
        'uniinfer': ['examples/*.py', 'examples/webdemo/*'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'uniinfer=uniinfer.uniinfer_cli:main',
            'uniioai-proxy=uniinfer.uniioai_proxy:main',  # <-- Add this line

        ],
    },
)
