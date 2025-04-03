from setuptools import setup, find_packages

setup(
    name='pdf2md-elegant',
    version='0.2.0',
    packages=find_packages(),
    install_requires=[
        'pdfplumber',
        'PyPDF2',
        'pymupdf',
        'python-dotenv',
        'llama_parse',
        'pytesseract',
        'docling',
        'easyocr',
        'pdf2image',
        'llama-index-core'
    ],
    entry_points={
        'console_scripts': [
            'pdf2md=pdf2md.main:main',
            'pdf2md-elegant=pdf2md.elegant:main'
        ]
    },
    author='Johann Waldherr',
    author_email='johann.waldherr@vergabepilot.at',
    description='A package to convert PDF files to Markdown using various extractors.',
    url='https://github.com/vergabepilot/pdf2md-elegant',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
