from setuptools import setup, find_packages

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
    install_requires=[
        "requests",  # Dependency for AI model access
        "uniinfer @ file:../uniinfer",
        "credgoo @ file:../credgoo",
        "ofs @ file:../ofs",
        "json_repair",
    ],
    entry_points={
        'console_scripts': [
            'strukt2meta=strukt2meta.main:main',
        ],
    },
)
