from setuptools import setup, find_packages

setup(
    name='md2pdfs',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'markdown',
        'reportlab',
    ],
    entry_points={
        'console_scripts': [
            'md2pdfs=md2pdfs.main:main',
        ],
    },
)
