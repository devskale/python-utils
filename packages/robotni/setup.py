from setuptools import setup, find_packages

setup(
    name="robotni",
    version="0.1.0",
    description="A Scalable Python Worker Management System",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="",
    author_email="",
    url="",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
