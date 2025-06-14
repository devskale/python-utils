from setuptools import setup, find_packages

setup(
    name="robotni_huey",
    version="0.1.0",
    description="Minimal task scheduler using Huey and FastAPI.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "huey",
        "fastapi",
    ],
    include_package_data=True,
    python_requires=">=3.8",
)
